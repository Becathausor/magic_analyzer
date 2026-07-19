from fastapi.testclient import TestClient

from card import decklist_helper as decklist_helper_module
from webclient import server as server_module
from webclient.server import app


class FakeCardDatabase:
    def __init__(self):
        self._cards = {}
        self._not_found = set()
        self.fetch_missing_calls = []

    def fetch_missing(self, cardnames):
        self.fetch_missing_calls.append(set(cardnames))

    def get(self, cardname):
        return self._cards.get(cardname)

    def is_not_found(self, cardname):
        return cardname in self._not_found


class FakeCard:
    def __init__(self, image_url, category="Land", opposite_category=None):
        self._image_url = image_url
        self._category = category
        self._opposite_category = opposite_category

    def image_url(self):
        return self._image_url

    def categories(self):
        return (self._category, self._opposite_category)


def setup_app(tmp_path, monkeypatch):
    monkeypatch.setattr(server_module, "DECKLIST_FOLDER", tmp_path)
    monkeypatch.setattr(decklist_helper_module, "DECKLIST_FOLDER", tmp_path)
    fake_db = FakeCardDatabase()
    monkeypatch.setattr(server_module, "CARD_DATABASE", fake_db)
    return TestClient(app), fake_db


def test_list_decklists_returns_sorted_filenames(tmp_path, monkeypatch):
    client, _ = setup_app(tmp_path, monkeypatch)
    (tmp_path / "b.txt").write_text("1 Island\n")
    (tmp_path / "a.txt").write_text("1 Island\n")

    response = client.get("/api/decklists")

    assert response.status_code == 200
    assert response.json() == ["a.txt", "b.txt"]


def test_get_decklist_returns_parsed_zones(tmp_path, monkeypatch):
    client, _ = setup_app(tmp_path, monkeypatch)
    (tmp_path / "deck.txt").write_text("4 Island\n1 Wonder\n\nCommander:\n1 The Ancient One\n")

    response = client.get("/api/decklists/deck.txt")

    assert response.status_code == 200
    body = response.json()
    assert body["main_deck"] == [
        {"cardname": "Island", "quantity": 4},
        {"cardname": "Wonder", "quantity": 1},
    ]
    assert body["commander_zone"] == [{"cardname": "The Ancient One", "quantity": 1}]
    assert body["sideboard_zone"] == []
    assert body["considering_zone"] == []


def test_get_decklist_missing_file_returns_404(tmp_path, monkeypatch):
    client, _ = setup_app(tmp_path, monkeypatch)

    response = client.get("/api/decklists/does_not_exist.txt")

    assert response.status_code == 404


def test_get_decklist_path_traversal_returns_404_without_leaking_content(tmp_path, monkeypatch):
    client, _ = setup_app(tmp_path, monkeypatch)
    secret = tmp_path.parent / "secret.txt"
    secret.write_text("TOP SECRET")

    response = client.get("/api/decklists/..%2Fsecret.txt")

    assert response.status_code == 404
    assert "TOP SECRET" not in response.text


def test_get_decklist_malformed_content_returns_422(tmp_path, monkeypatch):
    client, _ = setup_app(tmp_path, monkeypatch)
    (tmp_path / "deck.txt").write_text("four Island\n")

    response = client.get("/api/decklists/deck.txt")

    assert response.status_code == 422


def test_get_card_returns_ready_with_image_url(tmp_path, monkeypatch):
    client, fake_db = setup_app(tmp_path, monkeypatch)
    fake_db._cards["Island"] = FakeCard(image_url="https://example.com/island.jpg", category="Land")

    response = client.get("/api/cards/Island")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "cardname": "Island",
        "image_url": "https://example.com/island.jpg",
        "category": "Land",
        "opposite_category": None,
    }


def test_list_decklists_prefetches_first_five_decks(tmp_path, monkeypatch):
    client, fake_db = setup_app(tmp_path, monkeypatch)
    for letter in "abcdefg":
        (tmp_path / f"{letter}.txt").write_text(f"1 Card{letter.upper()}\n")

    response = client.get("/api/decklists")

    assert response.status_code == 200
    assert response.json() == [f"{letter}.txt" for letter in "abcdefg"]
    prefetched = set().union(*fake_db.fetch_missing_calls)
    assert prefetched == {"CardA", "CardB", "CardC", "CardD", "CardE"}


def test_get_card_returns_fetching_when_unknown(tmp_path, monkeypatch):
    client, _ = setup_app(tmp_path, monkeypatch)

    response = client.get("/api/cards/Unknown Card")

    assert response.status_code == 202
    assert response.json() == {"status": "fetching", "cardname": "Unknown Card"}


def test_get_card_returns_not_found_for_known_bad_name(tmp_path, monkeypatch):
    client, fake_db = setup_app(tmp_path, monkeypatch)
    fake_db._not_found.add("Bad Card")

    response = client.get("/api/cards/Bad Card")

    assert response.status_code == 404
    assert response.json() == {"status": "not_found", "cardname": "Bad Card"}
