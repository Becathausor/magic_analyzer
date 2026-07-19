from card.card import Card


def test_image_url_returns_none_without_data():
    card = Card(cardname="Island")
    assert card.image_url() is None


def test_image_url_returns_top_level_image_uris():
    card = Card(cardname="Island", data={"image_uris": {"normal": "https://example.com/island.jpg"}})
    assert card.image_url() == "https://example.com/island.jpg"
    assert card.image_url("normal") == "https://example.com/island.jpg"


def test_image_url_returns_none_when_size_missing_and_no_faces():
    card = Card(cardname="Island", data={"image_uris": {"small": "https://example.com/island_small.jpg"}})
    assert card.image_url("normal") is None


def test_image_url_falls_back_to_front_face_for_double_faced_cards():
    card = Card(
        cardname="Delver of Secrets",
        data={
            "card_faces": [
                {"image_uris": {"normal": "https://example.com/front.jpg"}},
                {"image_uris": {"normal": "https://example.com/back.jpg"}},
            ]
        },
    )
    assert card.image_url() == "https://example.com/front.jpg"


def test_image_url_returns_none_without_image_uris_or_faces():
    card = Card(cardname="Mystery Card", data={"name": "Mystery Card"})
    assert card.image_url() is None
