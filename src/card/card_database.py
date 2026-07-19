import logging
from typing import Iterable

from .card import Card
from scryfall import DeckContentFetcher, ScryfallCache, dict_to_card_identifier

logger = logging.getLogger(__name__)

# Scryfall's /cards/collection endpoint rejects requests with more than 75 identifiers.
MAX_IDENTIFIERS_PER_REQUEST = 75


class CardDatabase:
    def __init__(self, cache: ScryfallCache | None = None):
        self._cards: dict[str, Card] = {}
        self._not_found: set[str] = set()
        self._cache = cache or ScryfallCache()

    def get(self, cardname: str) -> Card | None:
        return self._cards.get(cardname)

    def is_not_found(self, cardname: str) -> bool:
        return cardname in self._not_found

    def fetch_missing(self, cardnames: Iterable[str], fetcher: DeckContentFetcher | None = None) -> None:
        missing = []
        for name in cardnames:
            if name in self._cards or name in self._not_found:
                continue
            cached_data = self._cache.get(name)
            if cached_data is not None:
                self._cards[name] = Card(cardname=name, data=cached_data)
            else:
                missing.append(name)
        if not missing:
            return
        fetcher = fetcher or DeckContentFetcher()
        for i in range(0, len(missing), MAX_IDENTIFIERS_PER_REQUEST):
            batch = missing[i:i + MAX_IDENTIFIERS_PER_REQUEST]
            identifiers = [dict_to_card_identifier({"name": name}) for name in batch]
            try:
                payload = fetcher.fetch_cards_infos(identifiers).json()
            except Exception:
                logger.exception("Scryfall fetch failed for batch, will retry on next request")
                continue
            for raw_card in payload.get("data", []):
                candidate_names = {raw_card["name"].lower()}
                candidate_names.update(
                    face["name"].lower() for face in raw_card.get("card_faces", []) if "name" in face
                )
                matched = [name for name in batch if name.lower() in candidate_names]
                if not matched:
                    logger.warning("Fetched card did not match any requested name: %s", raw_card.get("name"))
                    continue
                for name in matched:
                    self._cards[name] = Card(cardname=name, data=raw_card)
                    self._cache.set(name, raw_card)
            for not_found in payload.get("not_found", []):
                name = not_found.get("name")
                if name:
                    self._not_found.add(name)
                logger.warning("Card not found on Scryfall: %s", not_found)


CARD_DATABASE = CardDatabase()
