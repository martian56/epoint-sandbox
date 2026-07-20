import re

from tests.helpers import call, create_payment

NEW = {
    "name": "Acme Store",
    "tin": "1234567891",
    "contact_phone": "+994501112233",
    "site_url": "https://acme.az",
    "result_url": "https://acme.az/webhooks/epoint",
}


def create(client, **overrides):
    return client.post("/_sandbox/merchants", json={**NEW, **overrides})


def test_create_returns_201_with_a_key_pair(client):
    response = create(client)
    body = response.json()

    assert response.status_code == 201
    assert body["name"] == "Acme Store"
    assert body["public_key"]
    assert body["private_key"]


def test_generated_keys_match_the_production_formats(client):
    body = create(client).json()

    assert re.fullmatch(r"i\d{9}", body["public_key"])
    assert re.fullmatch(r"[A-Za-z0-9]{24}", body["private_key"])


def test_each_account_gets_a_distinct_key_pair(client):
    first = create(client, name="One").json()
    second = create(client, name="Two").json()

    assert first["public_key"] != second["public_key"]
    assert first["private_key"] != second["private_key"]


def test_a_new_account_can_immediately_sign_requests(client, session):
    from epoint_sandbox.models import Merchant

    body = create(client).json()
    merchant = session.scalar(
        Merchant.__table__.select().where(Merchant.public_key == body["public_key"])
    )
    assert merchant is not None

    # The signing helper only needs the key pair, so a lightweight stand-in is enough.
    class Signer:
        public_key = body["public_key"]
        private_key = body["private_key"]

    result = call(
        client,
        Signer,
        "/api/1/request",
        {"amount": "10.00", "currency": "AZN", "language": "en", "order_id": "first-order"},
    )
    assert result["status"] == "success"


def test_create_falls_back_to_a_placeholder_name(client):
    body = client.post("/_sandbox/merchants", json={}).json()
    assert body["name"] == "Untitled merchant"


def test_urls_can_be_updated(client, merchant):
    response = client.patch(
        f"/_sandbox/merchants/{merchant.public_key}",
        json={
            "site_url": "https://shop.example",
            "success_url": "https://shop.example/ok",
            "error_url": "https://shop.example/fail",
            "result_url": "https://shop.example/webhook",
        },
    )
    body = response.json()

    assert body["site_url"] == "https://shop.example"
    assert body["result_url"] == "https://shop.example/webhook"


def test_a_url_can_be_cleared(client, merchant):
    client.patch(f"/_sandbox/merchants/{merchant.public_key}", json={"result_url": "https://x.az"})
    body = client.patch(
        f"/_sandbox/merchants/{merchant.public_key}", json={"result_url": ""}
    ).json()

    assert body["result_url"] is None


def test_updating_one_field_leaves_the_others_alone(client, merchant):
    client.patch(f"/_sandbox/merchants/{merchant.public_key}", json={"site_url": "https://a.az"})
    body = client.patch(
        f"/_sandbox/merchants/{merchant.public_key}", json={"result_url": "https://b.az"}
    ).json()

    assert body["site_url"] == "https://a.az"
    assert body["result_url"] == "https://b.az"


def test_profile_fields_can_be_updated(client, merchant):
    body = client.patch(
        f"/_sandbox/merchants/{merchant.public_key}",
        json={"name": "Renamed", "tin": "9876543212", "contact_phone": "+994557778899"},
    ).json()

    assert body["name"] == "Renamed"
    assert body["tin"] == "9876543212"


def test_updating_an_unknown_merchant_is_404(client):
    assert client.patch("/_sandbox/merchants/i999999999", json={}).status_code == 404


def test_rotating_the_key_issues_a_new_one(client, merchant):
    before = merchant.private_key
    body = client.post(f"/_sandbox/merchants/{merchant.public_key}/rotate-key").json()

    assert body["private_key"] != before
    assert re.fullmatch(r"[A-Za-z0-9]{24}", body["private_key"])
    assert body["public_key"] == merchant.public_key


def test_the_old_key_stops_working_after_rotation(client, merchant):
    stale_private_key = merchant.private_key
    client.post(f"/_sandbox/merchants/{merchant.public_key}/rotate-key")

    class Stale:
        public_key = merchant.public_key
        private_key = stale_private_key

    result = call(
        client,
        Stale,
        "/api/1/request",
        {"amount": "5.00", "currency": "AZN", "language": "en", "order_id": "stale"},
    )
    assert "signature" in result["message"]


def test_an_account_can_be_deleted(client):
    body = create(client, name="Temporary").json()
    assert client.delete(f"/_sandbox/merchants/{body['public_key']}").status_code == 204

    remaining = {m["public_key"] for m in client.get("/_sandbox/merchants").json()}
    assert body["public_key"] not in remaining


def test_an_account_with_transactions_cannot_be_deleted(client, merchant):
    create_payment(client, merchant, "keeps-the-account-alive")
    response = client.delete(f"/_sandbox/merchants/{merchant.public_key}")

    assert response.status_code == 409
    assert "transactions" in response.json()["detail"]


def test_the_last_account_cannot_be_deleted(client, merchants):
    for m in merchants[1:]:
        client.delete(f"/_sandbox/merchants/{m.public_key}")

    remaining = client.get("/_sandbox/merchants").json()
    assert len(remaining) == 1

    response = client.delete(f"/_sandbox/merchants/{remaining[0]['public_key']}")
    assert response.status_code == 409
    assert "only merchant" in response.json()["detail"]


def test_deleting_an_unknown_merchant_is_404(client):
    assert client.delete("/_sandbox/merchants/i999999999").status_code == 404


def test_a_created_account_can_be_used_as_a_split_partner(client, merchant):
    partner = create(client, name="Marketplace Vendor").json()

    result = call(
        client,
        merchant,
        "/api/1/split-request",
        {
            "amount": "100.00",
            "currency": "AZN",
            "language": "en",
            "order_id": "split-to-new",
            "split_user": partner["public_key"],
            "split_amount": "25.00",
        },
    )
    assert result["status"] == "success"
