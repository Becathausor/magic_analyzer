from card import decklist as decklist_module
from card.card import Card
from card.decklist import Decklist, count_cards


def test_is_commander_deck_true_when_100_cards_total():
    deck = Decklist(main_deck={"Island": 99}, commander_zone={"The Ancient One": 1})
    assert deck.is_commander_deck() is True


def test_is_commander_deck_false_when_not_100_cards_total():
    deck = Decklist(main_deck={"Island": 99}, commander_zone={})
    assert deck.is_commander_deck() is False


def test_count_cards_sums_zone_quantities():
    assert count_cards({"Island": 4, "Wonder": 1}) == 5


def test_count_cards_empty_zone_is_zero():
    assert count_cards({}) == 0


def test_get_card_delegates_to_card_database(monkeypatch):
    expected_card = Card(cardname="Island", data={"name": "Island"})

    class FakeDatabase:
        def get(self, cardname):
            return expected_card if cardname == "Island" else None

    monkeypatch.setattr(decklist_module, "CARD_DATABASE", FakeDatabase())

    deck = Decklist(main_deck={"Island": 4})
    assert deck.get_card("Island") is expected_card
    assert deck.get_card("Unknown Card") is None
