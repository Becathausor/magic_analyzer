"""Orchestrates classification + synthesis into a single DeckReport."""

from __future__ import annotations

import json
import logging
import sys

from card.card import Card
from card.card_database import CARD_DATABASE
from card.decklist import Decklist
from card.decklist_helper import DecklistBuilder
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import BaseTool

from .classification import classify_cards
from .schema import CardTag, DeckReport
from .synthesis import synthesize_report

logger = logging.getLogger(__name__)


def _deck_cards(deck: Decklist) -> list[Card]:
    cardnames = {*deck.main_deck, *deck.commander_zone}
    cards = []
    for cardname in cardnames:
        card = CARD_DATABASE.get(cardname)
        if card is None:
            logger.warning("Card not found in database, skipping from analysis: %s", cardname)
            continue
        cards.append(card)
    return cards


def _names_with_tag(tags: list[CardTag], flag_name: str) -> list[str]:
    return [tag.cardname for tag in tags if getattr(tag, flag_name)]


def analyze_decklist(
    deck: Decklist,
    *,
    chat_model: BaseChatModel | None = None,
    retriever_tool: BaseTool | None = None,
) -> DeckReport:
    """Classify every card then synthesize the full deck report."""
    cards = _deck_cards(deck)
    tags = classify_cards(cards, model=chat_model)

    commander_names = list(deck.commander_zone)
    synthesis = synthesize_report(commander_names, tags, model=chat_model, retriever_tool=retriever_tool)

    ramp_cards = _names_with_tag(tags, "is_ramp")
    removal_cards = _names_with_tag(tags, "is_removal")
    draw_cards = _names_with_tag(tags, "is_card_draw")

    return DeckReport(
        archetypes=synthesis.archetypes,
        ramp_count=len(ramp_cards),
        ramp_cards=ramp_cards,
        removal_count=len(removal_cards),
        removal_cards=removal_cards,
        draw_count=len(draw_cards),
        draw_cards=draw_cards,
        deck_goal=synthesis.deck_goal,
        average_setup_turn=synthesis.average_setup_turn,
        win_conditions=synthesis.win_conditions,
        bracket=synthesis.bracket,
        bracket_name=synthesis.bracket_name,
        bracket_justification=synthesis.bracket_justification,
    )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python -m analyzer.pipeline <decklist_filename>")
    deck = DecklistBuilder(commander_deck=True).build(sys.argv[1])
    report = analyze_decklist(deck)
    print(json.dumps(report.model_dump(), indent=2))
