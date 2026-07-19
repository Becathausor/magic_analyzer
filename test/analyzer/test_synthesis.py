from analyzer import CardTag, DeckSynthesis, synthesize_report


def _synthesis(**overrides):
    payload = dict(
        archetypes=["Control"],
        deck_goal="Control the board then win with a big finisher.",
        average_setup_turn=7,
        win_conditions=["Big flier"],
        bracket=2,
        bracket_name="Core",
        bracket_justification="No Game Changers, no combos.",
    )
    payload.update(overrides)
    return DeckSynthesis(**payload)


def test_synthesize_report_returns_agent_structured_output():
    tags = [CardTag(cardname="Sol Ring", is_ramp=True), CardTag(cardname="Swords to Plowshares", is_removal=True)]
    captured = {}

    def fake_run_agent(user_message):
        captured["message"] = user_message
        return _synthesis()

    result = synthesize_report(["My Commander"], tags, run_agent=fake_run_agent)

    assert isinstance(result, DeckSynthesis)
    assert result.bracket == 2
    assert result.archetypes == ["Control"]
    assert "My Commander" in captured["message"]
    assert "Sol Ring: ramp" in captured["message"]
    assert "Swords to Plowshares: removal" in captured["message"]


def test_synthesize_report_forwards_agent_bracket():
    tags = [CardTag(cardname="Krenko", is_win_condition=True)]

    def fake_run_agent(_user_message):
        return _synthesis(bracket=3, bracket_name="Upgraded")

    result = synthesize_report([], tags, run_agent=fake_run_agent)

    assert result.bracket == 3
    assert result.bracket_name == "Upgraded"


def test_synthesize_report_mentions_no_commander_when_deck_has_none():
    captured = {}

    def fake_run_agent(user_message):
        captured["message"] = user_message
        return _synthesis()

    synthesize_report([], [], run_agent=fake_run_agent)

    assert "None (not a commander deck)" in captured["message"]
