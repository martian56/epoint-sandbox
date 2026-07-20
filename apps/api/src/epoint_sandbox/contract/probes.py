"""Probe definitions for contract capture.

Tier A is read-only and free. Tier B moves real money.
"""

from dataclasses import dataclass, field
from typing import Any, Literal

Tier = Literal["A", "B"]


@dataclass(frozen=True)
class Probe:
    name: str
    path: str
    payload: dict[str, Any] = field(default_factory=dict)
    tier: Tier = "A"
    method: str = "POST"
    signed: bool = True
    json_body: bool = False
    # Corrupt the signature to record how it is refused.
    break_signature: Literal[False, "hex", "no_suffix", "no_key", "garbage"] = False
    note: str = ""


PROBES: tuple[Probe, ...] = (
    # Availability
    Probe(
        "heartbeat",
        "/api/heartbeat",
        method="GET",
        signed=False,
        note="No auth, confirms reachability and the trace_id shape",
    ),
    # Catalogues. Both are invented in the sandbox.
    Probe(
        "wallet_status",
        "/api/1/wallet/status",
        note="Real wallet catalogue; the sandbox list is invented",
    ),
    Probe(
        "installments_catalogue",
        "/api/1/get-installment-request",
        {"currency": "AZN", "language": "en", "order_id": "probe-installments"},
        note="Real installment cards and months; the sandbox list is invented",
    ),
    # Lookups for things that do not exist.
    Probe(
        "status_unknown_transaction",
        "/api/1/get-status",
        {"transaction": "te0000000000"},
        note="Does an unknown id return 200-with-body or a real status code?",
    ),
    Probe("status_unknown_card", "/api/1/get-status-card", {"card_id": "ce00000000"}),
    # Validation.
    Probe(
        "missing_amount",
        "/api/1/request",
        {"currency": "AZN", "language": "en", "order_id": "probe-missing-amount"},
    ),
    Probe(
        "missing_order_id",
        "/api/1/request",
        {"amount": "1.00", "currency": "AZN", "language": "en"},
    ),
    Probe(
        "unsupported_currency",
        "/api/1/request",
        {"amount": "1.00", "currency": "GBP", "language": "en", "order_id": "probe-currency"},
    ),
    Probe(
        "negative_amount",
        "/api/1/request",
        {"amount": "-5.00", "currency": "AZN", "language": "en", "order_id": "probe-negative"},
    ),
    Probe(
        "zero_amount",
        "/api/1/request",
        {"amount": "0", "currency": "AZN", "language": "en", "order_id": "probe-zero"},
    ),
    Probe(
        "oversized_order_id",
        "/api/1/request",
        {"amount": "1.00", "currency": "AZN", "language": "en", "order_id": "x" * 300},
        note="Docs cap order_id at 255; is it enforced?",
    ),
    Probe(
        "unknown_split_user",
        "/api/1/split-request",
        {
            "amount": "10.00",
            "currency": "AZN",
            "language": "en",
            "order_id": "probe-split",
            "split_user": "i999999999",
            "split_amount": "1.00",
        },
    ),
    Probe(
        "bad_language",
        "/api/1/request",
        {"amount": "1.00", "currency": "AZN", "language": "zz", "order_id": "probe-lang"},
        note="Is language validated at all?",
    ),
    # Signature handling.
    Probe(
        "signature_hex_digest",
        "/api/1/request",
        {"amount": "1.00", "currency": "AZN", "language": "en", "order_id": "probe-sig-hex"},
        break_signature="hex",
    ),
    Probe(
        "signature_missing_suffix_key",
        "/api/1/request",
        {"amount": "1.00", "currency": "AZN", "language": "en", "order_id": "probe-sig-suffix"},
        break_signature="no_suffix",
    ),
    Probe(
        "signature_no_key",
        "/api/1/request",
        {"amount": "1.00", "currency": "AZN", "language": "en", "order_id": "probe-sig-nokey"},
        break_signature="no_key",
    ),
    Probe(
        "signature_garbage",
        "/api/1/request",
        {"amount": "1.00", "currency": "AZN", "language": "en", "order_id": "probe-sig-junk"},
        break_signature="garbage",
    ),
    # Tier B. Real money.
    Probe(
        "create_minimal_payment",
        "/api/1/request",
        {
            "amount": "0.01",
            "currency": "AZN",
            "language": "en",
            "order_id": "probe-live-payment",
            "description": "contract probe",
        },
        tier="B",
        note="Settles redirect_url shape and the real transaction id format",
    ),
    Probe(
        "card_registration",
        "/api/1/card-registration",
        {"language": "en"},
        tier="B",
        note="Settles whether redirect_url is returned; the docs omit it",
    ),
)


def by_tier(tier: Tier) -> tuple[Probe, ...]:
    return tuple(p for p in PROBES if p.tier == tier)
