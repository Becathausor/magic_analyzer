from card.card_database import CardDatabase
from scryfall.cache import ScryfallCache


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


class FakeFetcher:
    def __init__(self, payload):
        self._payload = payload

    def fetch_cards_infos(self, identifiers):
        return FakeResponse(self._payload)


class RaisingFetcher:
    def fetch_cards_infos(self, identifiers):
        raise AssertionError("network fetcher should not be called")


class FailingFetcher:
    def fetch_cards_infos(self, identifiers):
        raise ConnectionError("network unreachable")


def make_database(tmp_path):
    return CardDatabase(cache=ScryfallCache(path=tmp_path / "cache.json"))


def test_get_returns_none_for_never_fetched_card(tmp_path):
    db = make_database(tmp_path)
    assert db.get("Island") is None


def test_fetch_missing_populates_card_from_fetcher(tmp_path):
    db = make_database(tmp_path)
    fetcher = FakeFetcher({"data": [{"name": "Island", "id": "abc"}], "not_found": []})

    db.fetch_missing(["Island"], fetcher=fetcher)

    card = db.get("Island")
    assert card is not None
    assert card.cardname == "Island"
    assert card.data == {"name": "Island", "id": "abc"}


def test_fetch_missing_serves_from_disk_cache_without_network(tmp_path):
    cache_path = tmp_path / "cache.json"
    first_db = CardDatabase(cache=ScryfallCache(path=cache_path))
    first_db.fetch_missing(
        ["Island"], fetcher=FakeFetcher({"data": [{"name": "Island", "id": "abc"}], "not_found": []})
    )

    second_db = CardDatabase(cache=ScryfallCache(path=cache_path))
    second_db.fetch_missing(["Island"], fetcher=RaisingFetcher())

    card = second_db.get("Island")
    assert card is not None
    assert card.data == {"name": "Island", "id": "abc"}


def test_fetch_missing_matches_double_faced_card_by_front_face_name(tmp_path):
    db = make_database(tmp_path)
    fetcher = FakeFetcher({
        "data": [{
            "name": "Clearwater Pathway // Murkwater Pathway",
            "id": "abc",
            "card_faces": [{"name": "Clearwater Pathway"}, {"name": "Murkwater Pathway"}],
        }],
        "not_found": [],
    })

    db.fetch_missing(["Clearwater Pathway"], fetcher=fetcher)

    card = db.get("Clearwater Pathway")
    assert card is not None
    assert card.cardname == "Clearwater Pathway"
    assert card.data["name"] == "Clearwater Pathway // Murkwater Pathway"


def test_fetch_missing_serves_double_faced_card_from_disk_cache_without_network(tmp_path):
    cache_path = tmp_path / "cache.json"
    first_db = CardDatabase(cache=ScryfallCache(path=cache_path))
    first_db.fetch_missing(
        ["Clearwater Pathway"],
        fetcher=FakeFetcher({
            "data": [{
                "name": "Clearwater Pathway // Murkwater Pathway",
                "id": "abc",
                "card_faces": [{"name": "Clearwater Pathway"}, {"name": "Murkwater Pathway"}],
            }],
            "not_found": [],
        }),
    )

    second_db = CardDatabase(cache=ScryfallCache(path=cache_path))
    second_db.fetch_missing(["Clearwater Pathway"], fetcher=RaisingFetcher())

    card = second_db.get("Clearwater Pathway")
    assert card is not None
    assert card.data["name"] == "Clearwater Pathway // Murkwater Pathway"


def test_fetch_missing_marks_not_found_cards(tmp_path):
    db = make_database(tmp_path)
    fetcher = FakeFetcher({"data": [], "not_found": [{"name": "Bad Card"}]})

    db.fetch_missing(["Bad Card"], fetcher=fetcher)

    assert db.is_not_found("Bad Card") is True
    assert db.get("Bad Card") is None


def test_repeated_fetch_missing_keeps_not_found_state(tmp_path):
    db = make_database(tmp_path)
    db.fetch_missing(["Bad Card"], fetcher=FakeFetcher({"data": [], "not_found": [{"name": "Bad Card"}]}))

    db.fetch_missing(["Bad Card"], fetcher=RaisingFetcher())

    assert db.is_not_found("Bad Card") is True
    assert db.get("Bad Card") is None


def test_fetch_missing_survives_network_failure_and_stays_retryable(tmp_path):
    db = make_database(tmp_path)

    db.fetch_missing(["Island"], fetcher=FailingFetcher())

    assert db.get("Island") is None
    assert db.is_not_found("Island") is False
