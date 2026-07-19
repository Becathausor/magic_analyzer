"""Deterministic, batched classification of cards into ramp/removal/draw/win-condition tags."""

from __future__ import annotations

import logging

from card.card import Card
from langchain_core.language_models.chat_models import BaseChatModel

from .langchain_client import get_chat_model
from .schema import CardTag, CardTagBatch

logger = logging.getLogger(__name__)

DEFAULT_BATCH_SIZE = 15

SYSTEM_PROMPT = (
    "You are a Magic: The Gathering Commander deck analyst. For each card below, "
    "decide whether it is ramp, removal, card draw and/or a win condition, following "
    "the definitions of these categories from your MTG knowledge. A card can belong "
    "to several categories, or none. Keep the note field short (max one sentence)."
)


def _card_context(card: Card) -> str:
    data = card.data or {}
    type_line = data.get("type_line", "")
    mana_cost = data.get("mana_cost", "")
    oracle_text = data.get("oracle_text")
    if oracle_text is None:
        faces = data.get("card_faces") or []
        oracle_text = " // ".join(face.get("oracle_text", "") for face in faces)
    return f"- {card.cardname} | {mana_cost} | {type_line}\n  {oracle_text}"


def _classify_batch(cards: list[Card], model: BaseChatModel) -> list[CardTag]:
    prompt = "Classify these cards:\n\n" + "\n".join(_card_context(card) for card in cards)
    structured_model = model.with_structured_output(CardTagBatch)
    result = structured_model.invoke([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ])
    return result.tags


def classify_cards(
    cards: list[Card],
    *,
    model: BaseChatModel | None = None,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> list[CardTag]:
    """Classify every card into ramp/removal/draw/win-condition tags, batching LLM calls."""
    model = model or get_chat_model()
    tags: list[CardTag] = []
    for i in range(0, len(cards), batch_size):
        batch = cards[i:i + batch_size]
        try:
            tags.extend(_classify_batch(batch, model))
        except Exception:
            logger.exception("Card classification failed for batch starting at index %d", i)
    return tags
