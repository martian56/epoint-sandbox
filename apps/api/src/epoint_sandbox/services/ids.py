import secrets
import uuid

TRANSACTION_PREFIX = "te"
TRANSACTION_WIDTH = 10
CARD_PREFIX = "ce"
CARD_WIDTH = 8


def public_id(prefix: str, row_id: int, width: int) -> str:
    """Derive a public identifier from the row's primary key.

    A counter would collide after a restart.
    """
    return f"{prefix}{row_id:0{width}d}"


def transaction_id(row_id: int) -> str:
    return public_id(TRANSACTION_PREFIX, row_id, TRANSACTION_WIDTH)


def card_id(row_id: int) -> str:
    return public_id(CARD_PREFIX, row_id, CARD_WIDTH)


def bank_transaction_id() -> str:
    return f"BT{secrets.randbelow(10**8):08d}"


def rrn() -> str:
    return f"{secrets.randbelow(10**12):012d}"


def trace_id() -> str:
    return uuid.uuid4().hex


def checkout_token() -> str:
    return secrets.token_urlsafe(24)


def placeholder() -> str:
    """Placeholder held until the row id exists. Must fit a 32 character column."""
    return f"tmp{uuid.uuid4().hex[:20]}"
