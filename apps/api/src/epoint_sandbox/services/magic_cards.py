"""Test cards and the outcome each produces.

epoint publishes none, so 4000 0000 0000 0NNN maps to bank response code NNN.
"""

from dataclasses import dataclass

from epoint_sandbox.services import bank_codes

SUCCESS_CARD = "4111111111111111"
TIMEOUT_CARD = "4000000000009999"
THREE_DS_CARD = "4000000000003220"

DECLINE_PREFIX = "4000000000000"
CARD_LENGTH = 16


@dataclass(frozen=True)
class CardOutcome:
    bank_code: str
    message: str
    approved: bool
    timeout: bool = False
    requires_3ds: bool = False


def normalize(number: str) -> str:
    return "".join(ch for ch in number if ch.isdigit())


def resolve(number: str) -> CardOutcome:
    digits = normalize(number)

    if digits == SUCCESS_CARD:
        return CardOutcome(bank_codes.APPROVED, bank_codes.describe(bank_codes.APPROVED), True)

    if digits == TIMEOUT_CARD:
        return CardOutcome("", "Gateway timeout, no callback sent", False, timeout=True)

    if digits == THREE_DS_CARD:
        return CardOutcome(
            bank_codes.APPROVED,
            bank_codes.describe(bank_codes.APPROVED),
            True,
            requires_3ds=True,
        )

    if digits.startswith(DECLINE_PREFIX) and len(digits) == CARD_LENGTH:
        code = digits[-3:]
        if code in bank_codes.BANK_CODES:
            return CardOutcome(code, bank_codes.describe(code), bank_codes.is_approved(code))

    return CardOutcome("100", bank_codes.describe("100"), False)


def mask(number: str) -> str:
    digits = normalize(number)
    if len(digits) < 10:
        return digits
    return f"{digits[:6]}{'*' * 6}{digits[-4:]}"


def catalogue() -> list[dict[str, str | bool]]:
    """The list shown in the dashboard."""
    entries: list[dict[str, str | bool]] = [
        {
            "number": SUCCESS_CARD,
            "code": bank_codes.APPROVED,
            "outcome": bank_codes.describe(bank_codes.APPROVED),
            "approved": True,
        }
    ]
    for code in ("101", "102", "104", "111", "116", "121", "125", "180", "209"):
        entries.append(
            {
                "number": f"{DECLINE_PREFIX}{code}",
                "code": code,
                "outcome": bank_codes.describe(code),
                "approved": False,
            }
        )
    entries.append(
        {
            "number": THREE_DS_CARD,
            "code": bank_codes.APPROVED,
            "outcome": "Approved after a 3DS challenge",
            "approved": True,
        }
    )
    entries.append(
        {
            "number": TIMEOUT_CARD,
            "code": "",
            "outcome": "Gateway timeout, no callback sent",
            "approved": False,
        }
    )
    return entries


def outcome_for_code(bank_code: str | None) -> CardOutcome:
    """Rebuild the outcome for a saved card from its stored code."""
    if not bank_code:
        return CardOutcome("100", bank_codes.describe("100"), False)
    return CardOutcome(bank_code, bank_codes.describe(bank_code), bank_codes.is_approved(bank_code))
