from pydantic import BaseModel
from .card import Card
from .card_database import CARD_DATABASE

CardDictionnary = dict[str, int]

def count_cards(zone: CardDictionnary) -> int:
    return sum(zone.values())


class Decklist(BaseModel):
    main_deck: CardDictionnary = {}
    commander_zone: CardDictionnary = {}
    sideboard_zone: CardDictionnary = {}
    considering_zone: CardDictionnary = {}

    def is_commander_deck(self):
        cards_in_commander_zone = sum(self.commander_zone.values())
        return sum(self.main_deck.values()) + cards_in_commander_zone == 100

    def get_card(self, cardname: str) -> Card | None:
        return CARD_DATABASE.get(cardname)