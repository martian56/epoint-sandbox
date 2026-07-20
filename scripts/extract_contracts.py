"""Generate apps/api/src/epoint_sandbox/api/contract.py from the scraped docs.

The scrape is not redistributed, so this only runs with a local copy. The generated
contract.py is committed, so nothing downstream needs it.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "_private/docs/research/epoint-docs-raw.md"
OUT = ROOT / "apps/api/src/epoint_sandbox/api/contract.py"

# Doc page -> API path.
PAGES = {
    "/checkout/request": "/api/1/request",
    "/checkout/payment-request": "/api/1/payment-request",
    "/checkout/amex-request": "/api/1/amex-request",
    "/checkout/payment-change-sum": "/api/1/payment-change-sum",
    "/checkout/split-request": "/api/1/split-request",
    "/split-payment/split-request": "/api/1/split-request",
    "/split-payment/split-execute-pay": "/api/1/split-execute-pay",
    "/pre-auth/pre-auth-request": "/api/1/pre-auth-request",
    "/pre-auth/pre-auth-complete": "/api/1/pre-auth-complete",
    "/card-registration/card-registration": "/api/1/card-registration",
    "/card-registration/card-registration-with-pay": "/api/1/card-registration-with-pay",
    "/card-registration/execute-pay": "/api/1/execute-pay",
    "/status/get-status": "/api/1/get-status",
    "/status/get-status-card": "/api/1/get-status-card",
    "/refund/refund-request": "/api/1/refund-request",
    "/reverse/reverse": "/api/1/reverse",
    "/payout/payout": "/api/1/refund-request",
    "/invoice/create": "/api/1/invoices/create",
    "/invoice/update": "/api/1/invoices/update",
    "/invoice/view": "/api/1/invoices/view",
    "/invoice/list": "/api/1/invoices/list",
    "/invoice/send-sms": "/api/1/invoices/send-sms",
    "/invoice/send-email": "/api/1/invoices/send-email",
    "/installment/get-installment-request": "/api/1/get-installment-request",
    "/installment/installment-request": "/api/1/installment-request",
    "/wallet/wallet-payment": "/api/1/wallet/payment",
    "/b2b-payment/payment": "/api/1/b2b/payment",
    "/b2b-payment/payment-status": "/api/1/b2b/payment/{order_id}",
}

# Fields the sandbox adds deliberately. Anything else undocumented is a bug.
SANCTIONED_EXTRAS = {
    "/api/1/request": {"redirect_url"},
    "/api/1/payment-request": {"redirect_url"},
    "/api/1/amex-request": {"redirect_url"},
    "/api/1/payment-change-sum": {"redirect_url"},
    "/api/1/split-request": {"redirect_url"},
    "/api/1/pre-auth-request": {"redirect_url"},
    "/api/1/installment-request": {"redirect_url"},
    "/api/1/wallet/payment": {"redirect_url"},
    # Docs describe the redirect but omit the field. Unconfirmed.
    "/api/1/card-registration": {"redirect_url"},
    "/api/1/card-registration-with-pay": {"redirect_url"},
    "/api/1/token/widget": {"widget_url", "transaction"},
}

UNVERIFIED = {
    "/api/1/card-registration": "redirect_url is undocumented; confirm against production",
    "/api/1/card-registration-with-pay": (
        "the documented response carries rrn, bank_response and operation_code 200, which "
        "only exist once the customer has paid, so it reads as the callback payload rather "
        "than the response; those fields are withheld until a production capture settles it"
    ),
    "/api/1/reverse": (
        "message is documented but the production wording is unknown, so an empty string "
        "is returned to match the shape"
    ),
    "/api/1/payment-change-sum": (
        "docs omit transaction where siblings include it; the sandbox withholds it "
        "as the safe direction, but production may send it"
    ),
    "/api/1/refund-request": "payout mode is inferred from the card flag; unverified",
    "/api/1/request": (
        "the sandbox accepts any language value; whether production validates it "
        "against az, en and ru is unknown"
    ),
    "/api/1/b2b/payment": "not exercised against production",
    "/api/1/b2b/payment/{order_id}": "not exercised against production",
}


def response_fields(block: str) -> set[str]:
    start = block.find("### Response Parameters")
    if start < 0:
        start = block.find("### Response")
    if start < 0:
        return set()

    end = len(block)
    for marker in ("### Success", "Response \nSuccess", "### Error"):
        found = block.find(marker, start)
        if found > start:
            end = min(end, found)

    return {m.group(1) for m in re.finditer(r"\|\s*(\w+)\s*\n(?:Required|Optional)", block[start:end])}


def main() -> None:
    text = DOCS.read_text(encoding="utf-8")
    documented: dict[str, set[str]] = {}

    for page, api_path in PAGES.items():
        index = text.find(f"# {page}\n")
        if index < 0:
            print(f"  page not found: {page}")
            continue
        # Bounded, or the next endpoint's fields leak in.
        next_page = text.find("\n# /", index + 1)
        fields = response_fields(text[index : next_page if next_page > 0 else len(text)])
        if fields:
            documented.setdefault(api_path, set()).update(fields)

    lines = [
        '"""Documented response fields, generated from the scraped epoint docs.',
        "",
        "Regenerate with scripts/extract_contracts.py. Do not edit by hand.",
        '"""',
        "",
        "DOCUMENTED_RESPONSE_FIELDS: dict[str, frozenset[str]] = {",
    ]
    for path in sorted(documented):
        names = ", ".join(f'"{f}"' for f in sorted(documented[path]))
        lines.append(f'    "{path}": frozenset({{{names}}}),')
    lines.append("}")
    lines.append("")
    lines.append("# Extras the sandbox adds deliberately. Reasons live in the generator.")
    lines.append("SANCTIONED_EXTRAS: dict[str, frozenset[str]] = {")
    for path in sorted(SANCTIONED_EXTRAS):
        names = ", ".join(f'"{f}"' for f in sorted(SANCTIONED_EXTRAS[path]))
        lines.append(f'    "{path}": frozenset({{{names}}}),')
    lines.append("}")
    lines.append("")
    lines.append("# Rests on documentation alone, never seen from the real gateway.")
    lines.append("UNVERIFIED: dict[str, str] = {")
    for path, reason in sorted(UNVERIFIED.items()):
        words = " ".join(reason.split()).split()
        if len(" ".join(words)) + len(path) > 80:
            lines.append(f'    "{path}": (')
            chunk = ""
            for word in words:
                if len(chunk) + len(word) > 76:
                    lines.append(f'        "{chunk.strip()} "')
                    chunk = ""
                chunk += f"{word} "
            lines.append(f'        "{chunk.strip()}"')
            lines.append("    ),")
        else:
            lines.append(f'    "{path}": "{" ".join(words)}",')
    lines.append("}")
    lines.append("")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} covering {len(documented)} endpoints")
    print(json.dumps({k: sorted(v) for k, v in sorted(documented.items())}, indent=2)[:600])


if __name__ == "__main__":
    main()
