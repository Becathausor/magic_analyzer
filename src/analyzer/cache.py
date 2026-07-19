"""Persistent on-disk cache for deck analysis results.

Entries are keyed by a hash of the deck's contents (see `deck_cache_key`),
so edited decklists naturally miss the cache instead of serving a stale
analysis - no TTL/invalidation logic needed.
"""

import hashlib
import json
from pathlib import Path

from card import Decklist

PROJECT_ROOT = Path(__file__).parent.parent.parent
CACHE_FILE = PROJECT_ROOT / "data" / "analysis_cache.json"


def deck_cache_key(deck: Decklist) -> str:
    payload = {
        "main_deck": sorted(deck.main_deck.items()),
        "commander_zone": sorted(deck.commander_zone.items()),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


class AnalysisCache:
    def __init__(self, path: Path = CACHE_FILE):
        self._path = path
        self._entries: dict[str, dict] = self._load()

    def _load(self) -> dict[str, dict]:
        if not self._path.exists():
            return {}
        try:
            return json.loads(self._path.read_text())
        except json.JSONDecodeError:
            return {}

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(self._entries))

    def get(self, key: str) -> dict | None:
        entry = self._entries.get(key)
        return entry["data"] if entry is not None else None

    def set(self, key: str, data: dict) -> None:
        self._entries[key] = {"data": data}
        self._save()


ANALYSIS_CACHE = AnalysisCache()
