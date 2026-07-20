import pytest

from epoint_sandbox import signing

ORDER = "order-1"


def post(client, merchant, path, payload):
    data = signing.encode_payload({"public_key": merchant.public_key, **payload})
    signature = signing.sign(merchant.private_key, data)
    return client.post(path, data={"data": data, "signature": signature})


def payment_payload(order_id=ORDER, **overrides):
    return {
        "amount": "30.75",
        "currency": "AZN",
        "language": "en",
        "order_id": order_id,
        "description": "test payment",
        **overrides,
    }


def test_heartbeat_is_unsigned_and_returns_trace_id(client):
    response = client.get("/api/heartbeat")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.headers["X-Request-ID"]


def test_create_payment_returns_redirect_url(client, merchant):
    response = post(client, merchant, "/api/1/request", payment_payload())
    body = response.json()

    assert body["status"] == "success"
    assert body["transaction"].startswith("te")
    assert "/checkout/" in body["redirect_url"]
    assert body["trace_id"]


def test_response_carries_request_id_header(client, merchant):
    response = post(client, merchant, "/api/1/request", payment_payload())
    assert response.headers["X-Request-ID"] == response.json()["trace_id"]


def test_bad_signature_is_rejected_with_a_hint(client, merchant):
    data = signing.encode_payload({"public_key": merchant.public_key, **payment_payload()})
    response = client.post("/api/1/request", data={"data": data, "signature": "wrong"})
    body = response.json()

    assert body["status"] == "error"
    assert "signature" in body["message"]


def test_unknown_public_key_is_forbidden(client):
    data = signing.encode_payload({"public_key": "i999999999", **payment_payload()})
    response = client.post("/api/1/request", data={"data": data, "signature": "x"})
    assert response.status_code == 403


def test_missing_required_field_is_reported(client, merchant):
    response = post(client, merchant, "/api/1/request", {"currency": "AZN", "order_id": "x"})
    assert "amount" in response.json()["message"]


def test_duplicate_order_id_is_rejected(client, merchant):
    post(client, merchant, "/api/1/request", payment_payload())
    response = post(client, merchant, "/api/1/request", payment_payload())
    assert "already been used" in response.json()["message"]


@pytest.mark.parametrize("currency", ["GBP", "JPY"])
def test_unsupported_currency_is_rejected(client, merchant, currency):
    response = post(client, merchant, "/api/1/request", payment_payload(currency=currency))
    assert "Unsupported currency" in response.json()["message"]


def test_split_request_rejects_unknown_partner(client, merchant):
    response = post(
        client,
        merchant,
        "/api/1/split-request",
        payment_payload(split_user="i000000009", split_amount="10"),
    )
    assert response.status_code == 403


def test_split_request_rejects_split_larger_than_total(client, merchants):
    response = post(
        client,
        merchants[0],
        "/api/1/split-request",
        payment_payload(amount="10", split_user=merchants[1].public_key, split_amount="50"),
    )
    assert "cannot exceed" in response.json()["message"]


def test_split_request_succeeds(client, merchants):
    response = post(
        client,
        merchants[0],
        "/api/1/split-request",
        payment_payload(amount="100", split_user=merchants[1].public_key, split_amount="30"),
    )
    assert response.json()["status"] == "success"


def test_get_status_returns_new_before_payment(client, merchant):
    created = post(client, merchant, "/api/1/request", payment_payload()).json()
    response = post(client, merchant, "/api/1/get-status", {"transaction": created["transaction"]})
    body = response.json()

    assert body["status"] == "new"
    assert body["amount"] == 30.75


def test_get_status_rejects_unknown_transaction(client, merchant):
    response = post(client, merchant, "/api/1/get-status", {"transaction": "te0000009999"})
    assert "Unknown transaction" in response.json()["message"]


def test_checkout_endpoint_redirects_to_payment_page(client, merchant):
    data = signing.encode_payload({"public_key": merchant.public_key, **payment_payload()})
    signature = signing.sign(merchant.private_key, data)
    response = client.post(
        "/api/1/checkout", data={"data": data, "signature": signature}, follow_redirects=False
    )

    assert response.status_code == 303
    assert "/checkout/" in response.headers["location"]


@pytest.mark.parametrize("path", ["/api/1/request", "/api/1/payment-request"])
def test_payment_family_shares_behaviour(client, merchant, path):
    response = post(client, merchant, path, payment_payload(order_id=f"order-{path[-4:]}"))
    assert response.json()["status"] == "success"


def test_transaction_ids_derive_from_the_database(client, merchant):
    """An in-process counter collided after a restart."""
    first = post(client, merchant, "/api/1/request", payment_payload(order_id="a")).json()
    second = post(client, merchant, "/api/1/request", payment_payload(order_id="b")).json()

    assert first["transaction"] == "te0000000001"
    assert second["transaction"] == "te0000000002"


def test_transaction_ids_stay_unique_across_many_payments(client, merchant):
    seen = {
        post(client, merchant, "/api/1/request", payment_payload(order_id=f"o{i}")).json()[
            "transaction"
        ]
        for i in range(25)
    }
    assert len(seen) == 25


def create_for(client, merchant, order_id):
    return post(client, merchant, "/api/1/request", payment_payload(order_id=order_id)).json()


def test_sandbox_transactions_default_to_every_merchant(client, merchants):
    create_for(client, merchants[0], "m1-order")
    create_for(client, merchants[1], "m2-order")

    rows = client.get("/_sandbox/transactions").json()
    assert {r["order_id"] for r in rows} == {"m1-order", "m2-order"}


def test_sandbox_transactions_can_scope_to_one_merchant(client, merchants):
    create_for(client, merchants[0], "m1-order")
    create_for(client, merchants[1], "m2-order")

    rows = client.get(f"/_sandbox/transactions?merchant={merchants[1].public_key}").json()
    assert [r["order_id"] for r in rows] == ["m2-order"]


def test_sandbox_requests_scope_to_one_merchant(client, merchants):
    create_for(client, merchants[0], "m1-order")
    create_for(client, merchants[1], "m2-order")

    rows = client.get(f"/_sandbox/requests?merchant={merchants[0].public_key}").json()
    assert rows
    assert all(r["request"]["public_key"] == merchants[0].public_key for r in rows)


def test_sandbox_rejects_an_unknown_merchant_filter(client):
    assert client.get("/_sandbox/transactions?merchant=i999999999").status_code == 404


def test_checkout_assets_are_served(client):
    for asset in ("tokens.css", "checkout.css", "logo.svg"):
        assert client.get(f"/checkout-assets/{asset}").status_code == 200, asset


def test_checkout_tokens_carry_the_measured_palette(client):
    css = client.get("/checkout-assets/tokens.css").text
    assert "--color-tint-200: #ffd8eb;" in css
    assert "--radius-card: 9px;" in css


def test_amex_is_refused_until_the_merchant_is_granted_it(client, merchant):
    """AMEX is granted per merchant, so it is refused by default."""
    response = post(client, merchant, "/api/1/amex-request", payment_payload(order_id="amex-1"))

    assert response.status_code == 403
    assert "not enabled" in response.json()["message"]


def test_amex_works_once_granted(client, merchant):
    from tests.helpers import enable_features

    enable_features(client, merchant, amex_enabled=True)
    response = post(client, merchant, "/api/1/amex-request", payment_payload(order_id="amex-2"))

    assert response.json()["status"] == "success"


def test_every_response_declares_it_came_from_the_sandbox(client, merchant):
    """Integrations assert on this."""
    for response in (
        client.get("/api/heartbeat"),
        post(client, merchant, "/api/1/request", payment_payload(order_id="hdr-1")),
    ):
        assert response.headers["X-Epoint-Sandbox"] == "1"
