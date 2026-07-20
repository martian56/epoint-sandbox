"""B2B bank transfers.

Unlike the rest of the API these take a JSON body, return real HTTP status
codes, and send an unsigned JSON webhook.
"""

import re
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import select

from epoint_sandbox.api.deps import SessionDep, SignedRequestDep
from epoint_sandbox.api.errors import EpointError
from epoint_sandbox.models import B2BPayment, B2BStatus
from epoint_sandbox.services import features, ids, payments, webhooks

router = APIRouter(prefix="/api/1/b2b", tags=["b2b"])

IBAN = re.compile(r"^AZ[0-9A-Z]{18,32}$")
TIN = re.compile(r"^\d{9}[12]$")

MIN_AMOUNT = 0.01
MAX_AMOUNT = 40000


def _reject(message: str, status_code: int = 422) -> HTTPException:
    return HTTPException(status_code=status_code, detail=message)


@router.post("/payment", status_code=200)
async def create_payment(
    request: Request, signed: SignedRequestDep, session: SessionDep
) -> dict[str, Any]:
    features.require(signed.merchant, features.B2B)

    for field in ("order_id", "amount", "description", "iban", "name", "tin", "bank_code"):
        if signed.get(field) in (None, ""):
            raise _reject(f"Missing required parameter: {field}")

    iban = str(signed.get("iban")).upper()
    if not IBAN.match(iban):
        raise _reject(f"iban must start with AZ and be a valid length, got {iban}")

    tin = str(signed.get("tin"))
    if not TIN.match(tin):
        raise _reject("tin must be 10 digits ending in 1 (individual) or 2 (legal entity)")

    # Reported as a status code here, not the shared error body.
    try:
        amount = payments.parse_amount(signed.get("amount"))
    except EpointError as exc:
        raise _reject(exc.message) from exc

    if not (MIN_AMOUNT <= float(amount) <= MAX_AMOUNT):
        raise _reject(f"amount must be between {MIN_AMOUNT} and {MAX_AMOUNT}")

    if len(str(signed.get("description"))) > 255:
        raise _reject("description must be 255 characters or fewer")

    order_id = str(signed.get("order_id"))
    existing = session.scalar(
        select(B2BPayment).where(
            B2BPayment.merchant_id == signed.merchant.id,
            B2BPayment.order_id == order_id,
        )
    )
    if existing is not None:
        raise _reject(f"order_id {order_id} has already been used")

    payment = B2BPayment(
        merchant_id=signed.merchant.id,
        order_id=order_id,
        amount=amount,
        description=str(signed.get("description")),
        payee_iban=iban,
        payee_name=str(signed.get("name")),
        payee_tin=tin,
        bank_code=str(signed.get("bank_code")),
        bank_name=signed.get("bank_name"),
        email=signed.get("email"),
        address=signed.get("address"),
        additional_info=signed.get("additional_info"),
        bulk_description=signed.get("bulk_description"),
        webhook_url=signed.get("webhook_url"),
        status=B2BStatus.PENDING,
        bulk_id=str(ids.bank_transaction_id()),
        trace_id=str(getattr(request.state, "trace_id", "")),
    )
    session.add(payment)
    session.flush()
    session.commit()

    return {"status": "success", "order_id": payment.order_id, "bulkId": payment.bulk_id}


@router.get("/payment/{order_id}")
async def payment_status(order_id: str, session: SessionDep) -> dict[str, Any]:
    payment = session.scalar(select(B2BPayment).where(B2BPayment.order_id == order_id))
    if payment is None:
        raise HTTPException(status_code=404, detail=f"Unknown order_id: {order_id}")

    return {
        "status": payment.status.value,
        "order_id": payment.order_id,
        "bulkId": payment.bulk_id,
        "amount": str(payment.amount),
        "payee_iban": payment.payee_iban,
        "payee_name": payment.payee_name,
        "webhook_sent": payment.webhook_sent,
        "created_at": payment.created_at.isoformat(),
    }


@router.post("/payment/{order_id}/advance", include_in_schema=False)
async def advance(order_id: str, session: SessionDep) -> dict[str, Any]:
    """Step a transfer through its lifecycle without waiting."""
    payment = session.scalar(select(B2BPayment).where(B2BPayment.order_id == order_id))
    if payment is None:
        raise HTTPException(status_code=404, detail=f"Unknown order_id: {order_id}")

    nxt = {
        B2BStatus.PENDING: B2BStatus.PROCESSING,
        B2BStatus.PROCESSING: B2BStatus.SUCCESS,
    }.get(payment.status)

    if nxt is None:
        raise HTTPException(status_code=409, detail=f"{payment.status.value} is terminal")

    payment.status = nxt
    session.flush()

    if nxt in (B2BStatus.SUCCESS, B2BStatus.FAILED):
        webhooks.deliver_b2b(session, payment)

    return {"status": payment.status.value, "order_id": payment.order_id}
