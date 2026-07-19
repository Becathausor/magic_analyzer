import uuid

import pytest

from scryfall.identifiers import (
    ByCollectorNumberAndSet,
    ById,
    ByName,
    ByNameAndSet,
    dict_to_card_identifier,
)


def test_name_only_resolves_to_by_name():
    identifier = dict_to_card_identifier({"name": "Island"})
    assert isinstance(identifier, ByName)
    assert identifier.name == "Island"


def test_id_resolves_to_by_id():
    card_id = uuid.uuid4()
    identifier = dict_to_card_identifier({"id": str(card_id)})
    assert isinstance(identifier, ById)
    assert identifier.id == card_id


def test_collector_number_and_set_resolves_correctly():
    identifier = dict_to_card_identifier({"set": "mrd", "collector_number": "150"})
    assert isinstance(identifier, ByCollectorNumberAndSet)
    assert identifier.set == "mrd"
    assert identifier.collector_number == "150"


def test_name_and_set_resolves_correctly():
    identifier = dict_to_card_identifier({"name": "Island", "set": "mrd"})
    assert isinstance(identifier, ByNameAndSet)
    assert identifier.name == "Island"
    assert identifier.set == "mrd"


def test_unknown_field_combination_raises_value_error():
    with pytest.raises(ValueError):
        dict_to_card_identifier({"foo": "bar"})
