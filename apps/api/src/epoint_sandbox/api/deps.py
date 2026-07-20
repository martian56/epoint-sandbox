from dataclasses import dataclass
from typing import Annotated, Any

from fastapi import Depends, Form, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from epoint_sandbox import signing
from epoint_sandbox.api.errors import EpointError
from epoint_sandbox.db import get_session
from epoint_sandbox.models import Merchant

SessionDep = Annotated[Session, Depends(get_session)]


@dataclass
class SignedRequest:
    merchant: Merchant
    payload: dict[str, Any]
    raw_data: str
    raw_signature: str

    def require(self, *fields: str) -> None:
        missing = [f for f in fields if self.payload.get(f) in (None, "")]
        if missing:
            raise EpointError(f"Missing required parameter(s): {', '.join(missing)}")

    def get(self, field: str, default: Any = None) -> Any:
        value = self.payload.get(field)
        return default if value in (None, "") else value


async def signed_request(
    request: Request,
    session: SessionDep,
    data: Annotated[str | None, Form()] = None,
    signature: Annotated[str | None, Form()] = None,
) -> SignedRequest:
    """Parse and verify the data + signature pair.

    B2B sends the same pair as JSON, so fall back to the body when the form is empty.
    """
    if data is None or signature is None:
        body = await _json_body(request)
        data = data or body.get("data")
        signature = signature or body.get("signature")

    if not data or not signature:
        raise EpointError("Both data and signature are required")

    try:
        unverified = signing.decode_payload(data)
    except signing.SignatureError as exc:
        raise EpointError(str(exc)) from exc

    public_key = unverified.get("public_key")
    if not public_key:
        raise EpointError("public_key is missing from data")

    merchant = session.scalar(select(Merchant).where(Merchant.public_key == public_key))
    if merchant is None:
        raise EpointError(f"Unknown public_key: {public_key}", status_code=403)

    try:
        payload = signing.verify(merchant.private_key, data, signature)
    except signing.SignatureError as exc:
        raise EpointError(
            str(exc),
            hint=signing.explain(merchant.private_key, data, signature).get("hint"),
        ) from exc

    request.state.merchant_id = merchant.id
    request.state.raw_data = data
    request.state.raw_signature = signature
    request.state.signature_valid = True
    request.state.request_payload = payload

    return SignedRequest(merchant, payload, data, signature)


async def _json_body(request: Request) -> dict[str, Any]:
    try:
        body = await request.json()
    except Exception:
        return {}
    return body if isinstance(body, dict) else {}


SignedRequestDep = Annotated[SignedRequest, Depends(signed_request)]
