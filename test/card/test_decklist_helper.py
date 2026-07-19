import pytest

from card import decklist_helper as decklist_helper_module
from card.decklist_helper import DecklistBuilder


def write_decklist(tmp_path, monkeypatch, filename, content):
    monkeypatch.setattr(decklist_helper_module, "DECKLIST_FOLDER", tmp_path)
    (tmp_path / filename).write_text(content)


def test_build_parses_quantities_and_cardnames(tmp_path, monkeypatch):
    write_decklist(tmp_path, monkeypatch, "deck.txt", "4 Island\n1 Wonder\n")

    deck = DecklistBuilder().build("deck.txt", fetch_missing=False)

    assert deck.main_deck == {"Island": 4, "Wonder": 1}


def test_build_sums_repeated_cardnames_in_same_zone(tmp_path, monkeypatch):
    write_decklist(tmp_path, monkeypatch, "deck.txt", "1 Island\n1 Island\n")

    deck = DecklistBuilder().build("deck.txt", fetch_missing=False)

    assert deck.main_deck == {"Island": 2}


def test_build_handles_commander_zone_and_resets_after_blank_line(tmp_path, monkeypatch):
    content = "1 Wonder\n\nCommander:\n1 The Ancient One\n\n1 Sol Ring\n"
    write_decklist(tmp_path, monkeypatch, "deck.txt", content)

    deck = DecklistBuilder(commander_deck=True).build("deck.txt", fetch_missing=False)

    assert deck.commander_zone == {"The Ancient One": 1}
    assert deck.main_deck == {"Wonder": 1, "Sol Ring": 1}


def test_build_raises_value_error_on_malformed_quantity(tmp_path, monkeypatch):
    write_decklist(tmp_path, monkeypatch, "deck.txt", "four Island\n")

    with pytest.raises(ValueError):
        DecklistBuilder().build("deck.txt", fetch_missing=False)


def test_build_with_fetch_missing_false_never_touches_card_database(tmp_path, monkeypatch):
    write_decklist(tmp_path, monkeypatch, "deck.txt", "4 Island\n1 Wonder\n")

    class RaisingDatabase:
        def fetch_missing(self, cardnames):
            raise AssertionError("fetch_missing should not be called")

    monkeypatch.setattr(decklist_helper_module, "CARD_DATABASE", RaisingDatabase())

    deck = DecklistBuilder().build("deck.txt", fetch_missing=False)

    assert deck.main_deck == {"Island": 4, "Wonder": 1}


def test_build_with_fetch_missing_true_reaches_all_cardnames(tmp_path, monkeypatch):
    write_decklist(tmp_path, monkeypatch, "deck.txt", "4 Island\n1 Wonder\n")

    class FakeDatabase:
        def __init__(self):
            self.fetched_names = set()

        def fetch_missing(self, cardnames):
            self.fetched_names.update(cardnames)

    fake_db = FakeDatabase()
    monkeypatch.setattr(decklist_helper_module, "CARD_DATABASE", fake_db)

    DecklistBuilder().build("deck.txt")

    assert fake_db.fetched_names == {"Island", "Wonder"}
