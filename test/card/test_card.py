from card import Card


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


def test_categories_returns_land_for_plain_land():
    card = Card(cardname="Island", data={"type_line": "Basic Land — Island"})
    assert card.categories() == ("Land", None)


def test_categories_returns_creature_for_plain_creature():
    card = Card(cardname="Grizzly Bears", data={"type_line": "Creature — Bear"})
    assert card.categories() == ("Creature", None)


def test_categories_picks_creature_over_artifact_for_artifact_creature():
    card = Card(cardname="Ornithopter", data={"type_line": "Artifact Creature — Thopter"})
    assert card.categories() == ("Creature", None)


def test_categories_reports_differing_front_and_back_for_mdfc():
    card = Card(
        cardname="Sink into Stupor",
        data={
            "name": "Sink into Stupor // Soporific Springs",
            "card_faces": [
                {"name": "Sink into Stupor", "type_line": "Instant"},
                {"name": "Soporific Springs", "type_line": "Land"},
            ],
        },
    )
    assert card.categories() == ("Instant", "Land")


def test_categories_returns_none_for_back_when_both_faces_share_category():
    card = Card(
        cardname="Clearwater Pathway",
        data={
            "name": "Clearwater Pathway // Murkwater Pathway",
            "card_faces": [
                {"name": "Clearwater Pathway", "type_line": "Land"},
                {"name": "Murkwater Pathway", "type_line": "Land"},
            ],
        },
    )
    assert card.categories() == ("Land", None)
