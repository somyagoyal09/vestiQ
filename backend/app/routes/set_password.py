from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.database.database_connection import get_database
from app.services.authentication import (
    get_current_user,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

MIN_PASSWORD_CHARACTERS = 8
# bcrypt only uses the first 72 bytes of a password. Longer input is rejected
# rather than silently truncated, so the saved password matches what the user typed.
BCRYPT_MAX_BYTES = 72


class SetPasswordPayload(BaseModel):
    new_password: str = Field(min_length=MIN_PASSWORD_CHARACTERS, max_length=128)
    current_password: str | None = Field(default=None, max_length=128)


def _check_bcrypt_length(password: str, label: str) -> None:
    if len(password.encode("utf-8")) > BCRYPT_MAX_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"{label} must be {BCRYPT_MAX_BYTES} bytes or fewer.",
        )


@router.post("/set-password")
def set_password(
    payload: SetPasswordPayload,
    current_user: dict = Depends(get_current_user),
):
    _check_bcrypt_length(payload.new_password, "New password")
    if payload.current_password:
        _check_bcrypt_length(payload.current_password, "Current password")

    database = get_database()
    stored = database.users.find_one({"_id": current_user["_id"]})
    if not stored:
        raise HTTPException(status_code=404, detail="User not found.")

    existing_hash = stored.get("password_hash")
    if existing_hash:
        # Accounts that already have a password must confirm it before changing it.
        if not payload.current_password or not verify_password(payload.current_password, existing_hash):
            raise HTTPException(status_code=400, detail="Current password is incorrect.")

    result = database.users.update_one(
        {"_id": stored["_id"]},
        {
            "$set": {
                "password_hash": hash_password(payload.new_password),
                "password_set_at": datetime.now(timezone.utc),
            }
        },
    )
    if result.matched_count != 1:
        raise HTTPException(status_code=404, detail="User not found.")

    return {
        "saved": True,
        "message": "Password saved. You can now log in with your email and password.",
    }