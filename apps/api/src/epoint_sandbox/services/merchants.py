"""Merchant lifecycle.

Keys use the same formats epoint issues: `i` plus nine digits, and a 24
character secret.
"""

import secrets
import string

from sqlalchemy import select
from sqlalchemy.orm import Session

from epoint_sandbox.models import Merchant

PUBLIC_KEY_PREFIX = "i"
PUBLIC_KEY_DIGITS = 9
PRIVATE_KEY_LENGTH = 24
PRIVATE_KEY_ALPHABET = string.ascii_letters + string.digits

INTEGRATION_URL_FIELDS = ("site_url", "success_url", "error_url", "result_url")
PROFILE_FIELDS = ("name", "tin", "contact_phone")
FEATURE_FIELDS = (
    "amex_enabled",
    "token_payments_enabled",
    "installments_enabled",
    "wallets_enabled",
    "b2b_enabled",
)


def public_key_for(row_id: int) -> str:
    return f"{PUBLIC_KEY_PREFIX}{row_id:0{PUBLIC_KEY_DIGITS}d}"


def generate_private_key() -> str:
    return "".join(secrets.choice(PRIVATE_KEY_ALPHABET) for _ in range(PRIVATE_KEY_LENGTH))


def create(session: Session, **fields: str | None) -> Merchant:
    """Create an account, deriving its public key from the row id."""
    merchant = Merchant(
        public_key=f"pending-{secrets.token_hex(8)}",
        private_key=generate_private_key(),
        name=str(fields.get("name") or "Untitled merchant"),
    )
    apply_changes(merchant, fields)

    session.add(merchant)
    session.flush()
    merchant.public_key = public_key_for(merchant.id)
    session.flush()
    return merchant


def apply_changes(merchant: Merchant, changes: dict[str, str | None]) -> Merchant:
    for field in PROFILE_FIELDS + INTEGRATION_URL_FIELDS:
        if field in changes:
            value = changes[field]
            setattr(merchant, field, value or None)

    for field in FEATURE_FIELDS:
        if field in changes and changes[field] is not None:
            setattr(merchant, field, bool(changes[field]))

    if not merchant.name:
        merchant.name = "Untitled merchant"
    return merchant


def rotate_private_key(merchant: Merchant) -> Merchant:
    merchant.private_key = generate_private_key()
    return merchant


def find(session: Session, public_key: str) -> Merchant | None:
    return session.scalar(select(Merchant).where(Merchant.public_key == public_key))


def count(session: Session) -> int:
    return len(session.scalars(select(Merchant)).all())
