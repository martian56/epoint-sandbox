import pytest

from epoint_sandbox.models import B2BPayment
from epoint_sandbox.services import callbacks, magic_cards
from tests.helpers import (
    call,
    create_payment,
    enable_features,
    pay_checkout,
    post_json,
    settled_payment,
    signed_body,
    token_of,
)
from tests.test_cards import register_active_card

PAYMENT = {"amount": "20.00", "currency": "AZN", "language": "en", "description": "x"}

INVOICE = {
    "sum": "150.00",
    "display": 1,
    "save_as_template": 0,
    "period_from": "2026-01-01",
    "period_to": "2026-12-31",
}


def balance(client, merchant) -> float:
    rows = client.get("/_sandbox/merchants").json()
    return next(m for m in rows if m["public_key"] == merchant.public_key)["balance"]


def status_of(client, merchant, transaction: str) -> dict:
    return call(client, merchant, "/api/1/get-status", {"transaction": transaction})


@pytest.mark.parametrize("path", ["/api/1/request", "/api/1/payment-request"])
@pytest.mark.parametrize("flag", [0, 1])
def test_is_installment_is_accepted_by_the_json_checkout_family(client, merchant, path, flag):
    body = call(
        client,
        merchant,
        path,
        {**PAYMENT, "order_id": f"inst{path[-7:]}{flag}", "is_installment": flag},
    )

    assert body["status"] == "success"
    assert "/checkout/" in body["redirect_url"]


@pytest.mark.parametrize("flag", [0, 1])
def test_is_installment_is_accepted_by_the_form_checkout(client, merchant, flag):
    payload = {**PAYMENT, "order_id": f"inst-form{flag}", "is_installment": flag}
    response = client.post(
        "/api/1/checkout", data=signed_body(merchant, payload), follow_redirects=False
    )

    assert response.status_code == 303
    assert "/checkout/" in response.headers["location"]


def test_installment_lookup_accepts_description_and_other_attr(client, merchant):
    enable_features(client, merchant, installments_enabled=True)
    body = call(
        client,
        merchant,
        "/api/1/get-installment-request",
        {
            "currency": "AZN",
            "language": "en",
            "order_id": "inst-lookup-extra",
            "amount": "600",
            "description": "Laptop",
            "other_attr": {"basket": "42"},
        },
    )

    assert isinstance(body, list)
    assert body
    assert all("installment_card_id" in c for c in body)


def test_b2b_payment_stores_bulk_description(client, merchant, session):
    enable_features(client, merchant, b2b_enabled=True)
    response = post_json(
        client,
        merchant,
        "/api/1/b2b/payment",
        {
            "order_id": "b2b-bulk",
            "amount": "100.00",
            "description": "Salary",
            "iban": "AZ21NABZ00000000137010001944",
            "name": "Payee LLC",
            "tin": "1234567892",
            "bank_code": "505000",
            "bulk_description": "October payroll",
        },
    )

    assert response.status_code == 200
    stored = session.query(B2BPayment).filter_by(order_id="b2b-bulk").one()
    assert stored.bulk_description == "October payroll"


def test_invoice_update_stores_inn_contract_number_and_merchant_order_id(client, merchant):
    created = call(client, merchant, "/api/1/invoices/create", INVOICE)
    updated = call(
        client,
        merchant,
        "/api/1/invoices/update",
        {
            **INVOICE,
            "id": created["id"],
            "inn": "1234567891",
            "contract_number": "C-2026-17",
            "merchant_order_id": "mo-77",
        },
    )
    view = call(client, merchant, "/api/1/invoices/view", {"id": created["id"]})

    assert updated["status"] == "success"
    assert view["invoice"]["inn"] == "1234567891"
    assert view["invoice"]["contract_number"] == "C-2026-17"
    assert view["invoice"]["merchant_order_id"] == "mo-77"


@pytest.mark.parametrize("action", ["create", "update"])
def test_invoice_images_as_multipart_files_do_not_break_the_request(client, merchant, action):
    payload = dict(INVOICE)
    if action == "update":
        payload["id"] = call(client, merchant, "/api/1/invoices/create", INVOICE)["id"]
    response = client.post(
        f"/api/1/invoices/{action}",
        data=signed_body(merchant, payload),
        files=[("invoice_images[]", ("logo.png", b"\x89PNG\r\n\x1a\n", "image/png"))],
    )

    assert response.json()["status"] == "success"


def test_error_card_ends_the_payment_in_status_error(client, merchant):
    body = create_payment(client, merchant, "status-error")
    pay_checkout(client, token_of(body), magic_cards.ERROR_CARD)
    status = status_of(client, merchant, body["transaction"])

    assert status["status"] == "error"
    assert status["message"] == magic_cards.ERROR_MESSAGE
    assert status["code"] == ""
    assert status["transaction"] == body["transaction"]


def test_error_card_sends_a_callback_and_moves_no_money(client, merchant, monkeypatch):
    delivered: list[str] = []
    monkeypatch.setattr(callbacks, "deliver", lambda s, t, **k: delivered.append(t.status.value))
    body = create_payment(client, merchant, "status-error-cb")
    pay_checkout(client, token_of(body), magic_cards.ERROR_CARD)

    assert delivered == ["error"]
    assert balance(client, merchant) == 0.0


def test_error_card_is_listed_with_the_test_cards(client):
    numbers = [c["number"] for c in client.get("/_sandbox/cards").json()["cards"]]
    assert magic_cards.ERROR_CARD in numbers


def test_timeout_card_ends_the_payment_in_status_server_error(client, merchant):
    body = create_payment(client, merchant, "status-server-error")
    pay_checkout(client, token_of(body), magic_cards.TIMEOUT_CARD)

    assert status_of(client, merchant, body["transaction"])["status"] == "server_error"


def test_reverse_ends_the_payment_in_status_returned(client, merchant):
    body = settled_payment(client, merchant, "status-returned")
    call(
        client,
        merchant,
        "/api/1/reverse",
        {"language": "en", "transaction": body["transaction"], "currency": "AZN"},
    )

    assert status_of(client, merchant, body["transaction"])["status"] == "returned"


def test_refund_request_records_a_returned_transaction(client, merchant):
    settled_payment(client, merchant, "refund-src", "100.00")
    card_id = register_active_card(client, merchant)
    refund = call(
        client,
        merchant,
        "/api/1/refund-request",
        {
            "language": "en",
            "card_id": card_id,
            "order_id": "refund-status",
            "amount": "10.00",
            "currency": "AZN",
        },
    )

    assert status_of(client, merchant, refund["transaction"])["status"] == "returned"
