import pathlib

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from card.card_database import CARD_DATABASE
from card.decklist_helper import DECKLIST_FOLDER, DecklistBuilder

STATIC_DIR = pathlib.Path(__file__).parent / "static"

app = FastAPI()


class CardRow(BaseModel):
    cardname: str
    quantity: int


class DecklistResponse(BaseModel):
    main_deck: list[CardRow]
    commander_zone: list[CardRow]
    sideboard_zone: list[CardRow]
    considering_zone: list[CardRow]


def _zone_to_rows(zone: dict[str, int]) -> list[CardRow]:
    return [CardRow(cardname=name, quantity=quantity) for name, quantity in zone.items()]


@app.get("/api/decklists")
def list_decklists() -> list[str]:
    return sorted(p.name for p in DECKLIST_FOLDER.iterdir() if p.is_file())


@app.get("/api/decklists/{filename}")
def get_decklist(filename: str, background_tasks: BackgroundTasks) -> DecklistResponse:
    target = (DECKLIST_FOLDER / filename).resolve()
    if not target.is_relative_to(DECKLIST_FOLDER.resolve()) or not target.is_file():
        raise HTTPException(status_code=404, detail="Decklist not found")

    try:
        deck = DecklistBuilder(commander_deck=True).build(filename, fetch_missing=False)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    all_cardnames = {
        *deck.main_deck,
        *deck.commander_zone,
        *deck.sideboard_zone,
        *deck.considering_zone,
    }
    background_tasks.add_task(CARD_DATABASE.fetch_missing, all_cardnames)

    return DecklistResponse(
        main_deck=_zone_to_rows(deck.main_deck),
        commander_zone=_zone_to_rows(deck.commander_zone),
        sideboard_zone=_zone_to_rows(deck.sideboard_zone),
        considering_zone=_zone_to_rows(deck.considering_zone),
    )


@app.get("/api/cards/{cardname}")
def get_card(cardname: str) -> JSONResponse:
    card = CARD_DATABASE.get(cardname)
    if card is not None:
        return JSONResponse({"status": "ready", "cardname": cardname, "image_url": card.image_url()})
    if CARD_DATABASE.is_not_found(cardname):
        return JSONResponse({"status": "not_found", "cardname": cardname}, status_code=404)
    return JSONResponse({"status": "fetching", "cardname": cardname}, status_code=202)


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
