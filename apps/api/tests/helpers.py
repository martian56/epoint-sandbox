"""Shared request helpers."""

from typing import Any

from epoint_sandbox import signing
from epoint_sandbox.services import magic_cards


def signed_body(merchant, payload: dict[str, Any]) -> dict[str, str]:
    data = signing.encode_payload({"public_key": merchant.public_key, **payload})
    return {"data": data, "signature": signing.sign(merchant.private_key, data)}


def post(client, merchant, path: str, payload: dict[str, Any]):
    return client.post(path, data=signed_body(merchant, payload))


def call(client, merchant, path: str, payload: dict[str, Any]) -> Any:
    """Post a signed request, return the decoded JSON."""
    return post(client, merchant, path, payload).json()


def post_json(client, merchant, path: str, payload: dict[str, Any]):
    """B2B takes the same pair as a JSON body."""
    return client.post(path, json=signed_body(merchant, payload))


def token_of(body: dict[str, Any]) -> str:
    return str(body["redirect_url"]).rsplit("/", 1)[-1]


def pay_checkout(client, token: str, card_number: str = magic_cards.SUCCESS_CARD):
    return client.post(
        f"/checkout/{token}",
        data={
            "card_number": card_number,
            "card_holder": "Sandbox Tester",
            "month": "12",
            "year": "30",
        },
        follow_redirects=False,
    )


def create_payment(client, merchant, order_id: str, amount: str = "100.00") -> dict[str, Any]:
    return call(
        client,
        merchant,
        "/api/1/request",
        {
            "amount": amount,
            "currency": "AZN",
            "language": "en",
            "order_id": order_id,
            "description": order_id,
        },
    )


def settled_payment(client, merchant, order_id: str, amount: str = "100.00") -> dict[str, Any]:
    """Create a payment and carry it through checkout."""
    body = create_payment(client, merchant, order_id, amount)
    pay_checkout(client, token_of(body))
    return body


ALL_FEATURES = {
    "amex_enabled": True,
    "token_payments_enabled": True,
    "installments_enabled": True,
    "wallets_enabled": True,
    "b2b_enabled": True,
}


def enable_features(client, merchant, **flags: bool):
    """Grant features so gated endpoints answer."""
    return client.patch(f"/_sandbox/merchants/{merchant.public_key}", json=flags or ALL_FEATURES)
