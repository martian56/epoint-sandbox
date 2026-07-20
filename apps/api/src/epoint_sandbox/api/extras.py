"""Installments, wallets and the Apple Pay / Google Pay widget.

The catalogues are fixtures. Real ones are unverified.
"""

from typing import Any

from fastapi import APIRouter, Request

from epoint_sandbox.api.deps import SessionDep, SignedRequestDep
from epoint_sandbox.api.errors import EpointError
from epoint_sandbox.config import get_settings
from epoint_sandbox.services import features, payments
from epoint_sandbox.services.payments import AZN_ONLY

router = APIRouter(prefix="/api/1", tags=["extras"])

INSTALLMENT_CARDS = [
    {"name": "Birbank Taksit", "installment_card_id": "1", "installment_months": [3, 6, 12]},
    {"name": "Tamkart Taksit", "installment_card_id": "2", "installment_months": [3, 6, 9, 12]},
    {"name": "Bolkart", "installment_card_id": "3", "installment_months": [2, 3, 6]},
]

WALLETS = {
    "wallet_epul": "E-Pul",
    "wallet_mpay": "MPAY",
    "wallet_portmanat": "Portmanat",
}


def _trace(request: Request) -> str:
    return str(getattr(request.state, "trace_id", ""))


@router.post("/get-installment-request")
async def get_installments(
    request: Request, signed: SignedRequestDep, session: SessionDep
) -> list[dict[str, Any]]:
    signed.require("currency", "language", "order_id")
    features.require(signed.merchant, features.INSTALLMENTS)
    payments.validate_currency(str(signed.get("currency")))
    return INSTALLMENT_CARDS


@router.post("/installment-request")
async def installment_request(
    request: Request, signed: SignedRequestDep, session: SessionDep
) -> dict[str, Any]:
    signed.require("installment_card_id", "installment_month")
    features.require(signed.merchant, features.INSTALLMENTS)
    trace_id = _trace(request)

    card_id = str(signed.get("installment_card_id"))
    plan = next((c for c in INSTALLMENT_CARDS if c["installment_card_id"] == card_id), None)
    if plan is None:
        raise EpointError(f"Unknown installment_card_id: {card_id}")

    month = int(signed.get("installment_month"))
    if month not in plan["installment_months"]:
        raise EpointError(
            f"{plan['name']} does not offer {month} months. Available: {plan['installment_months']}"
        )

    transaction = payments.create_transaction(
        session, signed, endpoint="installment-request", trace_id=trace_id
    )
    return {
        "status": "success",
        "redirect_url": payments.checkout_url(transaction),
        "transaction": transaction.transaction_id,
        "message": "",
        "trace_id": trace_id,
    }


@router.post("/wallet/status")
async def wallet_status(
    request: Request, signed: SignedRequestDep, session: SessionDep
) -> dict[str, str]:
    features.require(signed.merchant, features.WALLETS)
    return WALLETS


@router.post("/wallet/payment")
async def wallet_payment(
    request: Request, signed: SignedRequestDep, session: SessionDep
) -> dict[str, Any]:
    signed.require("wallet_id")
    features.require(signed.merchant, features.WALLETS)
    trace_id = _trace(request)

    wallet_id = str(signed.get("wallet_id"))
    if wallet_id not in WALLETS:
        raise EpointError(f"Unknown wallet_id: {wallet_id}. Available: {', '.join(WALLETS)}")

    transaction = payments.create_transaction(
        session, signed, endpoint="wallet-payment", trace_id=trace_id, allowed_currencies=AZN_ONLY
    )
    return {
        "status": "success",
        "redirect_url": payments.checkout_url(transaction),
        "transaction": transaction.transaction_id,
        "message": "",
        "trace_id": trace_id,
    }


@router.post("/token/widget")
async def token_widget(
    request: Request, signed: SignedRequestDep, session: SessionDep
) -> dict[str, Any]:
    signed.require("amount", "order_id", "description")
    features.require(signed.merchant, features.TOKEN_PAYMENTS)
    trace_id = _trace(request)

    transaction = payments.create_transaction(
        session,
        signed,
        endpoint="token-widget",
        trace_id=trace_id,
        allowed_currencies=AZN_ONLY,
        default_currency="AZN",
        require_language=False,
    )
    base = get_settings().public_base_url
    return {
        "status": "success",
        "widget_url": f"{base}/checkout/{transaction.checkout_token}?widget=1",
        "transaction": transaction.transaction_id,
        "trace_id": trace_id,
    }
