import logging
import pathlib

from .card_database import CARD_DATABASE
from .decklist import Decklist


logger = logging.getLogger(__name__)

PROJECT_ROOT = pathlib.Path(__file__).parent.parent.parent
DECKLIST_FOLDER = PROJECT_ROOT / "data" / "decklists"


class DecklistBuilder:
    def __init__(self, commander_deck: bool = False):
        self._commander_deck = commander_deck

    def build(self, deck_name: str, fetch_missing: bool = True) -> Decklist:
        with open(DECKLIST_FOLDER / deck_name, "r") as file:
            lines = file.readlines()

        self._deck = Decklist()
        self._zone_to_add = self._deck.main_deck
        for i, line in enumerate(lines):
            # Is there a deck zone change ?
            if self._commander_deck and line.startswith("Commander:"):
                self._zone_to_add = self._deck.commander_zone
                continue
            if not line.strip():
                if self._commander_deck and self._zone_to_add is self._deck.commander_zone:
                    self._zone_to_add = self._deck.main_deck
                continue

            number_of_cards, cardname = self._extract_cards(i, line)
            self._add_cards_to_zone(number_of_cards, cardname)

        if self._commander_deck and not self._deck.is_commander_deck():
            logger.warning(
                "%s was parsed as a commander deck but doesn't total 100 cards "
                "(main deck + commander zone).",
                deck_name,
            )

        all_cardnames = {
            *self._deck.main_deck,
            *self._deck.commander_zone,
            *self._deck.sideboard_zone,
            *self._deck.considering_zone,
        }
        if fetch_missing:
            CARD_DATABASE.fetch_missing(all_cardnames)
        return self._deck

    @staticmethod
    def _extract_cards(i, line):
        words = line.strip().split(" ")
        number_of_cards_str = words[0]
        try:
            number_of_cards = int(number_of_cards_str)
        except ValueError as e:
            raise ValueError(f"The line {i} doesn't have a proper number of cards. Source: \n {e}")

        cardname = " ".join(words[1:])
        return number_of_cards, cardname

    def _add_cards_to_zone(self, number_of_cards: int, cardname: str):
        if cardname in self._zone_to_add:
            self._zone_to_add[cardname] += number_of_cards
        else:
            self._zone_to_add[cardname] = number_of_cards
