from pydantic import BaseModel


class Card(BaseModel):
    cardname: str
    data: dict | None = None