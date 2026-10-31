from fastapi import APIRouter, Depends, HTTPException, Query
import logging
import os
import re
import base64
import httpx
from pymongo.errors import PyMongoError

from app.schemas.stylist import (
    ChatRequest,
    ChatResponse,
    HistoryMessage,
    HistoryResponse,
    StylistPreferences,
)
from app.services import stylist_service
from app.services.authentication import get_current_user
from app.services.llm_client import LLMError
from app.core.configuration import settings

logger = logging.getLogger("vestiq.stylist.images")

router = APIRouter(prefix="/stylist", tags=["Stylist"])

_LLM_STATUS = {
    "not_configured": (503, "The stylist is not configured yet."),
    "timeout": (504, "The stylist took too long to respond. Please try again."),
    "provider_error": (502, "The stylist is temporarily unavailable. Please try again."),
}


def _database_unavailable() -> HTTPException:
    return HTTPException(status_code=503, detail="Database is temporarily unavailable.")


@router.post("/chat", response_model=ChatResponse)
async def stylist_chat(payload: ChatRequest, current_user: dict = Depends(get_current_user)):
    try:
        return await stylist_service.chat(current_user["_id"], payload.message, image_base64=payload.image_base64, image_mime_type=payload.image_mime_type)
    except LLMError as error:
        status_code, detail = _LLM_STATUS.get(error.kind, _LLM_STATUS["provider_error"])
        raise HTTPException(status_code=status_code, detail=detail)
    except PyMongoError:
        raise _database_unavailable()


@router.post("/generate-image")
async def generate_stylist_image(payload: dict, current_user: dict = Depends(get_current_user)):
    """Generate an outfit concept image through Gemini; never persist image bytes."""
    prompt = str(payload.get("prompt", "")).strip()
    if not prompt or len(prompt) > 1000:
        raise HTTPException(status_code=422, detail="Prompt must contain 1–1000 characters.")

    api_key = (getattr(settings, "LLM_API_KEY", "") or "").strip()
    if not api_key:
        raise HTTPException(status_code=503, detail="Gemini API key is not configured. Add LLM_API_KEY to backend/.env.")

    # This model supports image output through generateContent. Override in backend/.env if needed.
    model = os.getenv("STYLIST_IMAGE_MODEL", "gemini-2.5-flash-image").strip()
    if not re.fullmatch(r"[A-Za-z0-9._-]+", model):
        raise HTTPException(status_code=422, detail="Invalid STYLIST_IMAGE_MODEL value.")

    full_prompt = (
        "Create one polished fashion-styling inspiration image. Show a generic adult model or "
        "fashion mannequin wearing the complete outfit described below, full-body, with the "
        "clothing, shoes and accessories clearly visible. Use realistic fabric texture, clean "
        "studio lighting and an uncluttered background. Keep the outfit wearable and coherent. "
        "This is an illustrative concept, not an exact virtual try-on. Outfit request: " + prompt
    )
    parts = []
    image_base64 = payload.get("image_base64")
    image_mime_type = payload.get("image_mime_type")
    if image_base64:
        if not isinstance(image_base64, str) or len(image_base64) > 7_000_000:
            raise HTTPException(status_code=422, detail="Attached image is too large.")
        if image_mime_type not in {"image/jpeg", "image/png", "image/webp"}:
            raise HTTPException(status_code=422, detail="Attached image must be JPEG, PNG, or WebP.")
        try:
            decoded = base64.b64decode(image_base64, validate=True)
        except (ValueError, TypeError):
            raise HTTPException(status_code=422, detail="Attached image data is invalid.")
        if not decoded or len(decoded) > 5 * 1024 * 1024:
            raise HTTPException(status_code=422, detail="Attached image must be smaller than 5 MB.")
        parts.append({"inline_data": {"mime_type": image_mime_type, "data": image_base64}})
        full_prompt += (
            " Use the attached clothing image as a reference for the featured garment and its color. "
            "Style the rest of the outfit around it; do not claim this is an exact try-on."
        )
    parts.append({"text": full_prompt})

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    request_json = {
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]},
    }
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=15.0)) as client:
            response = await client.post(
                url,
                headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
                json=request_json,
            )
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Image generation took too long. Please try again.")
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="Could not reach Gemini image generation. Check your internet connection.")

    if response.status_code != 200:
        # Avoid logging prompts, image bytes, or API keys.
        logger.warning("Gemini image generation returned HTTP %s", response.status_code)
        raise HTTPException(status_code=502, detail="Gemini image generation failed. Check model access and API quota.")

    try:
        data = response.json()
        candidates = data.get("candidates", [])
        output_parts = candidates[0].get("content", {}).get("parts", []) if candidates else []
        for part in output_parts:
            inline = part.get("inlineData") or part.get("inline_data")
            if inline and inline.get("data"):
                encoded = inline["data"]
                decoded = base64.b64decode(encoded, validate=True)
                if decoded and len(decoded) <= 12 * 1024 * 1024:
                    return {
                        "mime_type": inline.get("mimeType") or inline.get("mime_type") or "image/png",
                        "image_base64": encoded,
                    }
    except (ValueError, TypeError, AttributeError, IndexError):
        pass
    raise HTTPException(status_code=502, detail="Gemini did not return an image. Try again or check the configured image model.")


@router.get("/preferences", response_model=StylistPreferences)
def get_stylist_preferences(current_user: dict = Depends(get_current_user)):
    try:
        return stylist_service.get_preferences(current_user["_id"])
    except PyMongoError:
        raise _database_unavailable()


@router.put("/preferences", response_model=StylistPreferences)
def update_stylist_preferences(
    preferences: StylistPreferences, current_user: dict = Depends(get_current_user)
):
    try:
        return stylist_service.save_preferences(current_user["_id"], preferences)
    except PyMongoError:
        raise _database_unavailable()


@router.delete("/preferences")
def reset_stylist_preferences(current_user: dict = Depends(get_current_user)):
    try:
        return {"deleted": stylist_service.delete_preferences(current_user["_id"])}
    except PyMongoError:
        raise _database_unavailable()


@router.get("/history", response_model=HistoryResponse)
def get_stylist_history(
    limit: int = Query(50, ge=1, le=100), current_user: dict = Depends(get_current_user)
):
    try:
        messages = stylist_service.get_history(current_user["_id"], limit)
    except PyMongoError:
        raise _database_unavailable()
    return HistoryResponse(
        messages=[
            HistoryMessage(role=m["role"], content=m["content"], created_at=m.get("created_at"))
            for m in messages
        ]
    )


@router.delete("/history")
def clear_stylist_history(current_user: dict = Depends(get_current_user)):
    try:
        return {"deleted": stylist_service.delete_history(current_user["_id"])}
    except PyMongoError:
        raise _database_unavailable()
