from datetime import datetime, timezone

from bson import ObjectId


def create_user_document(
    name: str,
    email: str,
    password_hash: str | None = None,
    auth_provider: str = "password",
    provider_id: str | None = None,
) -> dict:
    """Create a Vestiq user document for MongoDB."""

    document = {
        "_id": ObjectId(),
        "name": name,
        "email": email.lower().strip(),
        "password_hash": password_hash,
        "auth_provider": auth_provider,
        "provider_id": provider_id,
        "profile_completed": False,
        "onboarding_completed": False,
        "gender": None,
        "clothing_preference": "both",
        "preferred_styles": [],
        "preferred_traditional_categories": [],
        "created_at": datetime.now(timezone.utc),
    }

    return document
