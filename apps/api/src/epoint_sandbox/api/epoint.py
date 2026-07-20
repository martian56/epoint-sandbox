from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select

from epoint_sandbox.api.deps import SessionDep, SignedRequestDep
from epoint_sandbox.api.errors import EpointError
from epoint_sandbox.models import Card, Merchant, Transaction
from epoint_sandbox.services import features, payments
from epoint_sandbox.services.payments import AZN_ONLY

router = APIRouter(prefix="/api/1", tags=["epoint"])


def _trace(request: Request) -> str:
    return str(getattr(request.state, "trace_id", ""))


def _redirect_response(
    transaction: Transaction, trace_id: str, *, include_transaction: bool = True
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "status": "success",
        "redirect_url": payments.checkout_url(transaction),
        # Documented on every one of these. The production wording is unknown.
        "message": "",
        "trace_id": trace_id,
    }
    if include_transaction:
        body["transaction"] = transaction.transaction_id
    return body


def _register_payment_route(
    path: str,
    *,
    currencies: set[str] | None = None,
    include_transaction: bool = True,
    feature: features.Feature | None = None,
) -> None:
    """The checkout family shares one behaviour, so register them from one place."""

    @router.post(path, name=f"epoint_{path.strip('/')}")
    async def handler(
        request: Request,
        signed: SignedRequestDep,
        session: SessionDep,
    ) -> dict[str, Any]:
        if feature is not None:
            features.require(signed.merchant, feature)
        trace_id = _trace(request)
        transaction = payments.create_transaction(
            session,
            signed,
            endpoint=path.strip("/"),
            trace_id=trace_id,
            allowed_currencies=currencies or payments.SUPPORTED_CURRENCIES,
        )
        return _redirect_response(transaction, trace_id, include_transaction=include_transaction)


for _path in ("/request", "/payment-request"):
    _register_payment_route(_path)

_register_payment_route("/amex-request", feature=features.AMEX)

# Docs omit `transaction` for this endpoint alone. Withheld until confirmed.
_register_payment_route("/payment-change-sum", include_transaction=False)


@router.post("/checkout")
async def checkout_redirect(
    request: Request,
    signed: SignedRequestDep,
    session: SessionDep,
) -> RedirectResponse:
    """Form-post variant. The browser lands on the payment page instead of getting JSON."""
    transaction = payments.create_transaction(
        session, signed, endpoint="checkout", trace_id=_trace(request)
    )
    return RedirectResponse(payments.checkout_url(transaction), status_code=303)


@router.post("/split-request")
async def split_request(
    request: Request,
    signed: SignedRequestDep,
    session: SessionDep,
) -> dict[str, Any]:
    signed.require("split_user", "split_amount")
    trace_id = _trace(request)

    partner = session.scalar(
        select(Merchant).where(Merchant.public_key == signed.get("split_user"))
    )
    if partner is None:
        raise EpointError(f"Unknown split_user: {signed.get('split_user')}", status_code=403)

    transaction = payments.create_transaction(
        session, signed, endpoint="split-request", trace_id=trace_id, allowed_currencies=AZN_ONLY
    )
    split_amount = payments.parse_amount(signed.get("split_amount"), "split_amount")
    if split_amount > transaction.amount:
        raise EpointError("split_amount cannot exceed amount")

    transaction.split_merchant_id = partner.id
    transaction.split_amount = split_amount
    session.flush()

    return _redirect_response(transaction, trace_id)


@router.post("/pre-auth-request")
async def pre_auth_request(
    request: Request,
    signed: SignedRequestDep,
    session: SessionDep,
) -> dict[str, Any]:
    trace_id = _trace(request)
    transaction = payments.create_transaction(
        session, signed, endpoint="pre-auth-request", trace_id=trace_id, allowed_currencies=AZN_ONLY
    )
    return _redirect_response(transaction, trace_id)


@router.post("/get-status")
async def get_status(
    request: Request,
    signed: SignedRequestDep,
    session: SessionDep,
) -> dict[str, Any]:
    signed.require("transaction")

    transaction = session.scalar(
        select(Transaction).where(
            Transaction.transaction_id == signed.get("transaction"),
            Transaction.merchant_id == signed.merchant.id,
        )
    )
    if transaction is None:
        raise EpointError(f"Unknown transaction: {signed.get('transaction')}")

    return {
        "status": transaction.status.value,
        "code": transaction.bank_code or "",
        "message": transaction.message or "",
        "transaction": transaction.transaction_id,
        "bank_transaction": transaction.bank_transaction or "",
        "bank_response": transaction.bank_code or "",
        "operation_code": transaction.operation_code or "",
        "rrn": transaction.rrn,
        "card_name": transaction.card_name,
        "card_mask": transaction.card_mask,
        "amount": float(transaction.amount),
        "other_attr": transaction.other_attr,
        "trace_id": _trace(request),
    }


@router.post("/get-status-card")
async def get_status_card(
    request: Request,
    signed: SignedRequestDep,
    session: SessionDep,
) -> dict[str, Any]:
    signed.require("card_id")

    card = session.scalar(
        select(Card).where(
            Card.card_id == signed.get("card_id"),
            Card.merchant_id == signed.merchant.id,
        )
    )
    if card is None:
        raise EpointError(f"Unknown card_id: {signed.get('card_id')}")

    return {
        "id": card.card_id,
        "name": card.holder_name,
        "mask": card.mask,
        "status": card.status.value,
        "expired_date": card.expiry,
        "description": card.description,
        "trace_id": _trace(request),
    }
