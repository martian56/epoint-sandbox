from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel

from epoint_sandbox.config import get_settings
from epoint_sandbox.services import auth

router = APIRouter(prefix="/_sandbox/auth", tags=["sandbox"])


class Credentials(BaseModel):
    email: str
    password: str


class SessionState(BaseModel):
    auth_required: bool
    authenticated: bool
    email: str | None = None


def authenticated(request: Request) -> bool:
    settings = get_settings()
    if not auth.enabled(settings):
        return True
    return auth.token_valid(request.cookies.get(auth.COOKIE_NAME), settings) or auth.bearer_valid(
        request.headers.get("Authorization"), settings
    )


def require_admin(request: Request) -> None:
    if not authenticated(request):
        raise HTTPException(status_code=401, detail="Authentication required")


AdminOnly = Depends(require_admin)


@router.get("/session")
async def session_state(request: Request) -> SessionState:
    """Unauthenticated, so the dashboard can discover whether a login is needed."""
    settings = get_settings()
    if not auth.enabled(settings):
        return SessionState(auth_required=False, authenticated=True)

    is_authenticated = authenticated(request)
    return SessionState(
        auth_required=True,
        authenticated=is_authenticated,
        email=settings.admin_email if is_authenticated else None,
    )


@router.post("/login")
async def login(credentials: Credentials, response: Response) -> SessionState:
    settings = get_settings()
    if not auth.enabled(settings):
        return SessionState(auth_required=False, authenticated=True)

    if not auth.check_credentials(credentials.email, credentials.password, settings):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    response.set_cookie(
        auth.COOKIE_NAME,
        auth.issue_token(settings),
        max_age=settings.session_ttl_hours * 3600,
        httponly=True,
        samesite="lax",
        path="/",
    )
    return SessionState(auth_required=True, authenticated=True, email=settings.admin_email)


@router.post("/logout")
async def logout(response: Response) -> SessionState:
    response.delete_cookie(auth.COOKIE_NAME, path="/")
    return SessionState(auth_required=auth.enabled(), authenticated=False)


AdminDep = Annotated[None, AdminOnly]
