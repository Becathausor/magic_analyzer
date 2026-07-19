import pytest
import requests

from scryfall import fetcher as fetcher_module
from scryfall.fetcher import DeckContentFetcher
from scryfall.identifiers import dict_to_card_identifier


class FakeResponse:
    def __init__(self, json_data, raise_error=None):
        self._json_data = json_data
        self._raise_error = raise_error

    def json(self):
        return self._json_data

    def raise_for_status(self):
        if self._raise_error is not None:
            raise self._raise_error


def test_fetch_cards_infos_returns_the_http_response(monkeypatch):
    fake_response = FakeResponse({"data": [{"name": "Island"}], "not_found": []})
    monkeypatch.setattr(fetcher_module.requests, "post", lambda *a, **k: fake_response)

    fetcher = DeckContentFetcher()
    identifiers = [dict_to_card_identifier({"name": "Island"})]

    result = fetcher.fetch_cards_infos(identifiers)

    assert result is fake_response
    assert result.json() == {"data": [{"name": "Island"}], "not_found": []}


def test_fetch_cards_infos_stores_last_request_before_raising(monkeypatch):
    fake_response = FakeResponse({}, raise_error=requests.HTTPError("boom"))
    monkeypatch.setattr(fetcher_module.requests, "post", lambda *a, **k: fake_response)

    fetcher = DeckContentFetcher()
    identifiers = [dict_to_card_identifier({"name": "Island"})]

    with pytest.raises(requests.HTTPError):
        fetcher.fetch_cards_infos(identifiers)

    assert fetcher.last_request is not None
    stored_identifiers, stored_response = fetcher.last_request
    assert stored_identifiers == identifiers
    assert stored_response is fake_response
