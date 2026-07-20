"""Refunds, payouts and reversals.

epoint routes refunds and payouts through one endpoint, chosen by the card's
refund flag. The mode taken is reported in X-Sandbox-Mode.
"""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Request
from sqlalchemy import select

from epoint_sandbox.api.deps import SessionDep, SignedRequestDep
from epoint_sandbox.api.errors import EpointError
from epoint_sandbox.models import Card, CardStatus, Transaction, TransactionStatus
from epoint_sandbox.services import callbacks, ids, payments, settlement
from epoint_sandbox.services.payments import AZN_ONLY

router = APIRouter(prefix="/api/1", tags=["money"])


def _trace(request: Request) -> str:
    return str(getattr(request.state, "trace_id", ""))


@router.post("/refund-request")
async def refund_request(
    request: Request,
    signed: SignedRequestDep,
    session: SessionDep,
) -> dict[str, Any]:
    signed.require("card_id", "order_id", "amount", "currency")
    trace_id = _trace(request)

    card = session.scalar(
        select(Card).where(
            Card.card_id == signed.get("card_id"),
            Card.merchant_id == signed.merchant.id,
        )
    )
    if card is None:
        raise EpointError(f"Unknown card_id: {signed.get('card_id')}")
    if card.status is not CardStatus.ACTIVE:
        raise EpointError(f"Card {card.card_id} is {card.status.value}, not active")

    amount = payments.parse_amount(signed.get("amount"))
    payments.validate_currency(str(signed.get("currency")), AZN_ONLY)

    available = settlement.available_balance(session, signed.merchant.id)
    if amount > available:
        raise EpointError(
            f"Insufficient balance. Available: {available}, requested: {amount}",
            code="116",
        )

    mode = settlement.Kind.PAYOUT if card.is_payout_card else settlement.Kind.REFUND
    transaction = Transaction(
        transaction_id=ids.placeholder(),
        merchant_id=signed.merchant.id,
        order_id=str(signed.get("order_id")),
        amount=amount,
        currency="AZN",
        description=signed.get("description"),
        language=str(signed.get("language", "az")),
        status=TransactionStatus.RETURNED,
        endpoint="refund-request",
        bank_transaction=ids.bank_transaction_id(),
        bank_code="000",
        message="Approved",
        rrn=ids.rrn(),
        card_id=card.id,
        card_mask=card.mask,
        card_name=card.holder_name,
        trace_id=trace_id,
        paid_at=datetime.now(UTC),
    )
    session.add(transaction)
    session.flush()
    transaction.transaction_id = ids.transaction_id(transaction.id)
    session.flush()

    settlement.settle_debit(
        session, signed.merchant, amount, mode, transaction, f"{mode} to {card.mask}"
    )
    callbacks.deliver(session, transaction)

    # Sandbox-only, so it goes in a header rather than the body.
    request.state.sandbox_headers = {"X-Sandbox-Mode": mode}

    return {
        "status": "success",
        "transaction": transaction.transaction_id,
        "bank_transaction": transaction.bank_transaction,
        "bank_response": transaction.bank_code,
        "rrn": transaction.rrn,
        "card_mask": transaction.card_mask,
        "card_name": transaction.card_name,
        "amount": float(amount),
        "message": transaction.message,
        "trace_id": trace_id,
    }


@router.post("/reverse")
async def reverse(
    request: Request,
    signed: SignedRequestDep,
    session: SessionDep,
) -> dict[str, Any]:
    signed.require("transaction", "currency")
    trace_id = _trace(request)
    payments.validate_currency(str(signed.get("currency")), AZN_ONLY)

    original = session.scalar(
        select(Transaction).where(
            Transaction.transaction_id == signed.get("transaction"),
            Transaction.merchant_id == signed.merchant.id,
        )
    )
    if original is None:
        raise EpointError(f"Unknown transaction: {signed.get('transaction')}")
    if original.status is not TransactionStatus.SUCCESS:
        raise EpointError(
            f"Only successful transactions can be reversed, this is {original.status.value}"
        )

    raw_amount = signed.get("amount")
    amount = payments.parse_amount(raw_amount) if raw_amount else Decimal(str(original.amount))
    if amount > original.amount:
        raise EpointError("Reversal amount cannot exceed the original amount")

    original.status = TransactionStatus.RETURNED
    original.message = "Reversed"
    session.flush()

    settlement.settle_debit(
        session,
        signed.merchant,
        amount,
        settlement.Kind.REVERSAL,
        original,
        f"Reversal of {original.order_id}",
    )
    callbacks.deliver(session, original)

    return {"status": "success", "trace_id": trace_id}


@router.post("/pre-auth-complete")
async def pre_auth_complete(
    request: Request,
    signed: SignedRequestDep,
    session: SessionDep,
) -> dict[str, Any]:
    signed.require("transaction", "amount")
    trace_id = _trace(request)

    held = session.scalar(
        select(Transaction).where(
            Transaction.transaction_id == signed.get("transaction"),
            Transaction.merchant_id == signed.merchant.id,
            Transaction.endpoint == "pre-auth-request",
        )
    )
    if held is None:
        raise EpointError(f"Unknown pre-authorisation: {signed.get('transaction')}")
    if held.status is not TransactionStatus.SUCCESS:
        raise EpointError(f"Pre-authorisation is {held.status.value}, nothing to capture")
    if held.paid_at and held.endpoint == "pre-auth-complete":
        raise EpointError("Pre-authorisation has already been captured")

    amount = payments.parse_amount(signed.get("amount"))
    if amount > held.amount:
        raise EpointError("Capture cannot exceed the held amount")

    held.amount = amount
    held.endpoint = "pre-auth-complete"
    session.flush()
    settlement.settle_payment(session, held)

    return {
        "status": "success",
        "transaction": held.transaction_id,
        "trace_id": trace_id,
    }
