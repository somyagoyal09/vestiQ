from datetime import datetime, timezone
import secrets
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field

from app.database.database_connection import get_database
from app.models.user import create_user_document
from app.schemas.user import UserRegister, UserResponse, UserProfileUpdate
from app.services.authentication import (
    create_access_token,
    hash_password,
    verify_password,
    get_current_user,
    is_onboarding_completed,
)
from app.core.configuration import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])


def serialize_user(user: dict) -> dict:
    """Return only safe, frontend-facing user profile fields."""
    return {
        "id": str(user["_id"]),
        "name": user.get("name", ""),
        "email": user.get("email", ""),
        "profile_completed": user.get("profile_completed", False),
        "onboarding_completed": is_onboarding_completed(user),
        "style_profile": user.get("style_profile"),
        "age_group": user.get("age_group"),
        "gender": user.get("gender"),
        "clothing_preference": user.get("clothing_preference", "both"),
        "preferred_styles": user.get("preferred_styles", []),
        "preferred_occasions": user.get("preferred_occasions", []),
        "clothing_interests": user.get("clothing_interests", []),
        "preferred_colors": user.get("preferred_colors", []),
        "styling_approach": user.get("styling_approach", []),
        "preferred_traditional_categories": user.get("preferred_traditional_categories", []),
    }


def _oauth_error(message: str) -> RedirectResponse:
    url = f"{settings.FRONTEND_URL.rstrip('/')}?oauth_error={urlencode({'': message})[1:]}"
    return RedirectResponse(url=url, status_code=302)


def _frontend_error(message: str) -> RedirectResponse:
    from urllib.parse import quote
    return RedirectResponse(
        url=f"{settings.FRONTEND_URL.rstrip('/')}?oauth_error={quote(message)}",
        status_code=302,
    )


def _set_oauth_state(response: RedirectResponse, state: str) -> None:
    response.set_cookie(
        key="vestiq_oauth_state",
        value=state,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=600,
    )


def _validate_state(request: Request, state: str | None) -> None:
    stored_state = request.cookies.get("vestiq_oauth_state")
    if not state or not stored_state or not secrets.compare_digest(state, stored_state):
        raise HTTPException(status_code=400, detail="OAuth state validation failed.")



def _finish_oauth(
    response: RedirectResponse,
    user: dict,
) -> RedirectResponse:
    token = create_access_token(str(user["_id"]))
    response.set_cookie(
        key="vestiq_oauth_state",
        value="",
        expires=0,
        httponly=True,
        secure=False,
        samesite="lax",
    )
    response.headers["Location"] = (
        f"{settings.FRONTEND_URL.rstrip('/')}#token={token}"
    )
    return response


def _find_or_create_oauth_user(
    *,
    name: str,
    email: str,
    provider: str,
    provider_id: str,
) -> dict:
    database = get_database()
    clean_email = email.lower().strip()

    user = database.users.find_one({"email": clean_email})

    if user:
        database.users.update_one(
            {"_id": user["_id"]},
            {"$set": {"auth_provider": provider, "provider_id": provider_id}},
        )
        return database.users.find_one({"_id": user["_id"]})

    user_document = create_user_document(
        name=name or clean_email.split("@")[0],
        email=clean_email,
        password_hash=None,
        auth_provider=provider,
        provider_id=provider_id,
    )
    database.users.insert_one(user_document)
    return user_document


# =========================================================
# REGISTER
# =========================================================

@router.post("/register", response_model=UserResponse)
def register_user(user: UserRegister):
    database = get_database()
    existing_user = database.users.find_one({"email": user.email.lower().strip()})
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is already registered.")

    password_hash = hash_password(user.password)
    user_document = create_user_document(
        name=user.name,
        email=user.email,
        password_hash=password_hash,
        auth_provider="password",
    )
    database.users.insert_one(user_document)
    return serialize_user(user_document)


# =========================================================
# LOGIN
# =========================================================

@router.post("/login")
def login_user(form_data: OAuth2PasswordRequestForm = Depends()):
    database = get_database()
    existing_user = database.users.find_one({"email": form_data.username.lower().strip()})
    if not existing_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")

    if not existing_user.get("password_hash") or not verify_password(form_data.password, existing_user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")

    access_token = create_access_token(str(existing_user["_id"]))
    return {"access_token": access_token, "token_type": "bearer", "user": serialize_user(existing_user)}


# =========================================================
# GOOGLE OAUTH
# =========================================================

@router.get("/google")
def google_login(response: Response):
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=503, detail="Google OAuth is not configured.")

    state = secrets.token_urlsafe(32)
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "online",
        "prompt": "select_account",
    }
    redirect = RedirectResponse(
        url="https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params),
        status_code=302,
    )
    _set_oauth_state(redirect, state)
    return redirect


@router.get("/google/callback")
async def google_callback(request: Request, code: str | None = None, state: str | None = None, error: str | None = None):
    if error:
        return _frontend_error(f"Google login cancelled: {error}")

    try:
        _validate_state(request, state)
        if not code:
            raise HTTPException(status_code=400, detail="Google did not return an authorization code.")

        async with httpx.AsyncClient(timeout=15) as client:
            token_response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                    "grant_type": "authorization_code",
                },
            )
            token_response.raise_for_status()
            tokens = token_response.json()

            user_response = await client.get(
                "https://openidconnect.googleapis.com/v1/userinfo",
                headers={"Authorization": f"Bearer {tokens['access_token']}"},
            )
            user_response.raise_for_status()
            profile = user_response.json()

        email = profile.get("email")
        provider_id = profile.get("sub")
        if not email or not provider_id:
            raise HTTPException(status_code=400, detail="Google account did not provide the required profile information.")

        user = _find_or_create_oauth_user(
            name=profile.get("name", ""),
            email=email,
            provider="google",
            provider_id=provider_id,
        )
        return _finish_oauth(RedirectResponse(url=settings.FRONTEND_URL, status_code=302), user)

    except HTTPException as exc:
        return _frontend_error(exc.detail)
    except Exception:
        return _frontend_error("Google login could not be completed.")


# =========================================================
# INSTAGRAM OAUTH
# =========================================================

@router.get("/instagram")
def instagram_login():
    if not settings.INSTAGRAM_CLIENT_ID or not settings.INSTAGRAM_CLIENT_SECRET:
        raise HTTPException(status_code=503, detail="Instagram OAuth is not configured.")

    state = secrets.token_urlsafe(32)
    params = {
        "client_id": settings.INSTAGRAM_CLIENT_ID,
        "redirect_uri": settings.INSTAGRAM_REDIRECT_URI,
        "response_type": "code",
        "scope": "instagram_business_basic",
        "state": state,
        "enable_fb_login": "0",
    }
    redirect = RedirectResponse(
        url="https://www.instagram.com/oauth/authorize?" + urlencode(params),
        status_code=302,
    )
    _set_oauth_state(redirect, state)
    return redirect


@router.get("/instagram/callback")
async def instagram_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    error_reason: str | None = None,
    error_description: str | None = None,
):
    if error:
        detail = error_description or error_reason or error
        return _frontend_error(f"Instagram login cancelled: {detail}")

    try:
        _validate_state(request, state)
        if not code:
            raise HTTPException(status_code=400, detail="Instagram did not return an authorization code.")

        async with httpx.AsyncClient(timeout=15) as client:
            token_response = await client.post(
                "https://api.instagram.com/oauth/access_token",
                data={
                    "client_id": settings.INSTAGRAM_CLIENT_ID,
                    "client_secret": settings.INSTAGRAM_CLIENT_SECRET,
                    "grant_type": "authorization_code",
                    "redirect_uri": settings.INSTAGRAM_REDIRECT_URI,
                    "code": code,
                },
            )
            token_response.raise_for_status()
            tokens = token_response.json()

            access_token = tokens.get("access_token")
            provider_id = tokens.get("user_id")
            if not access_token or not provider_id:
                raise HTTPException(status_code=400, detail="Instagram did not return the required account information.")

            profile_response = await client.get(
                f"https://graph.instagram.com/{settings.INSTAGRAM_GRAPH_VERSION}/me",
                params={
                    "fields": "id,username,name",
                    "access_token": access_token,
                },
            )
            profile_response.raise_for_status()
            profile = profile_response.json()

        provider_id = str(profile.get("id") or provider_id)
        username = profile.get("username") or f"instagram_{provider_id}"
        name = profile.get("name") or username

        # Instagram Login does not provide an email address in this flow.
        # Vestiq still needs a unique email-shaped identifier for its user schema.
        email = f"instagram_{provider_id}@oauth.vestiq.local"

        user = _find_or_create_oauth_user(
            name=name,
            email=email,
            provider="instagram",
            provider_id=provider_id,
        )
        return _finish_oauth(RedirectResponse(url=settings.FRONTEND_URL, status_code=302), user)

    except HTTPException as exc:
        return _frontend_error(exc.detail)
    except Exception:
        return _frontend_error("Instagram login could not be completed.")


# =========================================================
# GET CURRENT USER
# =========================================================

@router.get("/me", response_model=UserResponse)
def get_my_profile(current_user: dict = Depends(get_current_user)):
    return serialize_user(current_user)


# =========================================================
# SAVE / UPDATE PERSONALIZATION PROFILE
# =========================================================

@router.patch("/profile", response_model=UserResponse)
def update_profile(profile: UserProfileUpdate, current_user: dict = Depends(get_current_user)):
    database = get_database()

    allowed_genders = {"female", "male", "other", "prefer_not_to_say"}
    allowed_preferences = {"western", "traditional", "both"}
    if profile.gender and profile.gender not in allowed_genders:
        raise HTTPException(status_code=400, detail="Invalid gender selection.")
    if profile.clothing_preference not in allowed_preferences:
        raise HTTPException(status_code=400, detail="Invalid clothing preference.")

    def clean_list(values, allowed=None):
        cleaned = []
        for value in values or []:
            value = str(value).strip().lower()
            if value and (allowed is None or value in allowed) and value not in cleaned:
                cleaned.append(value)
        return cleaned

    allowed_styles = {
        "casual", "minimal", "elegant", "traditional", "modern", "classic",
        "trendy", "bold", "formal", "street", "a bit of everything"
    }
    allowed_occasions = {
        "college", "office", "family events", "parties", "weddings", "everyday", "travel"
    }
    allowed_clothing = {
        "tops", "shirts", "t-shirts", "jeans", "trousers", "dresses", "kurtis",
        "sarees", "ethnic sets", "skirts", "jackets", "co-ords", "hoodies"
    }
    allowed_colors = {"black", "white", "pastels", "earthy", "bright", "neutrals"}
    allowed_approaches = {
        "keep it clean", "layer & experiment", "accessorize everything",
        "mix & match", "go bold"
    }
    allowed_traditional_categories = {
        "saree", "lehenga", "anarkali", "kurti", "salwar_suit", "sharara", "gharara",
        "palazzo_suit", "kurta", "kurta_pajama", "dhoti", "dhoti_pants", "sherwani",
        "nehru_jacket", "achkan", "bandhgala", "pathani_suit", "indo_western", "other",
    }

    update = {
        "profile_completed": True,
        "age_group": profile.age_group,
        "gender": profile.gender,
        "clothing_preference": profile.clothing_preference,
        "preferred_styles": clean_list(profile.preferred_styles, allowed_styles),
        "preferred_occasions": clean_list(profile.preferred_occasions, allowed_occasions),
        "clothing_interests": clean_list(profile.clothing_interests, allowed_clothing),
        "preferred_colors": clean_list(profile.preferred_colors, allowed_colors),
        "styling_approach": clean_list(profile.styling_approach, allowed_approaches),
        "preferred_traditional_categories": clean_list(profile.preferred_traditional_categories, allowed_traditional_categories),
    }

    database.users.update_one(
        {"_id": current_user["_id"]},
        {"$set": update},
    )

    updated_user = database.users.find_one({"_id": current_user["_id"]})
    return serialize_user(updated_user)



# =========================================================
# VESTIQ STYLE PROFILE + DAILY MOOD
# =========================================================

class StyleProfilePayload(BaseModel):
    name: str = Field(default="", max_length=100)
    vibes: list[str] = Field(default_factory=list)
    occasions: list[str] = Field(default_factory=list)
    clothing: list[str] = Field(default_factory=list)
    palette: list[str] = Field(default_factory=list)

class MoodPayload(BaseModel):
    mood: str = Field(min_length=1, max_length=80)

_ALLOWED_MOODS = {
    "Chill", "Cute", "Confident", "Main Character", "Soft",
    "Low-key / Don't talk to me", "Dress to impress", "Keep it simple",
}

@router.get("/style-profile")
def get_style_profile(current_user: dict = Depends(get_current_user)):
    database = get_database()
    stored = database.users.find_one({"_id": current_user["_id"]}) or {}
    profile = stored.get("style_profile") or {
        "name": current_user.get("name", ""),
        "vibes": [],
        "occasions": [],
        "clothing": [],
        "palette": [],
    }
    return {"profile": profile, "onboarding_completed": is_onboarding_completed(stored)}

@router.put("/style-profile")
def save_style_profile(profile: StyleProfilePayload, current_user: dict = Depends(get_current_user)):
    database = get_database()
    if not profile.name.strip():
        raise HTTPException(status_code=400, detail="Name is required.")
    clean = {
        "name": profile.name.strip()[:100],
        "vibes": list(dict.fromkeys(x.strip() for x in profile.vibes if x.strip()))[:20],
        "occasions": list(dict.fromkeys(x.strip() for x in profile.occasions if x.strip()))[:20],
        "clothing": list(dict.fromkeys(x.strip() for x in profile.clothing if x.strip()))[:30],
        "palette": list(dict.fromkeys(x.strip() for x in profile.palette if x.strip()))[:20],
    }
    database.users.update_one({"_id": current_user["_id"]}, {"$set": {"style_profile": clean, "profile_completed": True, "onboarding_completed": True}})
    return {"profile": clean, "saved": True, "onboarding_completed": True}

@router.get("/mood/today")
def get_today_mood(current_user: dict = Depends(get_current_user)):
    database = get_database()
    today = datetime.now(timezone.utc).date().isoformat()
    entry = database.mood_history.find_one({"user_id": current_user["_id"], "date": today}, sort=[("created_at", -1)])
    return {"mood": entry.get("mood") if entry else None, "date": today}

@router.post("/mood")
def save_today_mood(payload: MoodPayload, current_user: dict = Depends(get_current_user)):
    mood = payload.mood.strip()
    if mood not in _ALLOWED_MOODS:
        raise HTTPException(status_code=400, detail="Invalid mood selection.")
    database = get_database()
    now = datetime.now(timezone.utc)
    today = now.date().isoformat()
    database.mood_history.insert_one({"user_id": current_user["_id"], "mood": mood, "date": today, "created_at": now})
    database.users.update_one({"_id": current_user["_id"]}, {"$set": {"current_mood": mood, "current_mood_date": today}})
    return {"mood": mood, "date": today, "saved": True}

# VESTIQ_CORE_UPDATE_2026_10_06
