from datetime import datetime, timezone
from bson import ObjectId


def _split_tags(value):
    if not value:
        return []

    if isinstance(value, list):
        return [
            str(item).strip().lower()
            for item in value
            if str(item).strip()
        ]

    return [
        item.strip().lower()
        for item in str(value).split(",")
        if item.strip()
    ]


def create_clothing_document(
    user_id: str,
    name: str,
    category: str,
    image_url: str,
    color: str | None = None,
    style: str | None = None,
    weight: str | None = None,
    formality: str | None = None,
    occasion_tags=None,
    weather_suitability=None,
    domain: str | None = None,
) -> dict:

    return {
        "_id": ObjectId(),
        "user_id": ObjectId(user_id),

        "name": name.strip(),
        "category": category.strip().lower(),
        "domain": domain.strip().lower() if domain else None,

        "color": color.strip().lower() if color else None,
        "image_url": image_url,

        "style": style.strip().lower() if style else None,

        # Keep both names compatible with the recommendation system.
        "weight": weight.strip().lower() if weight else None,
        "outfit_weight": weight.strip().lower() if weight else None,

        "formality": (
            formality.strip().lower()
            if formality
            else None
        ),

        "occasion_tags": _split_tags(occasion_tags),

        "weather_suitability": _split_tags(
            weather_suitability
        ),

        # AI prediction is intentionally not used as the source
        # of truth for manually entered wardrobe items.
        "prediction": None,

        "created_at": datetime.now(timezone.utc),
        "last_worn_at": None,
    }