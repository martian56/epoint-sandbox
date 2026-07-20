import base64
import hashlib

import pytest

from epoint_sandbox import signing

PRIVATE_KEY = "d3hjsl38sd8kdfhbcea0be04eafde9e8e2bad2fb092d"
PAYLOAD = {
    "public_key": "i000000001",
    "amount": "30.75",
    "currency": "AZN",
    "description": "test payment",
    "order_id": "1",
}


def test_sign_matches_documented_formula():
    data = signing.encode_payload(PAYLOAD)
    expected = base64.b64encode(
        hashlib.sha1(f"{PRIVATE_KEY}{data}{PRIVATE_KEY}".encode()).digest()
    ).decode()
    assert signing.sign(PRIVATE_KEY, data) == expected


def test_sign_uses_raw_digest_not_hex():
    data = signing.encode_payload(PAYLOAD)
    hex_signature = hashlib.sha1(f"{PRIVATE_KEY}{data}{PRIVATE_KEY}".encode()).hexdigest()
    assert signing.sign(PRIVATE_KEY, data) != hex_signature


def test_encode_decode_round_trip():
    data = signing.encode_payload(PAYLOAD)
    assert signing.decode_payload(data) == PAYLOAD


def test_verify_accepts_valid_signature():
    data = signing.encode_payload(PAYLOAD)
    signature = signing.sign(PRIVATE_KEY, data)
    assert signing.verify(PRIVATE_KEY, data, signature) == PAYLOAD


def test_verify_rejects_wrong_key():
    data = signing.encode_payload(PAYLOAD)
    signature = signing.sign(PRIVATE_KEY, data)
    with pytest.raises(signing.SignatureError):
        signing.verify("wrong-key", data, signature)


@pytest.mark.parametrize("bad", ["not base64!", "", "###"])
def test_decode_rejects_malformed_base64(bad):
    with pytest.raises(signing.SignatureError):
        signing.decode_payload(bad)


def test_decode_rejects_non_object_json():
    data = base64.b64encode(b"[1, 2, 3]").decode()
    with pytest.raises(signing.SignatureError):
        signing.decode_payload(data)


def test_explain_detects_hex_digest_mistake():
    data = signing.encode_payload(PAYLOAD)
    hex_signature = hashlib.sha1(f"{PRIVATE_KEY}{data}{PRIVATE_KEY}".encode()).hexdigest()
    result = signing.explain(PRIVATE_KEY, data, hex_signature)
    assert result["matches"] is False
    assert "hex digest" in result["hint"]


def test_explain_detects_missing_suffix_key():
    data = signing.encode_payload(PAYLOAD)
    wrong = base64.b64encode(hashlib.sha1(f"{PRIVATE_KEY}{data}".encode()).digest()).decode()
    result = signing.explain(PRIVATE_KEY, data, wrong)
    assert "appended after data" in result["hint"]


def test_explain_detects_missing_key_entirely():
    data = signing.encode_payload(PAYLOAD)
    wrong = base64.b64encode(hashlib.sha1(data.encode()).digest()).decode()
    result = signing.explain(PRIVATE_KEY, data, wrong)
    assert "missing from the hashed string" in result["hint"]


def test_explain_reports_match_for_correct_signature():
    data = signing.encode_payload(PAYLOAD)
    result = signing.explain(PRIVATE_KEY, data, signing.sign(PRIVATE_KEY, data))
    assert result["matches"] is True
    assert "hint" not in result


def test_placeholder_fits_the_transaction_id_column():
    """SQLite ignores VARCHAR limits, so guard the Postgres constraint."""
    from epoint_sandbox.models import Transaction
    from epoint_sandbox.services import ids

    limit = Transaction.__table__.c.transaction_id.type.length
    assert len(ids.placeholder()) <= limit
    assert len(ids.transaction_id(9_999_999_999)) <= limit
