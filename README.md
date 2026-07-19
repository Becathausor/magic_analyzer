# Deck analyzer

This project is willing to analyze Magic The Gathering (MTG) Commander decks. The database will use data from the [Scryfall API](https://api.scryfall.com). See documentation [here](https://scryfall.com/docs/api)

The analyze will be done through a transformer pipeline. Please inform your API key in a `.env` file.

## Running the web server

Install dependencies:

```
pip install -r requirements.txt
```

Start the FastAPI server:

```
cd src && uvicorn webclient.server:app --reload
```

Then open http://127.0.0.1:8000/ in your browser to pick a decklist from `data/decklists/` and browse its cards.

## Running tests

```
pytest
```

## License

This project is licensed under the [MIT License](LICENSE).