"""A created resource must be committed before its id reaches the client.

The session commits in the dependency teardown, which FastAPI runs after the
response is sent. So anything a handler hands back and the client reads at once,
a checkout token or an order id, has to be committed inside the handler instead.
Otherwise a fast client beats the commit and gets a 404.
"""

from epoint_sandbox.api.deps import SignedRequest
from epoint_sandbox.services import payments


def signed(merchant, **payload):
    return SignedRequest(merchant=merchant, payload=payload, raw_data="", raw_signature="")


def count_commits(session):
    calls = {"n": 0}
    original = session.commit

    def spy():
        calls["n"] += 1
        return original()

    session.commit = spy
    return calls


def test_create_transaction_commits_before_returning(session, merchant):
    calls = count_commits(session)
    payments.create_transaction(
        session,
        signed(merchant, amount="10.00", currency="AZN", language="en", order_id="commit-1"),
        endpoint="request",
        trace_id="t",
    )
    assert calls["n"] == 1


def test_create_transaction_defers_commit_for_same_request_charges(session, merchant):
    calls = count_commits(session)
    payments.create_transaction(
        session,
        signed(merchant, amount="10.00", currency="AZN", language="en", order_id="commit-2"),
        endpoint="execute-pay",
        trace_id="t",
        commit=False,
    )
    assert calls["n"] == 0


def test_the_checkout_token_is_queryable_right_after_creation(client, merchant):
    """End to end: create, then read the checkout page with no delay."""
    from tests.helpers import call, token_of

    body = call(
        client,
        merchant,
        "/api/1/request",
        {"amount": "10.00", "currency": "AZN", "language": "en", "order_id": "commit-3"},
    )
    assert client.get(f"/checkout/{token_of(body)}").status_code == 200


def test_a_bank_transfer_is_readable_right_after_creation(client, merchant):
    from tests.helpers import enable_features, post_json

    enable_features(client, merchant, b2b_enabled=True)
    post_json(
        client,
        merchant,
        "/api/1/b2b/payment",
        {
            "order_id": "commit-b2b",
            "amount": "100.00",
            "description": "x",
            "iban": "AZ21NABZ00000000137010001944",
            "name": "N",
            "tin": "1234567892",
            "bank_code": "505141",
        },
    )
    assert client.get("/api/1/b2b/payment/commit-b2b").status_code == 200


def test_an_invoice_is_readable_right_after_creation(client, merchant):
    from tests.helpers import call

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
    viewed = call(client, merchant, "/api/1/invoices/view", {"id": created["id"]})
    assert viewed["status"] == "success"
