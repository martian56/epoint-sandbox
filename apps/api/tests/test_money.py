from tests.helpers import call, settled_payment
from tests.test_cards import register_active_card


def balance(client, merchant) -> float:
    rows = client.get("/_sandbox/merchants").json()
    entry = next(m for m in rows if m["public_key"] == merchant.public_key)
    return entry["balance"]


def test_successful_payment_credits_the_merchant_less_commission(client, merchant):
    settled_payment(client, merchant, "ledger-1", "100.00")
    # 100 credited, 3% commission taken
    assert balance(client, merchant) == 97.0


def test_declined_payment_moves_no_money(client, merchant):
    from tests.helpers import create_payment, pay_checkout, token_of

    body = create_payment(client, merchant, "ledger-declined", "50.00")
    pay_checkout(client, token_of(body), "4000000000000116")

    assert balance(client, merchant) == 0.0


def test_split_payment_credits_both_merchants(client, merchants):
    from tests.helpers import pay_checkout, token_of

    body = call(
        client,
        merchants[0],
        "/api/1/split-request",
        {
            "amount": "100.00",
            "currency": "AZN",
            "language": "en",
            "order_id": "split-ledger",
            "split_user": merchants[1].public_key,
            "split_amount": "30.00",
        },
    )
    pay_checkout(client, token_of(body))

    # primary keeps 70 less 3% of 70, partner receives the 30
    assert balance(client, merchants[0]) == 67.9
    assert balance(client, merchants[1]) == 30.0


def test_refund_debits_the_balance(client, merchant):
    settled_payment(client, merchant, "refund-source", "100.00")
    card_id = register_active_card(client, merchant)

    body = call(
        client,
        merchant,
        "/api/1/refund-request",
        {
            "language": "en",
            "card_id": card_id,
            "order_id": "refund-1",
            "amount": "20.00",
            "currency": "AZN",
        },
    )

    assert body["status"] == "success"
    assert balance(client, merchant) == 77.0


def test_payout_card_routes_through_the_payout_mode(client, merchant):
    """The mode travels as a header, never in the body."""
    from tests.helpers import post

    settled_payment(client, merchant, "payout-source", "100.00")
    card_id = register_active_card(client, merchant, payout=True)

    response = post(
        client,
        merchant,
        "/api/1/refund-request",
        {
            "language": "en",
            "card_id": card_id,
            "order_id": "payout-1",
            "amount": "10.00",
            "currency": "AZN",
        },
    )

    assert response.headers["X-Sandbox-Mode"] == "payout"
    assert "sandbox_mode" not in response.json()


def test_refund_beyond_the_balance_is_rejected(client, merchant):
    card_id = register_active_card(client, merchant)

    body = call(
        client,
        merchant,
        "/api/1/refund-request",
        {
            "language": "en",
            "card_id": card_id,
            "order_id": "refund-too-big",
            "amount": "500.00",
            "currency": "AZN",
        },
    )

    assert "Insufficient balance" in body["message"]
    assert body["code"] == "116"


def test_reverse_returns_the_full_amount(client, merchant):
    body = settled_payment(client, merchant, "reverse-1", "40.00")

    result = call(
        client,
        merchant,
        "/api/1/reverse",
        {"language": "en", "transaction": body["transaction"], "currency": "AZN"},
    )

    assert result["status"] == "success"
    status = call(client, merchant, "/api/1/get-status", {"transaction": body["transaction"]})
    assert status["status"] == "returned"


def test_reverse_accepts_a_partial_amount(client, merchant):
    body = settled_payment(client, merchant, "reverse-partial", "100.00")

    call(
        client,
        merchant,
        "/api/1/reverse",
        {
            "language": "en",
            "transaction": body["transaction"],
            "amount": "25.00",
            "currency": "AZN",
        },
    )

    assert balance(client, merchant) == 72.0


def test_reverse_cannot_exceed_the_original(client, merchant):
    body = settled_payment(client, merchant, "reverse-too-big", "10.00")

    result = call(
        client,
        merchant,
        "/api/1/reverse",
        {
            "language": "en",
            "transaction": body["transaction"],
            "amount": "99.00",
            "currency": "AZN",
        },
    )

    assert "cannot exceed" in result["message"]


def test_only_successful_transactions_can_be_reversed(client, merchant):
    from tests.helpers import create_payment

    body = create_payment(client, merchant, "never-paid")
    result = call(
        client,
        merchant,
        "/api/1/reverse",
        {"language": "en", "transaction": body["transaction"], "currency": "AZN"},
    )

    assert "Only successful transactions" in result["message"]


def test_pre_auth_capture_settles_the_captured_amount(client, merchant):
    from tests.helpers import pay_checkout, token_of

    body = call(
        client,
        merchant,
        "/api/1/pre-auth-request",
        {"amount": "100.00", "currency": "AZN", "language": "en", "order_id": "hold-1"},
    )
    pay_checkout(client, token_of(body))

    result = call(
        client,
        merchant,
        "/api/1/pre-auth-complete",
        {"transaction": body["transaction"], "amount": "80.00"},
    )

    assert result["status"] == "success"
    assert balance(client, merchant) == 77.6


def test_capture_cannot_exceed_the_hold(client, merchant):
    from tests.helpers import pay_checkout, token_of

    body = call(
        client,
        merchant,
        "/api/1/pre-auth-request",
        {"amount": "50.00", "currency": "AZN", "language": "en", "order_id": "hold-2"},
    )
    pay_checkout(client, token_of(body))

    result = call(
        client,
        merchant,
        "/api/1/pre-auth-complete",
        {"transaction": body["transaction"], "amount": "90.00"},
    )

    assert "cannot exceed" in result["message"]
