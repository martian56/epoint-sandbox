from tests.helpers import call

BASE = {
    "sum": "150.00",
    "display": 1,
    "save_as_template": 0,
    "name": "John Doe",
    "description": "Service payment",
    "period_from": "2026-01-01",
    "period_to": "2026-12-31",
}


def create(client, merchant, **overrides):
    return call(client, merchant, "/api/1/invoices/create", {**BASE, **overrides})


def test_create_returns_an_id(client, merchant):
    body = create(client, merchant)

    assert body["status"] == "success"
    assert isinstance(body["id"], int)


def test_created_invoice_starts_waiting_for_payment(client, merchant):
    created = create(client, merchant)
    body = call(client, merchant, "/api/1/invoices/view", {"id": created["id"]})

    assert body["invoice"]["status"] == "waiting_for_payment"
    assert body["invoice"]["sum"] == 150.0
    assert body["invoice"]["name"] == "John Doe"


def test_create_requires_the_period(client, merchant):
    payload = {k: v for k, v in BASE.items() if k != "period_from"}
    body = call(client, merchant, "/api/1/invoices/create", payload)

    assert "period_from" in body["message"]


def test_create_rejects_a_malformed_date(client, merchant):
    body = create(client, merchant, period_from="not-a-date")
    assert "ISO date" in body["message"]


def test_update_changes_the_amount(client, merchant):
    created = create(client, merchant)
    call(client, merchant, "/api/1/invoices/update", {**BASE, "id": created["id"], "sum": "220.00"})

    body = call(client, merchant, "/api/1/invoices/view", {"id": created["id"]})
    assert body["invoice"]["sum"] == 220.0


def test_view_rejects_another_merchants_invoice(client, merchants):
    created = create(client, merchants[0])
    body = call(client, merchants[1], "/api/1/invoices/view", {"id": created["id"]})

    assert "Unknown invoice" in body["message"]


def test_list_returns_newest_first(client, merchant):
    create(client, merchant, name="first")
    create(client, merchant, name="second")

    body = call(client, merchant, "/api/1/invoices/list", {})
    assert [i["name"] for i in body["invoices"]] == ["second", "first"]


def test_list_can_sort_ascending(client, merchant):
    create(client, merchant, name="first")
    create(client, merchant, name="second")

    body = call(client, merchant, "/api/1/invoices/list", {"order": "asc"})
    assert [i["name"] for i in body["invoices"]] == ["first", "second"]


def test_list_filters_templates(client, merchant):
    create(client, merchant, name="normal", save_as_template=0)
    create(client, merchant, name="template", save_as_template=1)

    body = call(client, merchant, "/api/1/invoices/list", {"type": "static"})
    assert [i["name"] for i in body["invoices"]] == ["template"]


def test_list_is_scoped_to_the_merchant(client, merchants):
    create(client, merchants[0], name="mine")
    body = call(client, merchants[1], "/api/1/invoices/list", {})

    assert body["invoices"] == []


def test_send_sms_is_captured_not_delivered(client, merchant):
    created = create(client, merchant)
    body = call(
        client,
        merchant,
        "/api/1/invoices/send-sms",
        {"id": created["id"], "phone": "+994501234567"},
    )

    assert body["status"] == "success"

    sent = client.get("/_sandbox/notifications").json()
    assert sent[0]["channel"] == "sms"
    assert sent[0]["recipient"] == "+994501234567"
    assert "150" in sent[0]["body"]


def test_send_email_is_captured_with_a_subject(client, merchant):
    created = create(client, merchant)
    call(
        client,
        merchant,
        "/api/1/invoices/send-email",
        {"id": created["id"], "email": "buyer@example.com"},
    )

    sent = client.get("/_sandbox/notifications").json()
    assert sent[0]["channel"] == "email"
    assert sent[0]["subject"] == f"Invoice #{created['id']}"


def test_send_requires_a_recipient(client, merchant):
    created = create(client, merchant)
    body = call(client, merchant, "/api/1/invoices/send-sms", {"id": created["id"]})

    assert "phone" in body["message"]
