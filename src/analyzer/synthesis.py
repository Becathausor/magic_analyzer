"""Synthesis step: a tool-calling agent turns the tagged decklist into a DeckSynthesis.

The agent can call two tools: a RAG search over data/knowledge/ (rules, glossary,
archetypes, WotC brackets) and a direct card lookup, in case it wants to re-read a
specific card's oracle text before deciding on an archetype or a bracket. Structured
output is handled natively by langchain's create_agent via response_format.
"""

from __future__ import annotations

from typing import Callable

from card import CARD_DATABASE
from langchain.agents import create_agent
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import BaseTool, tool

from .langchain_client import get_chat_model
from .rag import get_rules_search_tool
from .schema import CardTag, DeckSynthesis

SYSTEM_PROMPT = """You are a Magic: The Gathering Commander deck analyst.

You are given a decklist with its commander(s) and, for each card, tags computed \
from its oracle text (ramp, removal, card draw, win condition). Use the \
`search_mtg_rules_and_brackets` tool to consult the glossary, archetype vocabulary \
and the WotC Commander Bracket (1 to 5) definitions before you commit to an answer, \
especially for the bracket. Use `get_card_info` if you need to re-read a specific \
card's oracle text."""


@tool
def get_card_info(cardname: str) -> str:
    """Look up a card's mana cost, type line and oracle text by exact name."""
    card = CARD_DATABASE.get(cardname)
    if card is None:
        return f"Card not found: {cardname}"
    data = card.data or {}
    return f"{cardname} | {data.get('mana_cost', '')} | {data.get('type_line', '')}\n{data.get('oracle_text', '')}"


def _tag_line(tag: CardTag) -> str:
    labels = [
        label
        for label, flag in (
            ("ramp", tag.is_ramp),
            ("removal", tag.is_removal),
            ("draw", tag.is_card_draw),
            ("win condition", tag.is_win_condition),
        )
        if flag
    ]
    label_text = ", ".join(labels) if labels else "no tag"
    note = f" — {tag.note}" if tag.note else ""
    return f"- {tag.cardname}: {label_text}{note}"


def _default_run_agent(model: BaseChatModel, tools: list[BaseTool]) -> Callable[[str], DeckSynthesis]:
    agent = create_agent(model, tools, system_prompt=SYSTEM_PROMPT, response_format=DeckSynthesis)

    def run(user_message: str) -> DeckSynthesis:
        result = agent.invoke({"messages": [{"role": "user", "content": user_message}]})
        structured = result.get("structured_response")
        if structured is None:
            # The model occasionally ends its turn without calling the structured
            # output tool; nudge it once instead of failing outright.
            result = agent.invoke({
                "messages": result["messages"] + [{
                    "role": "user",
                    "content": "Provide your final answer now as a DeckSynthesis structured response.",
                }],
            })
            structured = result.get("structured_response")
        if structured is None:
            raise RuntimeError("Synthesis agent did not return a structured DeckSynthesis response.")
        return structured

    return run


def synthesize_report(
    commander_names: list[str],
    tagged_cards: list[CardTag],
    *,
    model: BaseChatModel | None = None,
    retriever_tool: BaseTool | None = None,
    run_agent: Callable[[str], DeckSynthesis] | None = None,
) -> DeckSynthesis:
    """Run the synthesis agent over the tagged decklist and return a DeckSynthesis."""
    commander_line = ", ".join(commander_names) if commander_names else "None (not a commander deck)"
    deck_summary = "\n".join(_tag_line(tag) for tag in tagged_cards)
    user_message = (
        f"Commander(s): {commander_line}\n\nDeck cards with classification tags:\n{deck_summary}\n\n"
        "Analyze this deck."
    )

    if run_agent is None:
        model = model or get_chat_model()
        tools = [retriever_tool or get_rules_search_tool(), get_card_info]
        run_agent = _default_run_agent(model, tools)

    return run_agent(user_message)
