from epoint_sandbox import signing
from epoint_sandbox.services import magic_cards


def create_payment(client, merchant, **overrides):
    payload = {
        "public_key": merchant.public_key,
        "amount": "25.00",
        "currency": "AZN",
        "language": "az",
        "order_id": "checkout-order",
        **overrides,
    }
    data = signing.encode_payload(payload)
    signature = signing.sign(merchant.private_key, data)
    body = client.post("/api/1/request", data={"data": data, "signature": signature}).json()
    return body["redirect_url"].rsplit("/", 1)[-1], body["transaction"]


def status_of(client, merchant, transaction):
    data = signing.encode_payload({"public_key": merchant.public_key, "transaction": transaction})
    signature = signing.sign(merchant.private_key, data)
    return client.post("/api/1/get-status", data={"data": data, "signature": signature}).json()


def test_checkout_page_renders_amount_and_merchant(client, merchant):
    token, _ = create_payment(client, merchant)
    page = client.get(f"/checkout/{token}")

    assert page.status_code == 200
    assert "25.00" in page.text
    assert merchant.name in page.text


def test_unknown_token_is_404(client):
    assert client.get("/checkout/nope").status_code == 404


def test_success_card_marks_transaction_successful(client, merchant):
    token, transaction = create_payment(client, merchant)
    client.post(f"/checkout/{token}", data={"card_number": magic_cards.SUCCESS_CARD})

    body = status_of(client, merchant, transaction)
    assert body["status"] == "success"
    assert body["code"] == "000"
    assert body["rrn"]
    assert body["card_mask"] == "411111******1111"


def test_decline_card_sets_matching_bank_code(client, merchant):
    token, transaction = create_payment(client, merchant)
    client.post(f"/checkout/{token}", data={"card_number": "4000000000000116"})

    body = status_of(client, merchant, transaction)
    assert body["status"] == "failed"
    assert body["code"] == "116"
    assert body["rrn"] is None


def test_timeout_card_leaves_server_error(client, merchant):
    token, transaction = create_payment(client, merchant)
    client.post(f"/checkout/{token}", data={"card_number": magic_cards.TIMEOUT_CARD})

    assert status_of(client, merchant, transaction)["status"] == "server_error"


def test_short_card_number_is_rejected(client, merchant):
    token, transaction = create_payment(client, merchant)
    response = client.post(f"/checkout/{token}", data={"card_number": "4111"})

    assert response.status_code == 400
    assert status_of(client, merchant, transaction)["status"] == "new"


def test_paid_session_shows_result_instead_of_form(client, merchant):
    token, _ = create_payment(client, merchant)
    client.post(f"/checkout/{token}", data={"card_number": magic_cards.SUCCESS_CARD})

    page = client.get(f"/checkout/{token}")
    assert "success" in page.text
    assert 'name="card_number"' not in page.text


def test_success_redirect_url_is_followed(client, merchant):
    token, _ = create_payment(client, merchant, success_redirect_url="https://shop.example/thanks")
    response = client.post(
        f"/checkout/{token}",
        data={"card_number": magic_cards.SUCCESS_CARD},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "https://shop.example/thanks"


def test_checkout_language_switches_copy(client, merchant):
    token, _ = create_payment(client, merchant, language="en", order_id="en-order")
    assert "Payment details" in client.get(f"/checkout/{token}").text


def test_checkout_page_links_the_shared_token_stylesheet(client, merchant):
    token, _ = create_payment(client, merchant)
    page = client.get(f"/checkout/{token}")

    assert "/checkout-assets/tokens.css" in page.text
    assert "/checkout-assets/checkout.css" in page.text


def test_checkout_translates_the_test_card_disclosure(client, merchant):
    az_token, _ = create_payment(client, merchant, language="az", order_id="az-cards")
    en_token, _ = create_payment(client, merchant, language="en", order_id="en-cards")

    assert "Test kartları" in client.get(f"/checkout/{az_token}").text
    assert "Test cards" in client.get(f"/checkout/{en_token}").text
