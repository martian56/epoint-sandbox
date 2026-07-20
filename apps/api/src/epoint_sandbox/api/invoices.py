from datetime import datetime
from typing import Any

from fastapi import APIRouter, Request
from sqlalchemy import select

from epoint_sandbox.api.deps import SessionDep, SignedRequest, SignedRequestDep
from epoint_sandbox.api.errors import EpointError
from epoint_sandbox.models import Invoice, InvoiceStatus
from epoint_sandbox.services import notifications, payments

router = APIRouter(prefix="/api/1/invoices", tags=["invoices"])


def _trace(request: Request) -> str:
    return str(getattr(request.state, "trace_id", ""))


def _parse_date(value: Any, field: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value))
    except ValueError as exc:
        raise EpointError(f"{field} must be an ISO date, got {value}") from exc


def _flag(signed: SignedRequest, field: str, *, default: str = "0") -> bool:
    return str(signed.get(field, default)) == "1"


def _apply(invoice: Invoice, signed: SignedRequest) -> None:
    invoice.total = payments.parse_amount(signed.get("sum"), "sum")
    invoice.display = _flag(signed, "display", default="1")
    invoice.save_as_template = _flag(signed, "save_as_template")
    invoice.allow_installment = _flag(signed, "status_installment")
    invoice.recipient_name = signed.get("name")
    invoice.description = signed.get("description")
    invoice.phone = signed.get("phone")
    invoice.email = signed.get("email")
    invoice.tin = signed.get("inn")
    invoice.contract_number = signed.get("contract_number")
    invoice.merchant_order_id = signed.get("merchant_order_id")
    invoice.period_from = _parse_date(signed.get("period_from"), "period_from")
    invoice.period_to = _parse_date(signed.get("period_to"), "period_to")


def _load(session: SessionDep, signed: SignedRequestDep) -> Invoice:
    signed.require("id")
    invoice = session.get(Invoice, int(signed.get("id")))
    if invoice is None or invoice.merchant_id != signed.merchant.id:
        raise EpointError(f"Unknown invoice: {signed.get('id')}")
    return invoice


def _serialise(invoice: Invoice) -> dict[str, Any]:
    return {
        "id": invoice.id,
        "sum": float(invoice.total),
        "status": invoice.status.value,
        "name": invoice.recipient_name,
        "description": invoice.description,
        "phone": invoice.phone,
        "email": invoice.email,
        "inn": invoice.tin,
        "contract_number": invoice.contract_number,
        "merchant_order_id": invoice.merchant_order_id,
        "display": int(invoice.display),
        "save_as_template": int(invoice.save_as_template),
        "status_installment": int(invoice.allow_installment),
        "period_from": invoice.period_from.date().isoformat() if invoice.period_from else None,
        "period_to": invoice.period_to.date().isoformat() if invoice.period_to else None,
        "created_at": invoice.created_at.isoformat(),
    }


@router.post("/create")
async def create(request: Request, signed: SignedRequestDep, session: SessionDep) -> dict[str, Any]:
    signed.require("sum", "display", "save_as_template", "period_from", "period_to")

    invoice = Invoice(merchant_id=signed.merchant.id, total=0)
    _apply(invoice, signed)
    session.add(invoice)
    session.flush()

    return {"status": "success", "id": invoice.id, "message": "", "trace_id": _trace(request)}


@router.post("/update")
async def update(request: Request, signed: SignedRequestDep, session: SessionDep) -> dict[str, Any]:
    signed.require("sum", "display", "save_as_template", "period_from", "period_to")
    invoice = _load(session, signed)

    if invoice.status is not InvoiceStatus.WAITING:
        raise EpointError(f"Invoice {invoice.id} is {invoice.status.value} and cannot be changed")

    _apply(invoice, signed)
    session.flush()
    return {"status": "success", "message": "", "trace_id": _trace(request)}


@router.post("/view")
async def view(request: Request, signed: SignedRequestDep, session: SessionDep) -> dict[str, Any]:
    invoice = _load(session, signed)
    return {
        "status": "success",
        "invoice": _serialise(invoice),
        "message": "",
        "trace_id": _trace(request),
    }


@router.post("/list")
async def list_invoices(
    request: Request, signed: SignedRequestDep, session: SessionDep
) -> dict[str, Any]:
    query = select(Invoice).where(Invoice.merchant_id == signed.merchant.id)

    kind = signed.get("type")
    if kind == "static":
        query = query.where(Invoice.save_as_template.is_(True))
    elif kind in {"incoming", "sent"}:
        query = query.where(Invoice.save_as_template.is_(False))

    descending = str(signed.get("order", "desc")).lower() != "asc"
    query = query.order_by(Invoice.id.desc() if descending else Invoice.id.asc())

    rows = session.scalars(query).all()
    return {
        "status": "success",
        "invoices": [_serialise(i) for i in rows],
        "message": "",
        "trace_id": _trace(request),
    }


@router.post("/send-sms")
async def send_sms(
    request: Request, signed: SignedRequestDep, session: SessionDep
) -> dict[str, Any]:
    signed.require("phone")
    invoice = _load(session, signed)
    notifications.record(
        session,
        invoice,
        channel="sms",
        recipient=str(signed.get("phone")),
        trace_id=_trace(request),
    )
    return {"status": "success", "message": "", "trace_id": _trace(request)}


@router.post("/send-email")
async def send_email(
    request: Request, signed: SignedRequestDep, session: SessionDep
) -> dict[str, Any]:
    signed.require("email")
    invoice = _load(session, signed)
    notifications.record(
        session,
        invoice,
        channel="email",
        recipient=str(signed.get("email")),
        trace_id=_trace(request),
    )
    return {"status": "success", "message": "", "trace_id": _trace(request)}
