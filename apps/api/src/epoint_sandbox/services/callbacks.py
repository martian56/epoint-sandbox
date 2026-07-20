import time
from datetime import UTC, datetime
from typing import Any

import httpx
from sqlalchemy.orm import Session

from epoint_sandbox import signing
from epoint_sandbox.config import get_settings
from epoint_sandbox.models import Callback, CallbackStatus, Transaction

LOCALHOST_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0"}


def build_payload(transaction: Transaction) -> dict[str, Any]:
    return {
        "order_id": transaction.order_id,
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
        "trace_id": transaction.trace_id,
    }


def deliver(session: Session, transaction: Transaction, *, attempt: int = 1) -> Callback | None:
    target = transaction.merchant.result_url
    if not target:
        return None

    payload = build_payload(transaction)
    data = signing.encode_payload(payload)
    signature = signing.sign(transaction.merchant.private_key, data)

    record = Callback(
        transaction_id=transaction.id,
        target_url=target,
        attempt=attempt,
        payload_data=data,
        payload_signature=signature,
        decoded_payload=payload,
    )

    started = time.perf_counter()
    try:
        response = httpx.post(
            target,
            data={"data": data, "signature": signature},
            timeout=get_settings().callback_timeout_seconds,
            follow_redirects=False,
        )
        record.response_status = response.status_code
        record.response_body = response.text[:4000]
        record.status = CallbackStatus.DELIVERED if response.is_success else CallbackStatus.FAILED
        if response.is_success:
            record.delivered_at = datetime.now(UTC)
    except httpx.HTTPError as exc:
        record.status = CallbackStatus.FAILED
        record.error = explain_failure(target, exc)

    record.duration_ms = int((time.perf_counter() - started) * 1000)
    session.add(record)
    session.flush()
    return record


def explain_failure(target: str, exc: httpx.HTTPError) -> str:
    """Name the container-to-host mistake rather than surfacing a bare error."""
    host = httpx.URL(target).host
    if host in LOCALHOST_HOSTS:
        return (
            f"{exc}\n\nThe sandbox runs inside a container, so {host} points at the container "
            "itself rather than your machine. Use http://host.docker.internal instead. "
            "On Linux add --add-host=host.docker.internal:host-gateway to your docker run."
        )
    return str(exc)
