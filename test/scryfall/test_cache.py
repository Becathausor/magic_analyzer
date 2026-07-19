from datetime import timedelta

from scryfall import ScryfallCache


def test_get_returns_none_for_unknown_card(tmp_path):
    cache = ScryfallCache(path=tmp_path / "cache.json")
    assert cache.get("Island") is None


def test_set_then_get_returns_same_data(tmp_path):
    cache = ScryfallCache(path=tmp_path / "cache.json")
    cache.set("Island", {"name": "Island", "id": "abc"})
    assert cache.get("Island") == {"name": "Island", "id": "abc"}


def test_data_persists_across_instances(tmp_path):
    path = tmp_path / "cache.json"
    first = ScryfallCache(path=path)
    first.set("Island", {"name": "Island"})

    second = ScryfallCache(path=path)
    assert second.get("Island") == {"name": "Island"}


def test_expired_entry_is_treated_as_uncached(tmp_path):
    cache = ScryfallCache(path=tmp_path / "cache.json", ttl=timedelta(seconds=0))
    cache.set("Island", {"name": "Island"})
    assert cache.get("Island") is None


def test_corrupted_cache_file_is_ignored(tmp_path):
    path = tmp_path / "cache.json"
    path.write_text("not valid json{{{")
    cache = ScryfallCache(path=path)
    assert cache.get("Island") is None
