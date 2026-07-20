from sqlalchemy import select
from sqlalchemy.orm import Session

from epoint_sandbox.config import DEFAULT_MERCHANTS
from epoint_sandbox.models import Merchant
from epoint_sandbox.services import auth
from epoint_sandbox.services import merchants as merchant_service

SEED_TIN = "1234567891"
SEED_PHONE = "+994501234567"


def seed_default_merchants(session: Session) -> list[Merchant]:
    """Seed the demo accounts.

    The documented keys are published, so a secured instance gets generated ones
    instead. Otherwise the login gate would protect the dashboard while anyone
    could still sign requests with a key from the README.
    """
    published_keys = not auth.enabled()

    merchants = []
    for public_key, private_key, name in DEFAULT_MERCHANTS:
        existing = session.scalar(select(Merchant).where(Merchant.public_key == public_key))
        if existing is not None:
            merchants.append(existing)
            continue

        merchant = Merchant(
            public_key=public_key,
            private_key=private_key if published_keys else merchant_service.generate_private_key(),
            name=name,
            tin=SEED_TIN,
            contact_phone=SEED_PHONE,
        )
        session.add(merchant)
        merchants.append(merchant)

    session.flush()
    return merchants
