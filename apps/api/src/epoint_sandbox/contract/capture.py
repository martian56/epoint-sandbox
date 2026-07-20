"""Record probe responses from any epoint-compatible host."""

import base64
import hashlib
import json
import re
import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

from epoint_sandbox import signing
from epoint_sandbox.contract.probes import Probe, Tier, by_tier

# Vary per run, so they are excluded from diffs.
VOLATILE = re.compile(
    r"^(order_id|trace_id|redirect_url|widget_url|bulkId|bank_transaction|rrn|transaction|card_id|id)$"
)


@dataclass
class Recording:
    probe: str
    path: str
    request: dict[str, Any]
    http_status: int
    headers: dict[str, str]
    body: Any

    def to_dict(self) -> dict[str, Any]:
        return {
            "probe": self.probe,
            "path": self.path,
            "request": self.request,
            "http_status": self.http_status,
            "headers": self.headers,
            "body": self.body,
        }


def _broken_signature(kind: str, private_key: str, data: str) -> str:
    concatenated = f"{private_key}{data}{private_key}"
    if kind == "hex":
        return hashlib.sha1(concatenated.encode()).hexdigest()
    if kind == "no_suffix":
        digest = hashlib.sha1(f"{private_key}{data}".encode()).digest()
        return base64.b64encode(digest).decode()
    if kind == "no_key":
        return base64.b64encode(hashlib.sha1(data.encode()).digest()).decode()
    return "not-a-signature"


def run_probe(
    client: httpx.Client,
    base_url: str,
    probe: Probe,
    public_key: str,
    private_key: str,
    run_id: str = "",
) -> Recording:
    url = base_url.rstrip("/") + probe.path

    if not probe.signed:
        response = client.request(probe.method, url)
        return _record(probe, {}, response)

    payload = {"public_key": public_key, **probe.payload}

    # Unique per run, or a repeat capture only sees duplicate-order errors.
    if run_id and isinstance(payload.get("order_id"), str):
        payload["order_id"] = f"{payload['order_id']}-{run_id}"
    data = signing.encode_payload(payload)
    signature = (
        _broken_signature(probe.break_signature, private_key, data)
        if probe.break_signature
        else signing.sign(private_key, data)
    )

    pair = {"data": data, "signature": signature}
    response = client.post(url, json=pair) if probe.json_body else client.post(url, data=pair)
    return _record(probe, payload, response)


def _record(probe: Probe, payload: dict[str, Any], response: httpx.Response) -> Recording:
    try:
        body = response.json()
    except ValueError:
        body = {"__non_json__": response.text[:500]}

    interesting = {
        k.lower(): v
        for k, v in response.headers.items()
        if k.lower() in {"content-type", "x-request-id", "x-epoint-sandbox"}
    }
    return Recording(probe.name, probe.path, payload, response.status_code, interesting, body)


def normalise(value: Any) -> Any:
    """Blank out values that change every run."""
    if isinstance(value, dict):
        return {k: ("<volatile>" if VOLATILE.match(k) else normalise(v)) for k, v in value.items()}
    if isinstance(value, list):
        return [normalise(v) for v in value]
    return value


def shape(recording: Recording) -> dict[str, Any]:
    """The part of a recording worth comparing."""
    body = recording.body
    return {
        "http_status": recording.http_status,
        "body_keys": sorted(body) if isinstance(body, dict) else f"<{type(body).__name__}>",
        "body": normalise(body),
    }


def capture(
    base_url: str,
    public_key: str,
    private_key: str,
    tier: Tier,
    out_dir: Path,
    timeout: float = 20.0,
) -> list[Recording]:
    out_dir.mkdir(parents=True, exist_ok=True)
    recordings: list[Recording] = []
    run_id = secrets.token_hex(3)

    with httpx.Client(timeout=timeout, follow_redirects=False) as client:
        for probe in by_tier(tier):
            recording = run_probe(client, base_url, probe, public_key, private_key, run_id)
            recordings.append(recording)
            (out_dir / f"{probe.name}.json").write_text(
                json.dumps(recording.to_dict(), indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

    return recordings


def compare(reference_dir: Path, candidate_dir: Path) -> list[dict[str, Any]]:
    """Report where the candidate disagrees with the reference."""
    differences: list[dict[str, Any]] = []

    for reference_file in sorted(reference_dir.glob("*.json")):
        candidate_file = candidate_dir / reference_file.name
        if not candidate_file.exists():
            differences.append({"probe": reference_file.stem, "issue": "missing from candidate"})
            continue

        reference = json.loads(reference_file.read_text(encoding="utf-8"))
        candidate = json.loads(candidate_file.read_text(encoding="utf-8"))

        ref_shape = shape(Recording(**reference))
        cand_shape = shape(Recording(**candidate))

        if ref_shape["http_status"] != cand_shape["http_status"]:
            differences.append(
                {
                    "probe": reference["probe"],
                    "issue": "http status",
                    "reference": ref_shape["http_status"],
                    "candidate": cand_shape["http_status"],
                }
            )

        if ref_shape["body_keys"] != cand_shape["body_keys"]:
            differences.append(
                {
                    "probe": reference["probe"],
                    "issue": "response fields",
                    "reference": ref_shape["body_keys"],
                    "candidate": cand_shape["body_keys"],
                }
            )

    return differences
