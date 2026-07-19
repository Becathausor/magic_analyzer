from pydantic import BaseModel

CARD_TYPE_PRIORITY = [
    "Creature", "Planeswalker", "Battle", "Instant", "Sorcery", "Artifact", "Enchantment", "Land",
]
NON_CARD_TYPES = {"Legendary", "Basic", "Snow", "World", "Ongoing", "Elite", "Host"}


def _categorize_type_line(type_line: str) -> str:
    types = {t for t in type_line.split("—")[0].split() if t not in NON_CARD_TYPES}
    for category in CARD_TYPE_PRIORITY:
        if category in types:
            return category
    return "Other"


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

    def categories(self) -> tuple[str, str | None]:
        faces = self.data.get("card_faces") if self.data else None
        if faces and len(faces) >= 2 and "type_line" in faces[0] and "type_line" in faces[1]:
            front = _categorize_type_line(faces[0]["type_line"])
            back = _categorize_type_line(faces[1]["type_line"])
            return (front, back if back != front else None)
        type_line = (self.data or {}).get("type_line", "")
        return (_categorize_type_line(type_line), None)