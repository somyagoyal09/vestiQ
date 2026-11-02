# Purpose: Pydantic models for wardrobe item requests and responses
from datetime import datetime

from pydantic import BaseModel, Field


class ClothingCreate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=100,
    )

    category: str = Field(
        min_length=2,
        max_length=50,
    )

    color: str | None = Field(
        default=None,
        max_length=50,
    )


class ClothingResponse(BaseModel):
    id: str

    name: str

    category: str | None = None

    color: str | None = None

    image_url: str

    style: str | None = None

    outfit_weight: str | None = None

    occasion_tags: list[str] = Field(
        default_factory=list
    )

    domain: str | None = None

    prediction: dict | None = None

    created_at: datetime | None = None

    last_worn_at: datetime | None = None