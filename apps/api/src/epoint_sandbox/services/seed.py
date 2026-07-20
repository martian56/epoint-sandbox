from sqlalchemy import select
from sqlalchemy.orm import Session

from epoint_sandbox.config import DEFAULT_MERCHANTS
from epoint_sandbox.models import Merchant

SEED_TIN = "1234567891"
SEED_PHONE = "+994501234567"


def seed_default_merchants(session: Session) -> list[Merchant]:
    merchants = []
    for public_key, private_key, name in DEFAULT_MERCHANTS:
        existing = session.scalar(select(Merchant).where(Merchant.public_key == public_key))
        if existing is not None:
            merchants.append(existing)
            continue

        merchant = Merchant(
            public_key=public_key,
            private_key=private_key,
            name=name,
            tin=SEED_TIN,
            contact_phone=SEED_PHONE,
        )
        session.add(merchant)
        merchants.append(merchant)

    session.flush()
    return merchants
