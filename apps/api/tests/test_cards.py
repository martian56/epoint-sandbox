import pytest

from epoint_sandbox.services import magic_cards
from tests.helpers import call, pay_checkout, token_of


def register_active_card(client, merchant, *, payout=False, card_number=None):
    """Register a card and confirm it at checkout."""
    body = call(
        client,
        merchant,
        "/api/1/card-registration",
        {"language": "en", "refund": 1 if payout else 0},
    )
    pay_checkout(client, token_of(body), card_number or magic_cards.SUCCESS_CARD)
    return body["card_id"]


def test_registration_returns_a_card_id_and_redirect(client, merchant):
    body = call(client, merchant, "/api/1/card-registration", {"language": "en"})

    assert body["status"] == "success"
    assert body["card_id"].startswith("ce")
    assert "/checkout/" in body["redirect_url"]


def test_card_is_pending_until_the_customer_confirms(client, merchant):
    body = call(client, merchant, "/api/1/card-registration", {"language": "en"})
    status = call(client, merchant, "/api/1/get-status-card", {"card_id": body["card_id"]})

    assert status["status"] == "new"


def test_card_becomes_active_after_a_successful_confirmation(client, merchant):
    card_id = register_active_card(client, merchant)
    status = call(client, merchant, "/api/1/get-status-card", {"card_id": card_id})

    assert status["status"] == "active"
    assert status["mask"] == "411111******1111"
    assert status["expired_date"] == "12/30"


def test_card_is_rejected_when_the_bank_declines(client, merchant):
    card_id = register_active_card(client, merchant, card_number="4000000000000116")
    status = call(client, merchant, "/api/1/get-status-card", {"card_id": card_id})

    assert status["status"] == "rejected"


def test_saved_card_can_be_charged(client, merchant):
    card_id = register_active_card(client, merchant)
    body = call(
        client,
        merchant,
        "/api/1/execute-pay",
        {
            "language": "en",
            "card_id": card_id,
            "order_id": "saved-1",
            "amount": "12.50",
            "currency": "AZN",
        },
    )

    assert body["status"] == "success"
    assert body["bank_response"] == "000"
    assert body["rrn"]
    assert body["card_mask"] == "411111******1111"


def test_charging_an_inactive_card_is_rejected(client, merchant):
    body = call(client, merchant, "/api/1/card-registration", {"language": "en"})
    result = call(
        client,
        merchant,
        "/api/1/execute-pay",
        {
            "language": "en",
            "card_id": body["card_id"],
            "order_id": "saved-2",
            "amount": "5.00",
            "currency": "AZN",
        },
    )

    assert "not active" in result["message"]


def test_charging_an_unknown_card_is_rejected(client, merchant):
    result = call(
        client,
        merchant,
        "/api/1/execute-pay",
        {
            "language": "en",
            "card_id": "ce99999999",
            "order_id": "saved-3",
            "amount": "5.00",
            "currency": "AZN",
        },
    )
    assert "Unknown card_id" in result["message"]


def test_register_and_pay_creates_both_in_one_step(client, merchant):
    body = call(
        client,
        merchant,
        "/api/1/card-registration-with-pay",
        {
            "language": "en",
            "order_id": "reg-and-pay",
            "amount": "30.00",
            "currency": "AZN",
        },
    )

    assert body["card_id"].startswith("ce")
    assert body["transaction"].startswith("te")

    pay_checkout(client, token_of(body), magic_cards.SUCCESS_CARD)
    status = call(client, merchant, "/api/1/get-status-card", {"card_id": body["card_id"]})
    assert status["status"] == "active"


def test_split_execute_pay_charges_and_splits(client, merchants):
    card_id = register_active_card(client, merchants[0])
    body = call(
        client,
        merchants[0],
        "/api/1/split-execute-pay",
        {
            "language": "en",
            "card_id": card_id,
            "order_id": "split-saved",
            "amount": "100.00",
            "currency": "AZN",
            "split_user": merchants[1].public_key,
            "split_amount": "30.00",
        },
    )

    assert body["status"] == "success"
    assert body["split_amount"] == 30.0


@pytest.mark.parametrize("field", ["card_id", "order_id", "amount"])
def test_execute_pay_reports_missing_fields(client, merchant, field):
    payload = {
        "language": "en",
        "card_id": "ce00000001",
        "order_id": "x",
        "amount": "1.00",
        "currency": "AZN",
    }
    del payload[field]

    result = call(client, merchant, "/api/1/execute-pay", payload)
    assert field in result["message"]
