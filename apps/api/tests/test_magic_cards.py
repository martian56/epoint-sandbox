import pytest

from epoint_sandbox.services import magic_cards


def test_success_card_is_approved():
    outcome = magic_cards.resolve(magic_cards.SUCCESS_CARD)
    assert outcome.approved is True
    assert outcome.bank_code == "000"


@pytest.mark.parametrize(
    ("number", "code"),
    [
        ("4000000000000116", "116"),
        ("4000000000000101", "101"),
        ("4000000000000102", "102"),
        ("4000000000000209", "209"),
    ],
)
def test_decline_cards_encode_their_bank_code(number, code):
    outcome = magic_cards.resolve(number)
    assert outcome.bank_code == code
    assert outcome.approved is False


def test_timeout_card_flags_timeout():
    outcome = magic_cards.resolve(magic_cards.TIMEOUT_CARD)
    assert outcome.timeout is True
    assert outcome.approved is False


def test_three_ds_card_requires_challenge_and_approves():
    outcome = magic_cards.resolve(magic_cards.THREE_DS_CARD)
    assert outcome.requires_3ds is True
    assert outcome.approved is True


def test_unknown_card_falls_back_to_generic_decline():
    outcome = magic_cards.resolve("5555444433332222")
    assert outcome.bank_code == "100"
    assert outcome.approved is False


def test_spaces_are_ignored():
    assert magic_cards.resolve("4111 1111 1111 1111").approved is True


def test_mask_keeps_first_six_and_last_four():
    assert magic_cards.mask("4111111111111111") == "411111******1111"


def test_catalogue_entries_resolve_to_their_documented_outcome():
    """Asserting only `approved` let a wrong-length prefix slip through."""
    for entry in magic_cards.catalogue():
        number = str(entry["number"])
        outcome = magic_cards.resolve(number)

        assert len(number) == magic_cards.CARD_LENGTH, f"{number} is not 16 digits"
        assert outcome.approved == entry["approved"], number
        if entry["code"]:
            assert outcome.bank_code == entry["code"], number


def test_every_documented_decline_keeps_its_own_code():
    declines = [c for c in magic_cards.catalogue() if not c["approved"] and c["code"]]
    codes = {str(c["code"]) for c in declines}

    assert len(codes) == len(declines), "decline cards collapsed onto the same code"
    assert "100" not in codes, "a card fell through to the generic decline"
