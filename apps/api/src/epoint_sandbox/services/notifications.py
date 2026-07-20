"""Invoice sends are recorded, never delivered."""

from sqlalchemy.orm import Session

from epoint_sandbox.config import get_settings
from epoint_sandbox.models import Invoice, Notification


def _body(invoice: Invoice) -> str:
    link = f"{get_settings().public_base_url}/invoice/{invoice.id}"
    name = invoice.recipient_name or "customer"
    return f"Hello {name}, you have an invoice for {invoice.total} AZN. Pay it here: {link}"


def record(
    session: Session,
    invoice: Invoice,
    *,
    channel: str,
    recipient: str,
    trace_id: str,
) -> Notification:
    notification = Notification(
        invoice_id=invoice.id,
        channel=channel,
        recipient=recipient,
        subject=f"Invoice #{invoice.id}" if channel == "email" else None,
        body=_body(invoice),
        trace_id=trace_id,
    )
    session.add(notification)
    session.flush()
    return notification
