import logging
from typing import Iterable

from .card import Card
from scryfall.fetcher import DeckContentFetcher
from scryfall.identifiers import dict_to_card_identifier

logger = logging.getLogger(__name__)

# Scryfall's /cards/collection endpoint rejects requests with more than 75 identifiers.
MAX_IDENTIFIERS_PER_REQUEST = 75


class CardDatabase:
    def __init__(self):
        self._cards: dict[str, Card] = {}

    def get(self, cardname: str) -> Card | None:
        return self._cards.get(cardname)

    def fetch_missing(self, cardnames: Iterable[str], fetcher: DeckContentFetcher | None = None) -> None:
        missing = [name for name in cardnames if name not in self._cards]
        if not missing:
            return
        fetcher = fetcher or DeckContentFetcher()
        for i in range(0, len(missing), MAX_IDENTIFIERS_PER_REQUEST):
            batch = missing[i:i + MAX_IDENTIFIERS_PER_REQUEST]
            identifiers = [dict_to_card_identifier({"name": name}) for name in batch]
            payload = fetcher.fetch_cards_infos(identifiers).json()
            for raw_card in payload.get("data", []):
                self._cards[raw_card["name"]] = Card(cardname=raw_card["name"], data=raw_card)
            for not_found in payload.get("not_found", []):
                logger.warning("Card not found on Scryfall: %s", not_found)


CARD_DATABASE = CardDatabase()
