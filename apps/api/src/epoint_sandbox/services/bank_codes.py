"""Bank response codes as published in the epoint error reference."""

APPROVED = "000"

BANK_CODES: dict[str, str] = {
    "000": "Approved",
    "100": "Decline (general, no comments)",
    "101": "Decline (card expired)",
    "102": "Decline (suspected fraud)",
    "103": "Decline (contact acquirer bank)",
    "104": "Decline (restricted card)",
    "105": "Decline (contact acquirer bank's security department)",
    "106": "Decline (allowable PIN attempts exceeded)",
    "107": "Decline (contact card issuer)",
    "108": "Decline (contact card issuer for special conditions)",
    "109": "Decline, invalid merchant",
    "110": "Decline, invalid amount",
    "111": "Decline, invalid card number",
    "112": "Decline, PIN required",
    "113": "Decline, unacceptable amount",
    "114": "Decline, requested account type not available",
    "115": "Decline, requested function not supported",
    "116": "Decline, insufficient funds",
    "117": "Decline, incorrect PIN",
    "118": "Decline, no card data",
    "119": "Decline, transaction not permitted for cardholder",
    "120": "Decline, transaction not permitted for terminal",
    "121": "Decline, withdrawal limit exceeded",
    "122": "Decline, security violation",
    "123": "Decline, withdrawal frequency limit exceeded",
    "124": "Decline, law violation",
    "125": "Decline, invalid card",
    "126": "Decline, PIN block error",
    "127": "Decline, PIN length error",
    "128": "Decline, PIN synchronization error",
    "129": "Decline, suspected counterfeit card",
    "180": "Decline, by cardholder's request",
    "200": "Pick-up (general, no comments)",
    "201": "Pick-up (card expired)",
    "202": "Pick-up (suspected fraud)",
    "203": "Pick-up (contact acquirer bank)",
    "204": "Pick-up (restricted card)",
    "205": "Pick-up (contact acquirer bank's security department)",
    "206": "Pick-up (allowable PIN attempts exceeded)",
    "207": "Pick-up (special condition)",
    "208": "Pick-up (lost card)",
    "209": "Pick-up (stolen card)",
    "210": "Pick-up (suspected counterfeit card)",
    "400": "Accepted (for reversal)",
    "499": "Approved, no original message data",
    "902": "Decline reason: invalid transaction",
    "903": "Status indicator: re-enter transaction",
    "904": "Decline reason: format error",
}


def describe(code: str) -> str:
    return BANK_CODES.get(code, "Unknown bank response code")


def is_approved(code: str) -> bool:
    return code == APPROVED
