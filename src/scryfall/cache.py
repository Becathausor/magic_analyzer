"""Persistent, TTL'd on-disk cache for Scryfall card data.

Avoids re-fetching cards from Scryfall across process restarts as long as
the cached data isn't older than the TTL.
"""

import json
import pathlib
from datetime import datetime, timedelta, timezone

PROJECT_ROOT = pathlib.Path(__file__).parent.parent.parent
CACHE_FILE = PROJECT_ROOT / "data" / "scryfall_cache.json"
CACHE_TTL = timedelta(days=30)


class ScryfallCache:
    def __init__(self, path: pathlib.Path = CACHE_FILE, ttl: timedelta = CACHE_TTL):
        self._path = path
        self._ttl = ttl
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

    def get(self, cardname: str) -> dict | None:
        entry = self._entries.get(cardname)
        if entry is None:
            return None
        fetched_at = datetime.fromisoformat(entry["fetched_at"])
        if datetime.now(timezone.utc) - fetched_at > self._ttl:
            return None
        return entry["data"]

    def set(self, cardname: str, data: dict) -> None:
        self._entries[cardname] = {
            "data": data,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
        self._save()
