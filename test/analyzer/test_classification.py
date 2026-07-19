from analyzer.classification import classify_cards
from analyzer.schema import CardTag, CardTagBatch
from card.card import Card


class _FakeStructuredModel:
    def __init__(self, parent):
        self._parent = parent

    def invoke(self, messages):
        self._parent.calls.append(messages)
        return self._parent.batches.pop(0)


class FakeChatModel:
    def __init__(self, batches):
        self.batches = list(batches)
        self.calls = []

    def with_structured_output(self, schema):
        assert schema is CardTagBatch
        return _FakeStructuredModel(self)


def _card(name):
    return Card(cardname=name, data={"type_line": "Artifact", "mana_cost": "{1}", "oracle_text": ""})


def test_classify_cards_batches_and_aggregates_tags():
    cards = [_card("Card 0"), _card("Card 1"), _card("Card 2")]
    batch1 = CardTagBatch(tags=[CardTag(cardname="Card 0", is_ramp=True), CardTag(cardname="Card 1")])
    batch2 = CardTagBatch(tags=[CardTag(cardname="Card 2", is_removal=True)])
    model = FakeChatModel([batch1, batch2])

    tags = classify_cards(cards, model=model, batch_size=2)

    assert [tag.cardname for tag in tags] == ["Card 0", "Card 1", "Card 2"]
    assert tags[0].is_ramp is True
    assert tags[2].is_removal is True
    assert len(model.calls) == 2


def test_classify_cards_skips_failing_batch_and_continues(monkeypatch):
    cards = [_card("Card 0"), _card("Card 1")]

    class RaisingModel:
        def with_structured_output(self, schema):
            raise AssertionError("boom")

    tags = classify_cards(cards, model=RaisingModel(), batch_size=2)

    assert tags == []
