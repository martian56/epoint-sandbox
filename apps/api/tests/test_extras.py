import pytest

from tests.helpers import call, enable_features, post_json

PAYMENT = {"amount": "600.00", "currency": "AZN", "language": "en"}


@pytest.fixture(autouse=True)
def _granted(client, merchant):
    """Gated in production, so grant them first."""
    enable_features(client, merchant)


def test_installment_catalogue_lists_cards_and_months(client, merchant):
    body = call(
        client,
        merchant,
        "/api/1/get-installment-request",
        {"currency": "AZN", "language": "en", "order_id": "inst-lookup"},
    )

    assert len(body) >= 2
    assert all("installment_card_id" in c and c["installment_months"] for c in body)


def test_installment_payment_returns_a_redirect(client, merchant):
    body = call(
        client,
        merchant,
        "/api/1/installment-request",
        {**PAYMENT, "order_id": "inst-1", "installment_card_id": "1", "installment_month": 6},
    )

    assert body["status"] == "success"
    assert "/checkout/" in body["redirect_url"]


def test_installment_rejects_an_unknown_card(client, merchant):
    body = call(
        client,
        merchant,
        "/api/1/installment-request",
        {**PAYMENT, "order_id": "inst-2", "installment_card_id": "99", "installment_month": 6},
    )
    assert "Unknown installment_card_id" in body["message"]


def test_installment_rejects_an_unsupported_month(client, merchant):
    body = call(
        client,
        merchant,
        "/api/1/installment-request",
        {**PAYMENT, "order_id": "inst-3", "installment_card_id": "1", "installment_month": 7},
    )
    assert "does not offer 7 months" in body["message"]


def test_wallet_status_returns_the_catalogue(client, merchant):
    body = call(client, merchant, "/api/1/wallet/status", {})

    assert isinstance(body, dict)
    assert all(isinstance(name, str) for name in body.values())


def test_wallet_payment_returns_a_redirect(client, merchant):
    wallets = call(client, merchant, "/api/1/wallet/status", {})
    wallet_id = next(iter(wallets))

    body = call(
        client,
        merchant,
        "/api/1/wallet/payment",
        {**PAYMENT, "order_id": "wallet-1", "wallet_id": wallet_id},
    )

    assert body["status"] == "success"
    assert "/checkout/" in body["redirect_url"]


def test_wallet_payment_rejects_an_unknown_wallet(client, merchant):
    body = call(
        client,
        merchant,
        "/api/1/wallet/payment",
        {**PAYMENT, "order_id": "wallet-2", "wallet_id": "nope"},
    )
    assert "Unknown wallet_id" in body["message"]


def test_token_widget_returns_a_widget_url(client, merchant):
    body = call(
        client,
        merchant,
        "/api/1/token/widget",
        {"amount": "2.50", "order_id": "widget-1", "description": "Digital wallet payment"},
    )

    assert body["status"] == "success"
    assert "widget=1" in body["widget_url"]


def test_token_widget_requires_a_description(client, merchant):
    body = call(client, merchant, "/api/1/token/widget", {"amount": "2.50", "order_id": "widget-2"})
    assert "description" in body["message"]


B2B = {
    "order_id": "b2b-1",
    "amount": "1000.00",
    "description": "Advance payment",
    "iban": "AZ29ABCD38053AZN00A7100186514",
    "name": "Technology LLC",
    "tin": "1234567891",
    "bank_code": "505141",
}


def test_b2b_payment_accepts_a_json_body(client, merchant):
    response = post_json(client, merchant, "/api/1/b2b/payment", B2B)
    body = response.json()

    assert response.status_code == 200
    assert body["status"] == "success"
    assert body["bulkId"]


def test_b2b_payment_starts_pending(client, merchant):
    post_json(client, merchant, "/api/1/b2b/payment", B2B)
    body = client.get("/api/1/b2b/payment/b2b-1").json()

    assert body["status"] == "PENDING"
    assert body["payee_iban"] == B2B["iban"]


def test_b2b_advances_through_its_lifecycle(client, merchant):
    post_json(client, merchant, "/api/1/b2b/payment", B2B)

    client.post("/api/1/b2b/payment/b2b-1/advance")
    assert client.get("/api/1/b2b/payment/b2b-1").json()["status"] == "PROCESSING"

    client.post("/api/1/b2b/payment/b2b-1/advance")
    assert client.get("/api/1/b2b/payment/b2b-1").json()["status"] == "SUCCESS"


def test_b2b_cannot_advance_past_a_terminal_status(client, merchant):
    post_json(client, merchant, "/api/1/b2b/payment", B2B)
    client.post("/api/1/b2b/payment/b2b-1/advance")
    client.post("/api/1/b2b/payment/b2b-1/advance")

    assert client.post("/api/1/b2b/payment/b2b-1/advance").status_code == 409


@pytest.mark.parametrize(
    ("field", "value", "fragment"),
    [
        ("iban", "GB29ABCD38053", "must start with AZ"),
        ("tin", "123", "10 digits"),
        ("tin", "1234567893", "10 digits"),
        ("amount", "50000", "between"),
        ("amount", "0", "greater than zero"),
    ],
)
def test_b2b_validation_rejects_bad_input(client, merchant, field, value, fragment):
    response = post_json(client, merchant, "/api/1/b2b/payment", {**B2B, field: value})

    assert response.status_code == 422
    assert fragment in response.json()["detail"]


def test_b2b_rejects_a_duplicate_order_id(client, merchant):
    post_json(client, merchant, "/api/1/b2b/payment", B2B)
    response = post_json(client, merchant, "/api/1/b2b/payment", B2B)

    assert response.status_code == 422
    assert "already been used" in response.json()["detail"]


def test_b2b_status_404s_for_an_unknown_order(client):
    assert client.get("/api/1/b2b/payment/nope").status_code == 404


def test_sandbox_routes_do_not_collide(client):
    """A saved-cards route once shadowed the catalogue at /_sandbox/cards."""
    catalogue = client.get("/_sandbox/cards").json()
    saved = client.get("/_sandbox/saved-cards").json()

    assert isinstance(catalogue, dict)
    assert "cards" in catalogue
    assert isinstance(saved, list)


def test_every_sandbox_list_endpoint_returns_an_array(client):
    for path in (
        "/transactions",
        "/callbacks",
        "/requests",
        "/saved-cards",
        "/invoices",
        "/balance",
        "/notifications",
        "/b2b",
        "/merchants",
    ):
        body = client.get(f"/_sandbox{path}").json()
        assert isinstance(body, list), f"{path} returned {type(body).__name__}"
