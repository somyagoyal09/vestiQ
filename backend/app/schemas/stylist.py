# Purpose: Pydantic models and limits for stylist preferences, chat and history

import base64
import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

MAX_ITEM_LENGTH = 40
MAX_LIST_ITEMS = 12

PREFERENCE_TOPICS = (
    "clothing_categories",
    "height_cm",
    "body_proportions",
    "preferred_fits",
    "favorite_colors",
    "advice_categories",
    "occasions",
    "budget",
    "comfort_notes",
    "dislikes",
)


def _clean_list(values) -> list[str]:
    if values is None:
        return []
    if isinstance(values, str):
        values = [values]

    cleaned = []
    seen = set()

    for value in values:
        item = str(value).strip()[:MAX_ITEM_LENGTH]
        key = item.lower()
        if item and key not in seen:
            cleaned.append(item)
            seen.add(key)

    return cleaned[:MAX_LIST_ITEMS]


class StylistPreferences(BaseModel):
    clothing_categories: list[str] = Field(default_factory=list)
    height_cm: int | None = Field(default=None, ge=100, le=250)
    body_proportions: str | None = Field(
        default=None, max_length=MAX_ITEM_LENGTH
    )
    preferred_fits: list[str] = Field(default_factory=list)
    favorite_colors: list[str] = Field(default_factory=list)
    advice_categories: list[str] = Field(default_factory=list)
    occasions: list[str] = Field(default_factory=list)
    budget: str | None = Field(default=None, max_length=60)
    comfort_notes: str | None = Field(default=None, max_length=300)
    dislikes: list[str] = Field(default_factory=list)
    skipped_topics: list[str] = Field(default_factory=list)

    @field_validator(
        "clothing_categories",
        "preferred_fits",
        "favorite_colors",
        "advice_categories",
        "occasions",
        "dislikes",
        mode="before",
    )
    @classmethod
    def normalize_lists(cls, value):
        return _clean_list(value)

    @field_validator("height_cm", mode="before")
    @classmethod
    def coerce_height(cls, value):
        if value is None or value == "":
            return None
        if isinstance(value, bool):
            raise ValueError("Height must be in centimetres.")
        if isinstance(value, float):
            return round(value)
        if isinstance(value, str):
            match = re.fullmatch(
                r"\s*(\d{2,3})(?:\.\d+)?\s*(?:cm)?\s*",
                value,
                re.IGNORECASE,
            )
            if not match:
                raise ValueError("Height must be in centimetres.")
            return int(match.group(1))
        return value

    @field_validator("skipped_topics", mode="before")
    @classmethod
    def normalize_skipped_topics(cls, value):
        return [
            topic
            for topic in _clean_list(value)
            if topic in PREFERENCE_TOPICS
        ]

    @field_validator(
        "body_proportions", "budget", "comfort_notes", mode="before"
    )
    @classmethod
    def blank_to_none(cls, value):
        if value is None:
            return None
        value = str(value).strip()
        return value or None


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    image_base64: str | None = Field(
        default=None, max_length=7_000_000
    )
    image_mime_type: str | None = Field(default=None, max_length=40)

    @field_validator("message")
    @classmethod
    def validate_message(cls, value):
        value = value.strip()
        if not value:
            raise ValueError("Message cannot be empty.")
        return value

    @field_validator("image_base64")
    @classmethod
    def validate_image_base64(cls, value):
        if value is None:
            return None
        try:
            decoded = base64.b64decode(value, validate=True)
        except (ValueError, TypeError) as exc:
            raise ValueError("Image data must be valid base64.") from exc

        if not decoded or len(decoded) > 5 * 1024 * 1024:
            raise ValueError("Image must be smaller than 5 MB.")
        return value

    @field_validator("image_mime_type")
    @classmethod
    def validate_image_mime_type(cls, value):
        if value is not None and value not in {
            "image/jpeg", "image/png", "image/webp"
        }:
            raise ValueError("Only JPEG, PNG, or WebP images are supported.")
        return value

    @field_validator("image_mime_type")
    @classmethod
    def require_mime_for_image(cls, value, info):
        if info.data.get("image_base64") and not value:
            raise ValueError(
                "Image MIME type is required when an image is attached."
            )
        return value


class ChatResponse(BaseModel):
    reply: str
    preferences: StylistPreferences
    preferences_updated: bool = False
    suggest_style_me: bool = False
    wardrobe_used: bool = False
    quick_replies: list[str] = Field(default_factory=list)


class HistoryMessage(BaseModel):
    role: str
    content: str
    created_at: datetime | None = None


class HistoryResponse(BaseModel):
    messages: list[HistoryMessage] = Field(default_factory=list)
