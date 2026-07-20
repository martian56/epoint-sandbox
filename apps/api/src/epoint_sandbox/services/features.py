"""Per-merchant feature grants.

epoint enables these on request, so they are off until switched on.
"""

from dataclasses import dataclass

from epoint_sandbox.api.errors import EpointError
from epoint_sandbox.models import Merchant


@dataclass(frozen=True)
class Feature:
    field: str
    label: str


AMEX = Feature("amex_enabled", "AMEX payments")
TOKEN_PAYMENTS = Feature("token_payments_enabled", "Apple Pay and Google Pay")
INSTALLMENTS = Feature("installments_enabled", "Installment payments")
WALLETS = Feature("wallets_enabled", "Wallet payments")
B2B = Feature("b2b_enabled", "B2B bank transfers")

ALL = (AMEX, TOKEN_PAYMENTS, INSTALLMENTS, WALLETS, B2B)


def is_enabled(merchant: Merchant, feature: Feature) -> bool:
    return bool(getattr(merchant, feature.field))


def require(merchant: Merchant, feature: Feature) -> None:
    if is_enabled(merchant, feature):
        return
    raise EpointError(
        f"{feature.label} are not enabled for {merchant.public_key}. "
        "In production you request this from epoint support; "
        "in the sandbox, enable it on the API Management page.",
        status_code=403,
    )


def as_dict(merchant: Merchant) -> dict[str, bool]:
    return {f.field: is_enabled(merchant, f) for f in ALL}
