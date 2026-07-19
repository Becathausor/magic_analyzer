from fastapi.testclient import TestClient

from analyzer import AnalysisCache, DeckReport
from card import decklist_helper as decklist_helper_module
from webclient import app
from webclient import server as server_module


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
    monkeypatch.setattr(server_module, "ANALYSIS_CACHE", AnalysisCache(path=tmp_path / "analysis_cache.json"))
    monkeypatch.setattr(server_module, "_analysis_jobs", {})
    monkeypatch.setattr(server_module, "_analysis_errors", {})
    return TestClient(app), fake_db


def _fake_report() -> DeckReport:
    return DeckReport(
        archetypes=["Aggro"],
        ramp_count=1,
        ramp_cards=["Sol Ring"],
        removal_count=0,
        removal_cards=[],
        draw_count=0,
        draw_cards=[],
        deck_goal="Go wide with goblins.",
        average_setup_turn=5,
        win_conditions=["Krenko token army"],
        bracket=3,
        bracket_name="Upgraded",
        bracket_justification="Has some efficient cards but no Game Changers.",
    )


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


def test_get_analysis_returns_not_cached_when_absent(tmp_path, monkeypatch):
    client, _ = setup_app(tmp_path, monkeypatch)
    (tmp_path / "deck.txt").write_text("1 Sol Ring\n\nCommander:\n1 Krenko\n")

    response = client.get("/api/decklists/deck.txt/analysis")

    assert response.status_code == 200
    assert response.json() == {"status": "not_cached"}


def test_trigger_analysis_runs_in_background_then_reports_ready(tmp_path, monkeypatch):
    client, _ = setup_app(tmp_path, monkeypatch)
    (tmp_path / "deck.txt").write_text("1 Sol Ring\n\nCommander:\n1 Krenko\n")
    monkeypatch.setattr(server_module, "analyze_decklist", lambda deck: _fake_report())

    trigger_response = client.post("/api/decklists/deck.txt/analysis")
    assert trigger_response.status_code == 202
    assert trigger_response.json() == {"status": "pending"}

    poll_response = client.post("/api/decklists/deck.txt/analysis")
    assert poll_response.status_code == 200
    body = poll_response.json()
    assert body["status"] == "ready"
    assert body["report"]["deck_goal"] == "Go wide with goblins."
    assert body["report"]["bracket_name"] == "Upgraded"


def test_get_analysis_returns_cached_report_after_trigger(tmp_path, monkeypatch):
    client, _ = setup_app(tmp_path, monkeypatch)
    (tmp_path / "deck.txt").write_text("1 Sol Ring\n\nCommander:\n1 Krenko\n")
    monkeypatch.setattr(server_module, "analyze_decklist", lambda deck: _fake_report())
    client.post("/api/decklists/deck.txt/analysis")

    response = client.get("/api/decklists/deck.txt/analysis")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["report"]["archetypes"] == ["Aggro"]


def test_trigger_analysis_does_not_recall_pipeline_once_cached(tmp_path, monkeypatch):
    client, _ = setup_app(tmp_path, monkeypatch)
    (tmp_path / "deck.txt").write_text("1 Sol Ring\n\nCommander:\n1 Krenko\n")
    calls = []

    def fake_analyze(deck):
        calls.append(deck)
        return _fake_report()

    monkeypatch.setattr(server_module, "analyze_decklist", fake_analyze)
    client.post("/api/decklists/deck.txt/analysis")
    assert len(calls) == 1

    response = client.post("/api/decklists/deck.txt/analysis")

    assert response.json()["status"] == "ready"
    assert len(calls) == 1


def test_trigger_analysis_reports_error_and_allows_retry(tmp_path, monkeypatch):
    client, _ = setup_app(tmp_path, monkeypatch)
    (tmp_path / "deck.txt").write_text("1 Sol Ring\n\nCommander:\n1 Krenko\n")

    def raising_analyze(deck):
        raise RuntimeError("DEEPINFRA_API_KEY missing. Fill it in .env file.")

    monkeypatch.setattr(server_module, "analyze_decklist", raising_analyze)
    client.post("/api/decklists/deck.txt/analysis")

    error_response = client.post("/api/decklists/deck.txt/analysis")
    assert error_response.status_code == 200
    body = error_response.json()
    assert body["status"] == "error"
    assert "DEEPINFRA_API_KEY" in body["message"]

    monkeypatch.setattr(server_module, "analyze_decklist", lambda deck: _fake_report())
    retry_trigger = client.post("/api/decklists/deck.txt/analysis")
    assert retry_trigger.json() == {"status": "pending"}

    retry_poll = client.post("/api/decklists/deck.txt/analysis")
    assert retry_poll.json()["status"] == "ready"
