import requests
import json
from identifiers import CardIdentifier, dict_to_card_identifier
from copy import deepcopy
from pydantic import BaseModel

URL = "https://api.scryfall.com"
CARD_PARAMETER = "cards"
COLLECTION_PARAMETER = "collection"

USER_AGENT = "MagicDeckAnalyzer/0.1 (personal project)"
REQUEST_FORMAT = "application/json"

HEADERS = {
    "User-Agent": "MagicDeckAnalyzer/0.1 (personal project)",
    "Accept": "application/json",
}

class DeckContentFetcher:
    def __init__(
            self, 
            url: str=URL, 
            user_agent: str=USER_AGENT, 
            request_format: str=REQUEST_FORMAT
            ):
        self._url: str = url
        self._headers: dict[str, str] = {
            "User-Agent": user_agent,
            "Accept": request_format,
        }
        self.last_request: tuple[list[CardIdentifier], requests.models.Response] | None = None
        pass
    
    def get_last_request(self, do_print: bool=True) -> requests.models.Response | None:
        if do_print:
            print(self.last_request[0])
            print(json.dumps(self.last_request[1].json(), indent=2))
        return self.last_request
    
    def fetch_cards_infos(self, raw_deck_list_identifiers: list[CardIdentifier]):
        request_url = "/".join([self._url, CARD_PARAMETER, COLLECTION_PARAMETER])
        json_request = {"identifiers": [identifier.model_dump(mode="json") 
                                        for identifier in raw_deck_list_identifiers]}
        result = requests.post(request_url, headers=HEADERS, json = json_request)
        self.last_request = deepcopy(raw_deck_list_identifiers), result
        try:
            result.raise_for_status()
        finally:
            return result
        
if __name__ == "__main__":
    raw_identifiers = [
    {
      "id": "683a5707-cddb-494d-9b41-51b4584ded69"
    },
    {
      "name": "Ancient Tomb"
    },
    {
      "set": "mrd",
      "collector_number": "150"
    }
  ]
    identifiers = [dict_to_card_identifier(identifier) for identifier in raw_identifiers]
    fetcher = DeckContentFetcher()
    fetcher.fetch_cards_infos(identifiers)
    fetcher.get_last_request(do_print=True)