from datetime import datetime, timezone

from bson import ObjectId


def create_profile_document(user_id: ObjectId, preferences: dict) -> dict:
    """One stylist profile per user (unique index on user_id)."""
    now = datetime.now(timezone.utc)
    return {
        "user_id": user_id,
        "preferences": preferences,
        "created_at": now,
        "updated_at": now,
    }


def create_message_document(user_id: ObjectId, role: str, content: str) -> dict:
    """A single chat message, always scoped to one user."""
    return {
        "_id": ObjectId(),
        "user_id": user_id,
        "role": role,
        "content": content,
        "created_at": datetime.now(timezone.utc),
    }
