from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse


class EpointError(Exception):
    """An error shaped like an epoint failure response."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int = 200,
        code: str | None = None,
        hint: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.hint = hint

    def body(self, trace_id: str) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "status": "error",
            "message": self.message,
            "trace_id": trace_id,
        }
        if self.code:
            payload["code"] = self.code
        return payload


async def epoint_error_handler(request: Request, exc: EpointError) -> JSONResponse:
    trace_id = getattr(request.state, "trace_id", "")
    body = exc.body(trace_id)
    request.state.response_payload = body

    headers = {"X-Request-ID": trace_id, "X-Epoint-Sandbox": "1"}
    # Sandbox-only, so it goes in a header rather than the body.
    if exc.hint:
        headers["X-Sandbox-Hint"] = exc.hint.replace("\n", " ")

    return JSONResponse(body, status_code=exc.status_code, headers=headers)
