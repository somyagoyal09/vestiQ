from datetime import datetime, timedelta, timezone

from bson import ObjectId
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.configuration import settings
from app.database.database_connection import get_database

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
http_bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_context.verify(password, password_hash)


def create_access_token(user_id: str) -> str:
    expiration_time = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": user_id, "exp": expiration_time}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def is_onboarding_completed(user: dict) -> bool:
    """Database is the source of truth. Legacy users without the field are
    treated as completed when they already have a saved profile."""
    flag = user.get("onboarding_completed")
    if flag is not None:
        return bool(flag)
    return bool(user.get("profile_completed") or user.get("gender") or user.get("style_profile"))


def serialize_user(user: dict) -> dict:
    return {
        "id": str(user["_id"]),
        "name": user.get("name", ""),
        "email": user.get("email", ""),
        "profile_completed": user.get("profile_completed", False),
        "onboarding_completed": is_onboarding_completed(user),
        "gender": user.get("gender"),
        "clothing_preference": user.get("clothing_preference", "both"),
        "preferred_styles": user.get("preferred_styles", []),
        "preferred_traditional_categories": user.get("preferred_traditional_categories", []),
    }


def _serialize_current_user(user: dict) -> dict:
    return {
        "_id": user["_id"],
        "id": str(user["_id"]),
        "name": user.get("name", ""),
        "email": user.get("email", ""),
        "profile_completed": user.get("profile_completed", False),
        "onboarding_completed": is_onboarding_completed(user),
        "gender": user.get("gender"),
        "clothing_preference": user.get("clothing_preference", "both"),
        "preferred_styles": user.get("preferred_styles", []),
        "preferred_traditional_categories": user.get("preferred_traditional_categories", []),
    }


def _get_demo_user():
    database = get_database()
    demo_email = settings.DEMO_USER_EMAIL.lower().strip()
    if not demo_email:
        raise HTTPException(status_code=500, detail="DEMO_USER_EMAIL is not configured.")
    user = database.users.find_one({"email": demo_email})
    if not user:
        raise HTTPException(status_code=500, detail="Demo user not found.")
    return _serialize_current_user(user)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(http_bearer),
):
    # Demo mode remains available when a protected request has no token.
    # If a real Bearer token is supplied, validate it even while demo mode is enabled.
    if credentials is None:
        if settings.DISABLE_AUTH:
            return _get_demo_user()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate authentication credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        user_id = payload.get("sub")
        if not user_id:
            raise credentials_exception
        try:
            object_id = ObjectId(user_id)
        except Exception:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    database = get_database()
    user = database.users.find_one({"_id": object_id})
    if not user:
        raise credentials_exception
    return _serialize_current_user(user)
