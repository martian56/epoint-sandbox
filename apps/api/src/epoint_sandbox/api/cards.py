from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Request
from sqlalchemy import select

from epoint_sandbox.api.deps import SessionDep, SignedRequestDep
from epoint_sandbox.api.errors import EpointError
from epoint_sandbox.models import Card, CardStatus, Merchant, Transaction, TransactionStatus
from epoint_sandbox.models.enums import OperationCode
from epoint_sandbox.services import callbacks, ids, magic_cards, payments, settlement
from epoint_sandbox.services.payments import AZN_ONLY

router = APIRouter(prefix="/api/1", tags=["cards"])


def _trace(request: Request) -> str:
    return str(getattr(request.state, "trace_id", ""))


def _load_card(session: SessionDep, signed: SignedRequestDep) -> Card:
    signed.require("card_id")
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
    return card


@router.post("/card-registration")
async def card_registration(
    request: Request,
    signed: SignedRequestDep,
    session: SessionDep,
) -> dict[str, Any]:
    """Start tokenisation. The customer confirms at checkout."""
    signed.require("language")
    trace_id = _trace(request)

    card = Card(
        card_id=ids.placeholder(),
        merchant_id=signed.merchant.id,
        mask="",
        status=CardStatus.NEW,
        is_payout_card=str(signed.get("refund", "0")) == "1",
        description=signed.get("description"),
    )
    session.add(card)
    session.flush()
    card.card_id = ids.card_id(card.id)

    holder = Transaction(
        transaction_id=ids.placeholder(),
        merchant_id=signed.merchant.id,
        order_id=f"card-registration-{card.card_id}",
        amount=0,
        currency="AZN",
        language=str(signed.get("language", "az")),
        status=TransactionStatus.NEW,
        endpoint="card-registration",
        checkout_token=ids.checkout_token(),
        operation_code=OperationCode.CARD_REGISTRATION.value,
        card_id=card.id,
        success_redirect_url=signed.get("success_redirect_url"),
        error_redirect_url=signed.get("error_redirect_url"),
        trace_id=trace_id,
    )
    session.add(holder)
    session.flush()
    holder.transaction_id = ids.transaction_id(holder.id)
    session.flush()

    return {
        "status": "success",
        "code": "000",
        "message": "Card registration started",
        "card_id": card.card_id,
        "bank_transaction": None,
        "bank_response": None,
        "redirect_url": payments.checkout_url(holder),
        "trace_id": trace_id,
    }


@router.post("/card-registration-with-pay")
async def card_registration_with_pay(
    request: Request,
    signed: SignedRequestDep,
    session: SessionDep,
) -> dict[str, Any]:
    trace_id = _trace(request)
    transaction = payments.create_transaction(
        session, signed, endpoint="card-registration-with-pay", trace_id=trace_id
    )

    card = Card(
        card_id=ids.placeholder(),
        merchant_id=signed.merchant.id,
        mask="",
        status=CardStatus.NEW,
        description=signed.get("description"),
    )
    session.add(card)
    session.flush()
    card.card_id = ids.card_id(card.id)

    transaction.card_id = card.id
    transaction.operation_code = OperationCode.REGISTRATION_WITH_PAYMENT.value
    session.flush()

    return {
        "status": "success",
        "redirect_url": payments.checkout_url(transaction),
        "card_id": card.card_id,
        "transaction": transaction.transaction_id,
        "trace_id": trace_id,
    }


def _charge_saved_card(
    session: SessionDep,
    signed: SignedRequestDep,
    card: Card,
    *,
    endpoint: str,
    trace_id: str,
) -> Transaction:
    """Server-to-server charge. No redirect."""
    transaction = payments.create_transaction(
        session, signed, endpoint=endpoint, trace_id=trace_id, allowed_currencies=AZN_ONLY
    )
    outcome = magic_cards.outcome_for_code(card.bank_code)

    transaction.card_id = card.id
    transaction.card_mask = card.mask
    transaction.card_name = card.holder_name
    transaction.bank_transaction = ids.bank_transaction_id()
    transaction.bank_code = outcome.bank_code or None
    transaction.message = outcome.message
    transaction.operation_code = OperationCode.PAYMENT.value
    transaction.paid_at = datetime.now(UTC)
    transaction.status = TransactionStatus.SUCCESS if outcome.approved else TransactionStatus.FAILED
    if outcome.approved:
        transaction.rrn = ids.rrn()
        settlement.settle_payment(session, transaction)

    session.flush()
    callbacks.deliver(session, transaction)
    return transaction


def _charge_response(transaction: Transaction, trace_id: str) -> dict[str, Any]:
    return {
        "status": "success" if transaction.status is TransactionStatus.SUCCESS else "failed",
        "transaction": transaction.transaction_id,
        "bank_transaction": transaction.bank_transaction,
        "bank_response": transaction.bank_code,
        "rrn": transaction.rrn,
        "card_name": transaction.card_name,
        "card_mask": transaction.card_mask,
        "amount": float(transaction.amount),
        "message": transaction.message,
        "trace_id": trace_id,
    }


@router.post("/execute-pay")
async def execute_pay(
    request: Request,
    signed: SignedRequestDep,
    session: SessionDep,
) -> dict[str, Any]:
    signed.require("language", "card_id", "order_id", "amount", "currency")
    card = _load_card(session, signed)
    trace_id = _trace(request)
    transaction = _charge_saved_card(
        session, signed, card, endpoint="execute-pay", trace_id=trace_id
    )
    return _charge_response(transaction, trace_id)


@router.post("/split-execute-pay")
async def split_execute_pay(
    request: Request,
    signed: SignedRequestDep,
    session: SessionDep,
) -> dict[str, Any]:
    signed.require(
        "language", "card_id", "order_id", "amount", "currency", "split_user", "split_amount"
    )
    card = _load_card(session, signed)
    trace_id = _trace(request)

    partner = session.scalar(
        select(Merchant).where(Merchant.public_key == signed.get("split_user"))
    )
    if partner is None:
        raise EpointError(f"Unknown split_user: {signed.get('split_user')}", status_code=403)

    split_amount = payments.parse_amount(signed.get("split_amount"), "split_amount")
    transaction = payments.create_transaction(
        session,
        signed,
        endpoint="split-execute-pay",
        trace_id=trace_id,
        allowed_currencies=AZN_ONLY,
    )
    if split_amount > transaction.amount:
        raise EpointError("split_amount cannot exceed amount")

    transaction.split_merchant_id = partner.id
    transaction.split_amount = split_amount
    transaction.card_id = card.id
    transaction.card_mask = card.mask
    transaction.card_name = card.holder_name
    transaction.bank_transaction = ids.bank_transaction_id()

    outcome = magic_cards.outcome_for_code(card.bank_code)
    transaction.bank_code = outcome.bank_code or None
    transaction.message = outcome.message
    transaction.operation_code = OperationCode.PAYMENT.value
    transaction.paid_at = datetime.now(UTC)
    transaction.status = TransactionStatus.SUCCESS if outcome.approved else TransactionStatus.FAILED
    if outcome.approved:
        transaction.rrn = ids.rrn()
        settlement.settle_payment(session, transaction)

    session.flush()
    callbacks.deliver(session, transaction)

    response = _charge_response(transaction, trace_id)
    response["split_amount"] = float(split_amount)
    return response
