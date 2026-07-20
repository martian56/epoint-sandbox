import json
import re

from epoint_sandbox.services import magic_cards
from tests.helpers import call, enable_features

DECLINE_CARD = "4000000000000116"


def widget(client, merchant, order_id="widget-1", amount="25.00"):
    enable_features(client, merchant, token_payments_enabled=True)
    return call(
        client,
        merchant,
        "/api/1/token/widget",
        {"amount": amount, "order_id": order_id, "description": "Widget payment"},
    )


def token_of(widget_url: str) -> str:
    return widget_url.split("/checkout/")[1].split("?")[0]


def path_of(widget_url: str) -> str:
    return widget_url.split("8181", 1)[-1]


def settle(client, widget_url: str, wallet="Apple Pay", card=magic_cards.SUCCESS_CARD):
    return client.post(
        f"/checkout/{token_of(widget_url)}/widget",
        data={"wallet": wallet, "card_number": card},
        follow_redirects=False,
    )


def payload_of(html: str) -> dict:
    match = re.search(r'<script id="payload" type="application/json">(.*?)</script>', html, re.S)
    assert match, "the settled page carries no payload for the parent"
    return json.loads(match.group(1))


def test_widget_url_points_at_the_embeddable_view(client, merchant):
    body = widget(client, merchant)

    assert body["status"] == "success"
    assert "widget=1" in body["widget_url"]
    assert body["transaction"].startswith("te")


def test_widget_view_offers_both_wallets(client, merchant):
    page = client.get(path_of(widget(client, merchant)["widget_url"])).text

    assert "Apple Pay" in page
    assert "Google Pay" in page


def test_widget_view_is_not_the_card_form(client, merchant):
    """Serving the card form here was the original bug."""
    url = widget(client, merchant)["widget_url"]

    assert 'name="card_holder"' not in client.get(path_of(url)).text
    assert 'name="card_holder"' in client.get(f"/checkout/{token_of(url)}").text


def test_paying_with_a_wallet_settles_the_transaction(client, merchant):
    body = widget(client, merchant)
    assert settle(client, body["widget_url"]).status_code == 200

    status = call(client, merchant, "/api/1/get-status", {"transaction": body["transaction"]})
    assert status["status"] == "success"
    assert status["code"] == "000"


def test_the_result_is_posted_to_the_parent_page(client, merchant):
    body = widget(client, merchant)
    html = settle(client, body["widget_url"], wallet="Google Pay").text

    assert "postMessage" in html
    payload = payload_of(html)
    assert payload["status"] == "success"
    assert payload["payment"]["order_id"] == "widget-1"
    assert payload["payment"]["card_mask"] == "411111******1111"
    assert payload["payment"]["transaction"] == body["transaction"]


def test_a_decline_reaches_the_parent_as_an_error(client, merchant):
    body = widget(client, merchant, order_id="widget-decline")
    payload = payload_of(settle(client, body["widget_url"], card=DECLINE_CARD).text)

    assert payload["status"] == "error"
    assert payload["payment"]["status"] == "failed"
    assert payload["payment"]["code"] == "116"


def test_the_widget_never_redirects(client, merchant):
    """A redirect would navigate the iframe instead of answering the parent."""
    body = widget(client, merchant, order_id="widget-no-redirect")
    assert settle(client, body["widget_url"]).status_code == 200


def test_a_settled_widget_replays_its_result(client, merchant):
    body = widget(client, merchant, order_id="widget-replay")
    settle(client, body["widget_url"])

    html = client.get(path_of(body["widget_url"])).text
    assert payload_of(html)["payment"]["order_id"] == "widget-replay"


def test_paying_twice_does_not_settle_twice(client, merchant):
    body = widget(client, merchant, order_id="widget-once", amount="40.00")

    settle(client, body["widget_url"])
    balance = client.get("/_sandbox/balance").json()
    settle(client, body["widget_url"])

    assert client.get("/_sandbox/balance").json() == balance


def test_the_callback_fires_for_a_wallet_payment(client, merchant):
    """The widget answers the browser, but the shop is still settled server to server."""
    client.patch(
        f"/_sandbox/merchants/{merchant.public_key}",
        json={"result_url": "http://shop.invalid/webhooks/epoint"},
    )
    body = widget(client, merchant, order_id="widget-callback")
    settle(client, body["widget_url"])

    attempts = client.get("/_sandbox/callbacks").json()
    assert any(a["decoded"]["order_id"] == "widget-callback" for a in attempts)


def test_the_widget_needs_the_token_payments_grant(client, merchant):
    enable_features(client, merchant, token_payments_enabled=False)
    result = call(
        client,
        merchant,
        "/api/1/token/widget",
        {"amount": "10.00", "order_id": "widget-ungranted", "description": "x"},
    )
    assert "not enabled" in result["message"]
