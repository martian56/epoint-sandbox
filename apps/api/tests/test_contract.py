"""Responses must stay within the documented field set."""

import pytest

from epoint_sandbox.api.contract import (
    DOCUMENTED_RESPONSE_FIELDS,
    SANCTIONED_EXTRAS,
    UNVERIFIED,
)
from epoint_sandbox.services import magic_cards
from tests.helpers import call, enable_features, pay_checkout, post_json, token_of


def allowed_for(path: str) -> set[str]:
    return set(DOCUMENTED_RESPONSE_FIELDS.get(path, set())) | set(
        SANCTIONED_EXTRAS.get(path, set())
    )


def assert_within_contract(path: str, body: dict) -> None:
    extra = set(body) - allowed_for(path)
    assert not extra, (
        f"{path} returned undocumented field(s) {sorted(extra)}. "
        "Either the docs list it and the contract needs regenerating, "
        "or the sandbox is inventing a field production will not send."
    )


PAYMENT = {"amount": "30.00", "currency": "AZN", "language": "en"}


@pytest.fixture(autouse=True)
def _granted(client, merchant):
    enable_features(client, merchant)


def test_create_payment_stays_within_contract(client, merchant):
    body = call(client, merchant, "/api/1/request", {**PAYMENT, "order_id": "c-1"})
    assert_within_contract("/api/1/request", body)


@pytest.mark.parametrize(
    "path",
    ["/api/1/payment-request", "/api/1/amex-request", "/api/1/payment-change-sum"],
)
def test_payment_family_stays_within_contract(client, merchant, path):
    body = call(client, merchant, path, {**PAYMENT, "order_id": f"c{path[-6:]}"})
    assert_within_contract(path, body)


def test_split_request_stays_within_contract(client, merchants):
    body = call(
        client,
        merchants[0],
        "/api/1/split-request",
        {
            **PAYMENT,
            "order_id": "c-split",
            "split_user": merchants[1].public_key,
            "split_amount": "10.00",
        },
    )
    assert_within_contract("/api/1/split-request", body)


def test_get_status_stays_within_contract(client, merchant):
    created = call(client, merchant, "/api/1/request", {**PAYMENT, "order_id": "c-status"})
    body = call(client, merchant, "/api/1/get-status", {"transaction": created["transaction"]})
    assert_within_contract("/api/1/get-status", body)


def test_card_registration_stays_within_contract(client, merchant):
    body = call(client, merchant, "/api/1/card-registration", {"language": "en"})
    assert_within_contract("/api/1/card-registration", body)


def test_card_status_stays_within_contract(client, merchant):
    created = call(client, merchant, "/api/1/card-registration", {"language": "en"})
    body = call(client, merchant, "/api/1/get-status-card", {"card_id": created["card_id"]})
    assert_within_contract("/api/1/get-status-card", body)


def test_execute_pay_stays_within_contract(client, merchant):
    registration = call(client, merchant, "/api/1/card-registration", {"language": "en"})
    pay_checkout(client, token_of(registration), magic_cards.SUCCESS_CARD)

    body = call(
        client,
        merchant,
        "/api/1/execute-pay",
        {**PAYMENT, "order_id": "c-saved", "card_id": registration["card_id"]},
    )
    assert_within_contract("/api/1/execute-pay", body)


def test_refund_stays_within_contract(client, merchant):
    seed = call(client, merchant, "/api/1/request", {**PAYMENT, "order_id": "c-seed"})
    pay_checkout(client, token_of(seed))

    registration = call(client, merchant, "/api/1/card-registration", {"language": "en"})
    pay_checkout(client, token_of(registration), magic_cards.SUCCESS_CARD)

    body = call(
        client,
        merchant,
        "/api/1/refund-request",
        {
            "language": "en",
            "card_id": registration["card_id"],
            "order_id": "c-refund",
            "amount": "5.00",
            "currency": "AZN",
        },
    )
    assert_within_contract("/api/1/refund-request", body)


def test_refund_no_longer_leaks_the_sandbox_mode_field(client, merchant):
    """sandbox_mode used to ship in the body."""
    seed = call(client, merchant, "/api/1/request", {**PAYMENT, "order_id": "c-seed2"})
    pay_checkout(client, token_of(seed))
    registration = call(client, merchant, "/api/1/card-registration", {"language": "en"})
    pay_checkout(client, token_of(registration), magic_cards.SUCCESS_CARD)

    response = client.post(
        "/api/1/refund-request",
        data=__import__("tests.helpers", fromlist=["signed_body"]).signed_body(
            merchant,
            {
                "language": "en",
                "card_id": registration["card_id"],
                "order_id": "c-refund2",
                "amount": "5.00",
                "currency": "AZN",
            },
        ),
    )

    assert "sandbox_mode" not in response.json()
    assert response.headers["X-Sandbox-Mode"] == "refund"


def test_reverse_stays_within_contract(client, merchant):
    seed = call(client, merchant, "/api/1/request", {**PAYMENT, "order_id": "c-rev"})
    pay_checkout(client, token_of(seed))

    body = call(
        client,
        merchant,
        "/api/1/reverse",
        {"language": "en", "transaction": seed["transaction"], "currency": "AZN"},
    )
    assert_within_contract("/api/1/reverse", body)


@pytest.mark.parametrize(
    ("path", "payload"),
    [
        (
            "/api/1/invoices/create",
            {
                "sum": "10.00",
                "display": 1,
                "save_as_template": 0,
                "period_from": "2026-01-01",
                "period_to": "2026-12-31",
            },
        ),
        ("/api/1/invoices/list", {}),
    ],
)
def test_invoice_endpoints_stay_within_contract(client, merchant, path, payload):
    body = call(client, merchant, path, payload)
    assert_within_contract(path, body)


def test_invoice_view_stays_within_contract(client, merchant):
    created = call(
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
    )
    body = call(client, merchant, "/api/1/invoices/view", {"id": created["id"]})
    assert_within_contract("/api/1/invoices/view", body)


def test_b2b_create_stays_within_contract(client, merchant):
    response = post_json(
        client,
        merchant,
        "/api/1/b2b/payment",
        {
            "order_id": "c-b2b",
            "amount": "100.00",
            "description": "contract check",
            "iban": "AZ29ABCD38053AZN00A7100186514",
            "name": "Contract LLC",
            "tin": "1234567891",
            "bank_code": "505141",
        },
    )
    assert_within_contract("/api/1/b2b/payment", response.json())


def test_every_documented_field_set_is_non_empty():
    for path, fields in DOCUMENTED_RESPONSE_FIELDS.items():
        assert fields, f"{path} has no documented response fields"


def test_sanctioned_extras_all_carry_a_reason():
    """Extras are only acceptable if the generator records why."""
    generator = (
        __import__("pathlib").Path(__file__).resolve().parents[3] / "scripts/extract_contracts.py"
    ).read_text(encoding="utf-8")

    for path in SANCTIONED_EXTRAS:
        assert path in generator, f"{path} is sanctioned but not explained in the generator"


def test_unverified_endpoints_are_declared():
    """Anything resting on docs alone must say so."""
    assert "/api/1/card-registration" in UNVERIFIED
    assert "/api/1/b2b/payment" in UNVERIFIED


def test_error_hints_never_ship_in_the_body(client, merchant):
    """The diagnosis is sandbox-only, so it travels as a header."""
    from epoint_sandbox import signing

    data = signing.encode_payload({"public_key": merchant.public_key, "amount": "1.00"})
    response = client.post("/api/1/request", data={"data": data, "signature": "wrong"})

    assert "sandbox_hint" not in response.json()
    assert response.headers["X-Sandbox-Hint"]


def test_error_bodies_carry_only_epoint_fields(client, merchant):
    from epoint_sandbox import signing

    data = signing.encode_payload({"public_key": merchant.public_key, "currency": "AZN"})
    signature = signing.sign(merchant.private_key, data)
    body = client.post("/api/1/request", data={"data": data, "signature": signature}).json()

    assert set(body) <= {"status", "message", "code", "trace_id"}
