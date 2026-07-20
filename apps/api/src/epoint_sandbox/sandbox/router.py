from typing import Annotated, Any

from fastapi import APIRouter, Body, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from epoint_sandbox import signing
from epoint_sandbox.api.deps import SessionDep
from epoint_sandbox.models import (
    B2BPayment,
    BalanceEntry,
    Callback,
    Card,
    Invoice,
    Merchant,
    Notification,
    RequestLog,
    Transaction,
)
from epoint_sandbox.services import features, magic_cards, payments
from epoint_sandbox.services import merchants as merchant_service

router = APIRouter(prefix="/_sandbox", tags=["sandbox"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/cards")
async def cards() -> dict[str, Any]:
    return {
        "scheme": "4000 0000 0000 0NNN maps to bank response code NNN",
        "cards": magic_cards.catalogue(),
    }


@router.get("/merchants")
async def merchants(session: SessionDep) -> list[dict[str, Any]]:
    rows = session.scalars(select(Merchant).order_by(Merchant.id)).all()
    return [_serialise_merchant(session, m) for m in rows]


class MerchantInput(BaseModel):
    name: str | None = None
    tin: str | None = None
    contact_phone: str | None = None
    site_url: str | None = None
    result_url: str | None = None
    success_url: str | None = None
    error_url: str | None = None
    amex_enabled: bool | None = None
    token_payments_enabled: bool | None = None
    installments_enabled: bool | None = None
    wallets_enabled: bool | None = None
    b2b_enabled: bool | None = None


def _serialise_merchant(session: Session, merchant: Merchant) -> dict[str, Any]:
    return {
        "public_key": merchant.public_key,
        "private_key": merchant.private_key,
        "name": merchant.name,
        "tin": merchant.tin,
        "contact_phone": merchant.contact_phone,
        "site_url": merchant.site_url,
        "result_url": merchant.result_url,
        "success_url": merchant.success_url,
        "error_url": merchant.error_url,
        "balance": float(payments.current_balance(session, merchant.id)),
        "features": features.as_dict(merchant),
        "created_at": merchant.created_at.isoformat(),
    }


def _require_merchant(session: Session, public_key: str) -> Merchant:
    merchant = merchant_service.find(session, public_key)
    if merchant is None:
        raise HTTPException(status_code=404, detail=f"Unknown public_key: {public_key}")
    return merchant


@router.post("/merchants", status_code=201)
async def create_merchant(payload: MerchantInput, session: SessionDep) -> dict[str, Any]:
    """Create an account."""
    merchant = merchant_service.create(session, **payload.model_dump(exclude_unset=True))
    return _serialise_merchant(session, merchant)


@router.delete("/merchants/{public_key}", status_code=204)
async def delete_merchant(public_key: str, session: SessionDep) -> None:
    merchant = _require_merchant(session, public_key)

    if merchant_service.count(session) <= 1:
        raise HTTPException(status_code=409, detail="Cannot delete the only merchant")

    if merchant.transactions:
        raise HTTPException(
            status_code=409,
            detail=(
                f"{public_key} has {len(merchant.transactions)} transactions and cannot be deleted"
            ),
        )

    session.delete(merchant)
    session.flush()


@router.post("/merchants/{public_key}/rotate-key")
async def rotate_key(public_key: str, session: SessionDep) -> dict[str, Any]:
    """Issue a new private key. Existing signatures stop verifying."""
    merchant = merchant_service.rotate_private_key(_require_merchant(session, public_key))
    session.flush()
    return _serialise_merchant(session, merchant)


@router.patch("/merchants/{public_key}")
async def update_merchant(
    public_key: str, changes: MerchantInput, session: SessionDep
) -> dict[str, Any]:
    merchant = merchant_service.apply_changes(
        _require_merchant(session, public_key), changes.model_dump(exclude_unset=True)
    )
    session.flush()
    return _serialise_merchant(session, merchant)


MerchantFilter = Annotated[str | None, Query(alias="merchant", description="Scope to a public_key")]


def _merchant_id(session: Session, public_key: str | None) -> int | None:
    """Resolve a public_key to its row id. None means every merchant."""
    if not public_key:
        return None
    merchant = session.scalar(select(Merchant).where(Merchant.public_key == public_key))
    if merchant is None:
        raise HTTPException(status_code=404, detail=f"Unknown public_key: {public_key}")
    return merchant.id


@router.get("/transactions")
async def transactions(
    session: SessionDep,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    merchant: MerchantFilter = None,
) -> list[dict[str, Any]]:
    query = select(Transaction).order_by(Transaction.id.desc()).limit(limit)
    merchant_id = _merchant_id(session, merchant)
    if merchant_id is not None:
        query = query.where(Transaction.merchant_id == merchant_id)
    rows = session.scalars(query).all()
    return [
        {
            "transaction": t.transaction_id,
            "order_id": t.order_id,
            "status": t.status.value,
            "code": t.bank_code,
            "amount": float(t.amount),
            "currency": t.currency,
            "description": t.description,
            "card_mask": t.card_mask,
            "rrn": t.rrn,
            "endpoint": t.endpoint,
            "trace_id": t.trace_id,
            "created_at": t.created_at.isoformat(),
        }
        for t in rows
    ]


@router.get("/callbacks")
async def callbacks(
    session: SessionDep,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    merchant: MerchantFilter = None,
) -> list[dict[str, Any]]:
    query = select(Callback).order_by(Callback.id.desc()).limit(limit)
    merchant_id = _merchant_id(session, merchant)
    if merchant_id is not None:
        query = query.join(Transaction).where(Transaction.merchant_id == merchant_id)
    rows = session.scalars(query).all()
    return [
        {
            "id": c.id,
            "target_url": c.target_url,
            "attempt": c.attempt,
            "status": c.status.value,
            "data": c.payload_data,
            "signature": c.payload_signature,
            "decoded": c.decoded_payload,
            "response_status": c.response_status,
            "response_body": c.response_body,
            "error": c.error,
            "duration_ms": c.duration_ms,
            "created_at": c.created_at.isoformat(),
        }
        for c in rows
    ]


@router.get("/requests")
async def requests(
    session: SessionDep,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    merchant: MerchantFilter = None,
) -> list[dict[str, Any]]:
    query = select(RequestLog).order_by(RequestLog.id.desc()).limit(limit)
    merchant_id = _merchant_id(session, merchant)
    if merchant_id is not None:
        query = query.where(RequestLog.merchant_id == merchant_id)
    rows = session.scalars(query).all()
    return [
        {
            "trace_id": r.trace_id,
            "method": r.method,
            "path": r.path,
            "status_code": r.status_code,
            "duration_ms": r.duration_ms,
            "signature_valid": r.signature_valid,
            "request": r.request_payload,
            "response": r.response_payload,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]


@router.post("/signature/verify")
async def verify_signature(
    private_key: Annotated[str, Body()],
    data: Annotated[str, Body()],
    signature: Annotated[str | None, Body()] = None,
) -> dict[str, Any]:
    return signing.explain(private_key, data, signature)


@router.post("/signature/build")
async def build_signature(
    private_key: Annotated[str, Body()],
    payload: Annotated[dict[str, Any], Body()],
) -> dict[str, Any]:
    data = signing.encode_payload(payload)
    return {
        "data": data,
        "signature": signing.sign(private_key, data),
        "payload": payload,
    }


@router.get("/notifications")
async def notifications(
    session: SessionDep,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[dict[str, Any]]:
    """Captured invoice sends."""
    rows = session.scalars(select(Notification).order_by(Notification.id.desc()).limit(limit)).all()
    return [
        {
            "id": n.id,
            "invoice_id": n.invoice_id,
            "channel": n.channel,
            "recipient": n.recipient,
            "subject": n.subject,
            "body": n.body,
            "trace_id": n.trace_id,
            "created_at": n.created_at.isoformat(),
        }
        for n in rows
    ]


@router.get("/saved-cards")
async def saved_cards(
    session: SessionDep,
    merchant: MerchantFilter = None,
) -> list[dict[str, Any]]:
    query = select(Card).order_by(Card.id.desc())
    merchant_id = _merchant_id(session, merchant)
    if merchant_id is not None:
        query = query.where(Card.merchant_id == merchant_id)

    return [
        {
            "card_id": c.card_id,
            "mask": c.mask or None,
            "holder_name": c.holder_name,
            "expiry": c.expiry,
            "status": c.status.value,
            "is_payout_card": c.is_payout_card,
            "bank_code": c.bank_code,
            "description": c.description,
            "created_at": c.created_at.isoformat(),
        }
        for c in session.scalars(query).all()
    ]


@router.get("/invoices")
async def invoices_list(
    session: SessionDep,
    merchant: MerchantFilter = None,
) -> list[dict[str, Any]]:
    query = select(Invoice).order_by(Invoice.id.desc())
    merchant_id = _merchant_id(session, merchant)
    if merchant_id is not None:
        query = query.where(Invoice.merchant_id == merchant_id)

    return [
        {
            "id": i.id,
            "total": float(i.total),
            "status": i.status.value,
            "recipient_name": i.recipient_name,
            "description": i.description,
            "phone": i.phone,
            "email": i.email,
            "is_template": i.save_as_template,
            "allow_installment": i.allow_installment,
            "period_from": i.period_from.date().isoformat() if i.period_from else None,
            "period_to": i.period_to.date().isoformat() if i.period_to else None,
            "created_at": i.created_at.isoformat(),
        }
        for i in session.scalars(query).all()
    ]


@router.get("/balance")
async def balance_history(
    session: SessionDep,
    merchant: MerchantFilter = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[dict[str, Any]]:
    query = select(BalanceEntry).order_by(BalanceEntry.id.desc()).limit(limit)
    merchant_id = _merchant_id(session, merchant)
    if merchant_id is not None:
        query = query.where(BalanceEntry.merchant_id == merchant_id)

    return [
        {
            "id": e.id,
            "amount": float(e.amount),
            "balance_after": float(e.balance_after),
            "kind": e.kind,
            "description": e.description,
            "transaction_id": e.transaction_id,
            "created_at": e.created_at.isoformat(),
        }
        for e in session.scalars(query).all()
    ]


@router.get("/b2b")
async def b2b_list(
    session: SessionDep,
    merchant: MerchantFilter = None,
) -> list[dict[str, Any]]:
    query = select(B2BPayment).order_by(B2BPayment.id.desc())
    merchant_id = _merchant_id(session, merchant)
    if merchant_id is not None:
        query = query.where(B2BPayment.merchant_id == merchant_id)

    return [
        {
            "order_id": p.order_id,
            "status": p.status.value,
            "amount": float(p.amount),
            "payee_name": p.payee_name,
            "payee_iban": p.payee_iban,
            "bank_code": p.bank_code,
            "webhook_sent": p.webhook_sent,
            "bulk_id": p.bulk_id,
            "created_at": p.created_at.isoformat(),
        }
        for p in session.scalars(query).all()
    ]
