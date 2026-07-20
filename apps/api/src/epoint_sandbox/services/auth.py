import hashlib
import hmac
import time

from epoint_sandbox.config import Settings, get_settings

COOKIE_NAME = "epoint_session"


def enabled(settings: Settings | None = None) -> bool:
    settings = settings or get_settings()
    return bool(settings.admin_email and settings.admin_password)


def _secret(settings: Settings) -> bytes:
    """Derived from the credentials, so changing either invalidates live sessions."""
    return hashlib.sha256(f"{settings.admin_email}:{settings.admin_password}".encode()).digest()


def check_credentials(email: str, password: str, settings: Settings | None = None) -> bool:
    settings = settings or get_settings()
    if not enabled(settings):
        return False

    email_ok = hmac.compare_digest(email.strip().lower(), settings.admin_email.strip().lower())
    password_ok = hmac.compare_digest(password, settings.admin_password)
    return email_ok and password_ok


def issue_token(settings: Settings | None = None) -> str:
    """Signed rather than stored, so sessions survive a restart and span workers."""
    settings = settings or get_settings()
    expires = int(time.time()) + settings.session_ttl_hours * 3600
    return f"{expires}.{_sign(expires, settings)}"


def token_valid(token: str | None, settings: Settings | None = None) -> bool:
    settings = settings or get_settings()
    if not token or not enabled(settings):
        return False

    expires_raw, _, signature = token.partition(".")
    if not signature:
        return False

    try:
        expires = int(expires_raw)
    except ValueError:
        return False

    if expires < time.time():
        return False

    return hmac.compare_digest(signature, _sign(expires, settings))


def _sign(expires: int, settings: Settings) -> str:
    return hmac.new(_secret(settings), str(expires).encode(), hashlib.sha256).hexdigest()


def bearer_valid(header: str | None, settings: Settings | None = None) -> bool:
    """Scripts authenticate with the admin password rather than a browser session."""
    settings = settings or get_settings()
    if not header or not enabled(settings):
        return False

    scheme, _, credential = header.partition(" ")
    if scheme.lower() != "bearer" or not credential:
        return False

    return hmac.compare_digest(credential, settings.admin_password)
