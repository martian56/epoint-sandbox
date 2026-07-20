"""Refuse what production refuses.

A sandbox that accepts a payload production rejects is the dangerous direction: the
developer never learns their request is wrong until they switch over. Every field here
is marked Required on developer.epoint.az.
"""

import pytest

from epoint_sandbox.services import magic_cards
from tests.helpers import call, enable_features, pay_checkout, token_of


@pytest.fixture(autouse=True)
def _granted(client, merchant):
    enable_features(client, merchant)


@pytest.fixture
def active_card(client, merchant):
    body = call(client, merchant, "/api/1/card-registration", {"language": "en"})
    pay_checkout(client, token_of(body), magic_cards.SUCCESS_CARD)
    return body["card_id"]


@pytest.fixture
def settled(client, merchant):
    body = call(
        client,
        merchant,
        "/api/1/request",
        {"amount": "80.00", "currency": "AZN", "language": "en", "order_id": "req-seed"},
    )
    pay_checkout(client, token_of(body))
    return body["transaction"]


@pytest.fixture
def invoice(client, merchant):
    return call(
        client,
        merchant,
        "/api/1/invoices/create",
        {
            "sum": "10.00",
            "display": 1,
            "save_as_template": 0,
            "period_from": "2026-01-01",
            "period_to": "2026-12-31",
        },
    )["id"]


PAYMENT = {"amount": "10.00", "currency": "AZN", "language": "en"}

PAYMENT_FAMILY = [
    "/api/1/request",
    "/api/1/payment-request",
    "/api/1/amex-request",
    "/api/1/payment-change-sum",
    "/api/1/pre-auth-request",
]


def refused(body: dict, field: str) -> None:
    assert body.get("status") in ("error", "failed"), (
        f"accepted a payload with no {field!r}, which production documents as required. "
        "A developer would never learn their request is incomplete."
    )
    assert field in body.get("message", ""), f"the refusal does not name {field!r}"


@pytest.mark.parametrize("path", PAYMENT_FAMILY)
@pytest.mark.parametrize("field", ["amount", "currency", "language", "order_id"])
def test_payment_family_requires_its_documented_fields(client, merchant, path, field):
    payload = {**PAYMENT, "order_id": f"r{path[-6:]}{field}"}
    del payload[field]
    refused(call(client, merchant, path, payload), field)


@pytest.mark.parametrize(
    "field", ["amount", "currency", "language", "order_id", "split_user", "split_amount"]
)
def test_split_request_requires_its_documented_fields(client, merchants, field):
    payload = {
        **PAYMENT,
        "order_id": f"rsplit{field}",
        "split_user": merchants[1].public_key,
        "split_amount": "3.00",
    }
    del payload[field]
    refused(call(client, merchants[0], "/api/1/split-request", payload), field)


@pytest.mark.parametrize("field", ["language", "card_id", "order_id", "amount", "currency"])
def test_execute_pay_requires_its_documented_fields(client, merchant, active_card, field):
    payload = {
        "language": "en",
        "card_id": active_card,
        "order_id": f"rexec{field}",
        "amount": "5.00",
        "currency": "AZN",
    }
    del payload[field]
    refused(call(client, merchant, "/api/1/execute-pay", payload), field)


@pytest.mark.parametrize("field", ["language", "card_id", "order_id", "amount", "currency"])
def test_refund_request_requires_its_documented_fields(client, merchant, active_card, field):
    payload = {
        "language": "en",
        "card_id": active_card,
        "order_id": f"rrefund{field}",
        "amount": "1.00",
        "currency": "AZN",
    }
    del payload[field]
    refused(call(client, merchant, "/api/1/refund-request", payload), field)


@pytest.mark.parametrize("field", ["language", "transaction", "currency"])
def test_reverse_requires_its_documented_fields(client, merchant, settled, field):
    payload = {"language": "en", "transaction": settled, "currency": "AZN"}
    del payload[field]
    refused(call(client, merchant, "/api/1/reverse", payload), field)


@pytest.mark.parametrize("field", ["wallet_id", "amount", "currency", "order_id", "language"])
def test_wallet_payment_requires_its_documented_fields(client, merchant, field):
    payload = {**PAYMENT, "order_id": f"rwallet{field}", "wallet_id": "wallet_epul"}
    del payload[field]
    refused(call(client, merchant, "/api/1/wallet/payment", payload), field)


@pytest.mark.parametrize(
    "field", ["amount", "currency", "language", "order_id", "installment_card_id"]
)
def test_installment_request_requires_its_documented_fields(client, merchant, field):
    payload = {
        **PAYMENT,
        "order_id": f"rinst{field}",
        "installment_card_id": "1",
        "installment_month": 3,
    }
    del payload[field]
    refused(call(client, merchant, "/api/1/installment-request", payload), field)


@pytest.mark.parametrize("field", ["language", "order_id", "amount", "currency"])
def test_register_and_pay_requires_its_documented_fields(client, merchant, field):
    payload = {
        "language": "en",
        "order_id": f"rregpay{field}",
        "amount": "10.00",
        "currency": "AZN",
    }
    del payload[field]
    refused(call(client, merchant, "/api/1/card-registration-with-pay", payload), field)


@pytest.mark.parametrize(
    "field", ["sum", "display", "save_as_template", "period_from", "period_to"]
)
def test_invoice_create_requires_its_documented_fields(client, merchant, field):
    payload = {
        "sum": "10.00",
        "display": 1,
        "save_as_template": 0,
        "period_from": "2026-01-01",
        "period_to": "2026-12-31",
    }
    del payload[field]
    refused(call(client, merchant, "/api/1/invoices/create", payload), field)


@pytest.mark.parametrize("field", ["sum", "display", "save_as_template"])
def test_invoice_update_requires_its_documented_fields(client, merchant, invoice, field):
    payload = {
        "id": invoice,
        "sum": "12.00",
        "display": 1,
        "save_as_template": 0,
        "period_from": "2026-01-01",
        "period_to": "2026-12-31",
    }
    del payload[field]
    refused(call(client, merchant, "/api/1/invoices/update", payload), field)


def test_zero_is_a_value_not_an_omission(client, merchant):
    """display=0 and save_as_template=0 are meaningful, not missing."""
    body = call(
        client,
        merchant,
        "/api/1/invoices/create",
        {
            "sum": "10.00",
            "display": 0,
            "save_as_template": 0,
            "period_from": "2026-01-01",
            "period_to": "2026-12-31",
        },
    )
    assert body["status"] == "success"


def test_the_widget_does_not_require_language(client, merchant):
    """Its doc page lists only public_key, amount, order_id and description."""
    body = call(
        client,
        merchant,
        "/api/1/token/widget",
        {"amount": "10.00", "order_id": "rwidget", "description": "no language"},
    )
    assert body["status"] == "success"
