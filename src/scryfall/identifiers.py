"""Card identifiers accepted by the Scryfall `/cards/collection` endpoint.

See https://scryfall.com/docs/api/cards/collection
"""

from __future__ import annotations

from typing import Union
from uuid import UUID

from pydantic import BaseModel, ValidationError


class ById(BaseModel):
    """Finds a card with the specified Scryfall id."""

    id: UUID


class ByMtgoId(BaseModel):
    """Finds a card with the specified mtgo_id or mtgo_foil_id."""

    mtgo_id: int


class ByMultiverseId(BaseModel):
    """Finds a card with the specified value among its multiverse_ids."""

    multiverse_id: int


class ByOracleId(BaseModel):
    """Finds the newest edition of cards with the specified oracle_id."""

    oracle_id: UUID


class ByIllustrationId(BaseModel):
    """Finds the preferred scans of cards with the specified illustration_id."""

    illustration_id: UUID


class ByName(BaseModel):
    """Finds the newest edition of a card with the specified name."""

    name: str


class ByNameAndSet(BaseModel):
    """Finds a card matching the specified name and set."""

    name: str
    set: str


class ByCollectorNumberAndSet(BaseModel):
    """Finds a card with the specified collector_number and set."""

    collector_number: str
    set: str

card_identifier_types: list[type[BaseModel]] = [ById,
    ByMtgoId,
    ByMultiverseId,
    ByOracleId,
    ByIllustrationId,
    ByNameAndSet,
    ByCollectorNumberAndSet,
    ByName,]

CardIdentifier = Union[*card_identifier_types]

_FIELD_SETS_TO_TYPE: dict[frozenset[str], type[BaseModel]] = {
    frozenset(model.model_fields): model for model in card_identifier_types
}


def dict_to_card_identifier(raw_identifier: dict) -> CardIdentifier:
    card_identifier_type = _FIELD_SETS_TO_TYPE.get(frozenset(raw_identifier))
    if card_identifier_type is None:
        valid_field_sets = [sorted(fields) for fields in _FIELD_SETS_TO_TYPE]
        raise ValueError(
            f"No card identifier type accepts exactly these fields: {sorted(raw_identifier)}. "
            f"Valid field combinations: {valid_field_sets}"
        )
    return card_identifier_type.model_validate(raw_identifier)