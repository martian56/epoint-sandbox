import time
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from epoint_sandbox import __version__
from epoint_sandbox.api.auth import router as auth_router
from epoint_sandbox.api.b2b import router as b2b_router
from epoint_sandbox.api.cards import router as cards_router
from epoint_sandbox.api.epoint import router as epoint_router
from epoint_sandbox.api.errors import EpointError, epoint_error_handler
from epoint_sandbox.api.extras import router as extras_router
from epoint_sandbox.api.invoices import router as invoices_router
from epoint_sandbox.api.money import router as money_router
from epoint_sandbox.config import get_settings
from epoint_sandbox.db import SessionLocal
from epoint_sandbox.models import RequestLog
from epoint_sandbox.sandbox.router import public_router as sandbox_public_router
from epoint_sandbox.sandbox.router import router as sandbox_router
from epoint_sandbox.services import ids
from epoint_sandbox.services.seed import seed_default_merchants
from epoint_sandbox.web.checkout import router as checkout_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    if settings.seed_merchants:
        with SessionLocal() as session:
            seed_default_merchants(session)
            session.commit()
    yield


app = FastAPI(
    title="epoint sandbox",
    version=__version__,
    description="Local drop-in replacement for the epoint.az payment gateway",
    lifespan=lifespan,
)

app.add_exception_handler(EpointError, epoint_error_handler)  # type: ignore[arg-type]


@app.middleware("http")
async def trace_and_log(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    request.state.trace_id = ids.trace_id()
    started = time.perf_counter()

    response = await call_next(request)

    duration_ms = int((time.perf_counter() - started) * 1000)
    response.headers["X-Request-ID"] = request.state.trace_id

    # Integrations assert on this to catch a misconfigured base URL.
    response.headers["X-Epoint-Sandbox"] = "1"
    for name, value in getattr(request.state, "sandbox_headers", {}).items():
        response.headers[name] = value

    if request.url.path.startswith("/api/"):
        _record(request, response.status_code, duration_ms)

    return response


def _record(request: Request, status_code: int, duration_ms: int) -> None:
    with SessionLocal() as session:
        session.add(
            RequestLog(
                trace_id=request.state.trace_id,
                merchant_id=getattr(request.state, "merchant_id", None),
                method=request.method,
                path=request.url.path,
                status_code=status_code,
                duration_ms=duration_ms,
                raw_data=getattr(request.state, "raw_data", None),
                raw_signature=getattr(request.state, "raw_signature", None),
                signature_valid=getattr(request.state, "signature_valid", None),
                request_payload=getattr(request.state, "request_payload", None),
                response_payload=getattr(request.state, "response_payload", None),
            )
        )
        session.commit()


@app.get("/api/heartbeat", tags=["epoint"])
async def heartbeat(request: Request) -> dict[str, str]:
    return {"status": "ok", "trace_id": request.state.trace_id}


for api_router in (
    epoint_router,
    cards_router,
    money_router,
    invoices_router,
    extras_router,
    b2b_router,
):
    app.include_router(api_router)

app.include_router(auth_router)
app.include_router(sandbox_public_router)
app.include_router(sandbox_router)
app.include_router(checkout_router)

_checkout_assets = Path(__file__).parent / "web" / "static"
app.mount("/checkout-assets", StaticFiles(directory=_checkout_assets), name="checkout-assets")

_dist = Path(__file__).parent / settings.web_dist_path

# Asset filenames carry a content hash, so they can be cached forever. The shell that
# points at them cannot: a stale copy asks for a hash that a newer image no longer has.
IMMUTABLE = "public, max-age=31536000, immutable"
REVALIDATE = "no-cache"


class HashedAssets(StaticFiles):
    def file_response(self, *args: Any, **kwargs: Any) -> Response:
        response = super().file_response(*args, **kwargs)
        response.headers["Cache-Control"] = IMMUTABLE
        return response


if _dist.is_dir():
    app.mount("/assets", HashedAssets(directory=_dist / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    async def spa(path: str) -> Response:
        candidate = _dist / path
        if path and candidate.is_file():
            return FileResponse(candidate, headers={"Cache-Control": REVALIDATE})
        return FileResponse(_dist / "index.html", headers={"Cache-Control": REVALIDATE})

else:

    @app.get("/", include_in_schema=False)
    async def dashboard_missing() -> JSONResponse:
        return JSONResponse(
            {
                "status": "ok",
                "message": "API is running. The dashboard bundle is not present in this build.",
                "docs": "/docs",
            }
        )
