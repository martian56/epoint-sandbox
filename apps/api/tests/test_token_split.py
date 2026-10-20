import pytest

from tests.helpers import call, enable_features, pay_checkout, post, token_of

PATH = "/api/1/token/split-payment"


def payload(partner, order_id="tsplit-1", **overrides):
    return {
        "amount": "100.00",
        "currency": "AZN",
        "language": "en",
        "order_id": order_id,
        "split_user": partner.public_key,
        "split_amount": "30.00",
        **overrides,
    }


def balance(client, merchant) -> float:
    rows = client.get("/_sandbox/merchants").json()
    return next(m for m in rows if m["public_key"] == merchant.public_key)["balance"]


@pytest.fixture
def granted(client, merchants):
    enable_features(client, merchants[0], token_payments_enabled=True)
    return merchants


def test_token_split_returns_the_split_request_shape(client, granted):
    body = call(client, granted[0], PATH, payload(granted[1]))

    assert body["status"] == "success"
    assert body["transaction"].startswith("te")
    assert "/checkout/" in body["redirect_url"]
    assert body["trace_id"]
    split = call(client, granted[0], "/api/1/split-request", payload(granted[1], "tsplit-twin"))
    assert set(body) == set(split)


def test_token_split_rejects_an_unknown_split_user(client, granted):
    response = post(client, granted[0], PATH, {**payload(granted[1]), "split_user": "i000000009"})

    assert response.status_code == 403
    assert "Unknown split_user" in response.json()["message"]


def test_token_split_rejects_a_split_larger_than_the_amount(client, granted):
    body = call(client, granted[0], PATH, payload(granted[1], amount="10", split_amount="50"))

    assert body["status"] == "error"
    assert "cannot exceed" in body["message"]


@pytest.mark.parametrize("currency", ["USD", "EUR", "RUB"])
def test_token_split_accepts_azn_only(client, granted, currency):
    body = call(client, granted[0], PATH, payload(granted[1], currency=currency))

    assert body["status"] == "error"
    assert "Unsupported currency" in body["message"]


@pytest.mark.parametrize(
    "field", ["amount", "currency", "language", "order_id", "split_user", "split_amount"]
)
def test_token_split_requires_its_documented_fields(client, granted, field):
    body = payload(granted[1], order_id=f"tsplit-{field}")
    del body[field]
    result = call(client, granted[0], PATH, body)

    assert result["status"] == "error"
    assert field in result["message"]


def test_token_split_is_off_until_token_payments_are_granted(client, merchants):
    response = post(client, merchants[0], PATH, payload(merchants[1]))
    widget = post(
        client,
        merchants[0],
        "/api/1/token/widget",
        {"amount": "10.00", "order_id": "tsplit-widget", "description": "gate"},
    )

    assert response.status_code == widget.status_code == 403
    assert response.json()["message"] == widget.json()["message"]
    assert set(response.json()) == set(widget.json())


def test_token_split_stores_its_endpoint(client, granted):
    call(client, granted[0], PATH, payload(granted[1]))
    rows = client.get(f"/_sandbox/transactions?merchant={granted[0].public_key}").json()

    assert any(r["endpoint"] == "token/split-payment" for r in rows)


def test_token_split_checkout_settles_and_splits_like_split_request(client, granted):
    body = call(client, granted[0], PATH, payload(granted[1]))
    pay_checkout(client, token_of(body))

    status = call(client, granted[0], "/api/1/get-status", {"transaction": body["transaction"]})
    assert status["status"] == "success"
    assert balance(client, granted[0]) == 67.9
    assert balance(client, granted[1]) == 30.0
