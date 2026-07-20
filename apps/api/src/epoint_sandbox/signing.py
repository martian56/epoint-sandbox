import base64
import binascii
import hashlib
import json
from typing import Any


class SignatureError(Exception):
    """Payload could not be decoded, or its signature did not match."""


def sign(private_key: str, data: str) -> str:
    """Sign an already base64-encoded payload.

    The sha1 digest must be the raw 20 bytes, not the hex string.
    """
    digest = hashlib.sha1(f"{private_key}{data}{private_key}".encode()).digest()
    return base64.b64encode(digest).decode()


def encode_payload(payload: dict[str, Any]) -> str:
    return base64.b64encode(json.dumps(payload, separators=(",", ":")).encode()).decode()


def decode_payload(data: str) -> dict[str, Any]:
    try:
        decoded = base64.b64decode(data, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise SignatureError("data is not valid base64") from exc

    try:
        parsed = json.loads(decoded)
    except json.JSONDecodeError as exc:
        raise SignatureError("data does not contain valid JSON") from exc

    if not isinstance(parsed, dict):
        raise SignatureError("data must decode to a JSON object")
    return parsed


def verify(private_key: str, data: str, signature: str) -> dict[str, Any]:
    """Verify a signature and return the decoded payload."""
    expected = sign(private_key, data)
    if not _constant_time_equals(expected, signature):
        raise SignatureError("signature does not match")
    return decode_payload(data)


def explain(private_key: str, data: str, signature: str | None = None) -> dict[str, Any]:
    """Break a signature down step by step for the debugger."""
    concatenated = f"{private_key}{data}{private_key}"
    expected = sign(private_key, data)

    result: dict[str, Any] = {
        "concatenated": concatenated,
        "concatenated_length": len(concatenated),
        "sha1_hex": hashlib.sha1(concatenated.encode()).hexdigest(),
        "expected_signature": expected,
        "formula": "base64(sha1_raw(private_key + data + private_key))",
    }

    try:
        result["decoded_payload"] = decode_payload(data)
    except SignatureError as exc:
        result["decoded_payload"] = None
        result["decode_error"] = str(exc)

    if signature is not None:
        result["provided_signature"] = signature
        result["matches"] = _constant_time_equals(expected, signature)
        if not result["matches"]:
            result["hint"] = _diagnose(private_key, data, signature)

    return result


def _constant_time_equals(a: str, b: str) -> bool:
    if len(a) != len(b):
        return False
    mismatch = 0
    for x, y in zip(a.encode(), b.encode(), strict=True):
        mismatch |= x ^ y
    return mismatch == 0


def _diagnose(private_key: str, data: str, signature: str) -> str:
    """Identify which common mistake produced a mismatch."""
    concatenated = f"{private_key}{data}{private_key}"

    hex_digest = hashlib.sha1(concatenated.encode()).hexdigest()
    if signature == hex_digest:
        return "You used the SHA-1 hex digest. Take the raw 20 byte digest, then base64 it."
    if signature == base64.b64encode(hex_digest.encode()).decode():
        return "You base64-encoded the hex digest. Base64 the raw digest instead."

    without_suffix = hashlib.sha1(f"{private_key}{data}".encode()).digest()
    if signature == base64.b64encode(without_suffix).decode():
        return "The private key must be appended after data as well as prepended."

    data_only = hashlib.sha1(data.encode()).digest()
    if signature == base64.b64encode(data_only).decode():
        return "The private key is missing from the hashed string entirely."

    return (
        "Signature does not match any common mistake. "
        "Check the private key and the exact data string."
    )
