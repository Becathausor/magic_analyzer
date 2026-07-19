from analyzer.cache import AnalysisCache, deck_cache_key
from card.decklist import Decklist


def test_get_returns_none_for_unknown_key(tmp_path):
    cache = AnalysisCache(path=tmp_path / "cache.json")
    assert cache.get("abc") is None


def test_set_then_get_returns_same_data(tmp_path):
    cache = AnalysisCache(path=tmp_path / "cache.json")
    cache.set("abc", {"deck_goal": "Go wide"})
    assert cache.get("abc") == {"deck_goal": "Go wide"}


def test_data_persists_across_instances(tmp_path):
    path = tmp_path / "cache.json"
    first = AnalysisCache(path=path)
    first.set("abc", {"deck_goal": "Go wide"})

    second = AnalysisCache(path=path)
    assert second.get("abc") == {"deck_goal": "Go wide"}


def test_corrupted_cache_file_is_ignored(tmp_path):
    path = tmp_path / "cache.json"
    path.write_text("not valid json{{{")
    cache = AnalysisCache(path=path)
    assert cache.get("abc") is None


def test_deck_cache_key_is_stable_regardless_of_dict_order():
    deck_a = Decklist(main_deck={"Sol Ring": 1, "Island": 4}, commander_zone={"Krenko": 1})
    deck_b = Decklist(main_deck={"Island": 4, "Sol Ring": 1}, commander_zone={"Krenko": 1})
    assert deck_cache_key(deck_a) == deck_cache_key(deck_b)


def test_deck_cache_key_differs_for_different_decks():
    deck_a = Decklist(main_deck={"Sol Ring": 1}, commander_zone={"Krenko": 1})
    deck_b = Decklist(main_deck={"Sol Ring": 2}, commander_zone={"Krenko": 1})
    assert deck_cache_key(deck_a) != deck_cache_key(deck_b)


def test_deck_cache_key_ignores_sideboard_and_considering_zones():
    deck_a = Decklist(main_deck={"Sol Ring": 1}, commander_zone={"Krenko": 1})
    deck_b = Decklist(
        main_deck={"Sol Ring": 1},
        commander_zone={"Krenko": 1},
        sideboard_zone={"Island": 1},
        considering_zone={"Mountain": 1},
    )
    assert deck_cache_key(deck_a) == deck_cache_key(deck_b)
