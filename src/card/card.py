from pydantic import BaseModel


class Card(BaseModel):
    cardname: str
    data: dict | None = None

    def image_url(self, size: str = "normal") -> str | None:
        if self.data is None:
            return None
        image_uris = self.data.get("image_uris")
        if image_uris and size in image_uris:
            return image_uris[size]
        faces = self.data.get("card_faces")
        if faces and faces[0].get("image_uris"):
            return faces[0]["image_uris"].get(size)
        return None