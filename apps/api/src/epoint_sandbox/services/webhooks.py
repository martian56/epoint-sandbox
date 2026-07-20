"""B2B webhooks. Plain JSON, with their own retry schedule."""

import time
from typing import Any

import httpx
from sqlalchemy.orm import Session

from epoint_sandbox.config import get_settings
from epoint_sandbox.models import B2BPayment, B2BStatus
from epoint_sandbox.services.callbacks import explain_failure

RETRY_BACKOFF_SECONDS = (60, 120, 180, 240)


def build_payload(payment: B2BPayment) -> dict[str, Any]:
    return {
        "order_id": payment.order_id,
        "status": "success" if payment.status is B2BStatus.SUCCESS else "failed",
        "amount": str(payment.amount),
        "payee_iban": payment.payee_iban,
        "payee_name": payment.payee_name,
        "error_message": payment.error_message,
    }


def deliver_b2b(session: Session, payment: B2BPayment) -> bool:
    if not payment.webhook_url:
        return False

    payload = build_payload(payment)
    started = time.perf_counter()
    try:
        response = httpx.post(
            payment.webhook_url,
            json=payload,
            timeout=get_settings().callback_timeout_seconds,
        )
        payment.webhook_sent = response.is_success
        if not response.is_success:
            payment.error_message = f"Webhook returned {response.status_code}"
    except httpx.HTTPError as exc:
        payment.webhook_sent = False
        payment.error_message = explain_failure(payment.webhook_url, exc)

    session.flush()
    _ = time.perf_counter() - started
    return payment.webhook_sent
