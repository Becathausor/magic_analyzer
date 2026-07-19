from __future__ import annotations

from pydantic import BaseModel, Field


class CardTag(BaseModel):
    cardname: str
    is_ramp: bool = False
    is_removal: bool = False
    is_card_draw: bool = False
    is_win_condition: bool = False
    note: str = Field(default="", description="Short justification, e.g. combo piece, board wipe, voltron target")


class CardTagBatch(BaseModel):
    tags: list[CardTag]


class DeckSynthesis(BaseModel):
    archetypes: list[str]
    deck_goal: str
    average_setup_turn: int
    win_conditions: list[str]
    bracket: int
    bracket_name: str
    bracket_justification: str


class DeckReport(BaseModel):
    archetypes: list[str]
    ramp_count: int
    ramp_cards: list[str]
    removal_count: int
    removal_cards: list[str]
    draw_count: int
    draw_cards: list[str]
    deck_goal: str
    average_setup_turn: int
    win_conditions: list[str]
    bracket: int
    bracket_name: str
    bracket_justification: str
