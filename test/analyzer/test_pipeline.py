from analyzer import CardTag, DeckSynthesis
from analyzer import pipeline as pipeline_module
from card import Card, Decklist


def _card(name):
    return Card(cardname=name, data={})


def test_analyze_decklist_combines_classification_and_synthesis(monkeypatch):
    deck = Decklist(
        main_deck={"Sol Ring": 1, "Swords to Plowshares": 1, "Island": 1},
        commander_zone={"Krenko": 1},
    )

    cards_by_name = {
        "Sol Ring": _card("Sol Ring"),
        "Swords to Plowshares": _card("Swords to Plowshares"),
        "Island": _card("Island"),
        "Krenko": _card("Krenko"),
    }

    class FakeDatabase:
        def get(self, cardname):
            return cards_by_name.get(cardname)

    monkeypatch.setattr(pipeline_module, "CARD_DATABASE", FakeDatabase())

    tags = [
        CardTag(cardname="Sol Ring", is_ramp=True),
        CardTag(cardname="Swords to Plowshares", is_removal=True),
        CardTag(cardname="Island"),
        CardTag(cardname="Krenko", is_win_condition=True),
    ]

    def fake_classify_cards(cards, *, model=None):
        assert {c.cardname for c in cards} == set(cards_by_name)
        return tags

    def fake_synthesize_report(commander_names, tagged_cards, *, model=None, retriever_tool=None):
        assert commander_names == ["Krenko"]
        assert tagged_cards == tags
        return DeckSynthesis(
            archetypes=["Aggro"],
            deck_goal="Go wide with goblins.",
            average_setup_turn=5,
            win_conditions=["Krenko token army"],
            bracket=3,
            bracket_name="Upgraded",
            bracket_justification="Has some efficient cards but no Game Changers.",
        )

    monkeypatch.setattr(pipeline_module, "classify_cards", fake_classify_cards)
    monkeypatch.setattr(pipeline_module, "synthesize_report", fake_synthesize_report)

    report = pipeline_module.analyze_decklist(deck)

    assert report.ramp_count == 1
    assert report.ramp_cards == ["Sol Ring"]
    assert report.removal_count == 1
    assert report.removal_cards == ["Swords to Plowshares"]
    assert report.draw_count == 0
    assert report.archetypes == ["Aggro"]
    assert report.bracket == 3
    assert report.bracket_name == "Upgraded"


def test_analyze_decklist_skips_cards_missing_from_database(monkeypatch):
    deck = Decklist(main_deck={"Known Card": 1, "Unknown Card": 1}, commander_zone={})

    class FakeDatabase:
        def get(self, cardname):
            return _card("Known Card") if cardname == "Known Card" else None

    monkeypatch.setattr(pipeline_module, "CARD_DATABASE", FakeDatabase())

    seen_cardnames = []

    def fake_classify_cards(cards, *, model=None):
        seen_cardnames.extend(c.cardname for c in cards)
        return [CardTag(cardname="Known Card")]

    def fake_synthesize_report(commander_names, tagged_cards, *, model=None, retriever_tool=None):
        return DeckSynthesis(
            archetypes=[],
            deck_goal="",
            average_setup_turn=0,
            win_conditions=[],
            bracket=1,
            bracket_name="Exhibition",
            bracket_justification="",
        )

    monkeypatch.setattr(pipeline_module, "classify_cards", fake_classify_cards)
    monkeypatch.setattr(pipeline_module, "synthesize_report", fake_synthesize_report)

    pipeline_module.analyze_decklist(deck)

    assert seen_cardnames == ["Known Card"]
