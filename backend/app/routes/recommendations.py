# Purpose: GET /recommendations: outfit suggestions from wardrobe, weather and preferences
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query

from app.database.database_connection import get_database
from app.services.authentication import get_current_user
from app.services.recommendation_service import (
    generate_outfits,
    parse_stylist_request,
)
from app.services.weather_service import get_weather_forecast

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


def _first(*values):
    for value in values:
        if value is not None and str(value).strip():
            return str(value).strip()
    return None


@router.get("")
async def get_recommendations(
    city: str = Query("Meerut", min_length=2, max_length=100),
    target_date: str | None = Query(None),
    occasion: str = Query("everyday", min_length=2, max_length=50),
    style: str | None = Query(None),
    preferred_color: str | None = Query(None),
    top_color: str | None = Query(None),
    bottom_color: str | None = Query(None),
    top_type: str | None = Query(None),
    bottom_type: str | None = Query(None),
    one_piece: bool = Query(False),
    outfit_weight: str | None = Query(None),
    mood: str | None = Query(None),
    preferred_top: str | None = Query(None),
    preferred_bottom: str | None = Query(None),
    preferred_vibe: str | None = Query(None),
    vibe: str | None = Query(None),
    specific_request: str | None = Query(None),
    request: str | None = Query(None),
    top_preference: str | None = Query(None),
    bottom_preference: str | None = Query(None),
    current_user: dict = Depends(get_current_user),
):
    if target_date is None:
        target_date = str(date.today() + timedelta(days=1))

    database = get_database()

    wardrobe_items = list(
        database.clothing.find(
            {"user_id": current_user["_id"]}
        )
    )

    # Weather does not depend on the wardrobe, so a new user with 0 pieces still sees it.
    weather = None
    weather_error = None
    try:
        weather = await get_weather_forecast(
            city=city,
            target_date=target_date,
        )
    except ValueError as error:
        weather_error = error

    if not wardrobe_items:
        return {
            "message": "Your wardrobe is empty.",
            "weather": weather,
            "recommendations": [],
        }

    if weather_error is not None:
        raise HTTPException(
            status_code=400,
            detail=str(weather_error),
        )

    free_text = _first(specific_request, request, "") or ""

    request_parts = [free_text]

    if top_color:
        request_parts.append(f"top color: {top_color}")

    if bottom_color:
        request_parts.append(f"bottom color: {bottom_color}")

    if one_piece:
        request_parts.append("one piece outfit; no bottom")

    service_request = ". ".join(
        part.strip()
        for part in request_parts
        if part.strip()
    )

    parsed = parse_stylist_request(service_request)

    styles = list(
        current_user.get("preferred_styles", []) or []
    )

    if style:
        styles.extend(
            value.strip().lower()
            for value in style.split(",")
            if value.strip()
        )

    styles.extend(parsed.get("styles", []))
    styles = list(dict.fromkeys(styles))

    final_color = _first(
        preferred_color,
        parsed.get("preferred_color"),
    )

    profile_colors = current_user.get("preferred_colors", []) or []

    if not final_color and profile_colors:
        final_color = profile_colors[0]

    final_weight = _first(
        outfit_weight,
        parsed.get("preferred_weight"),
    )

    final_top = _first(
        preferred_top,
        top_preference,
        top_type,
        parsed.get("preferred_top"),
    )

    final_bottom = _first(
        preferred_bottom,
        bottom_preference,
        bottom_type,
        parsed.get("preferred_bottom"),
    )

    final_vibe = _first(preferred_vibe, vibe)

    if final_vibe:
        parsed_vibe = parse_stylist_request(final_vibe)
        styles.extend(parsed_vibe.get("styles", []))
        styles = list(dict.fromkeys(styles))

    elif mood:
        parsed_mood = parse_stylist_request(mood)
        styles.extend(parsed_mood.get("styles", []))
        styles = list(dict.fromkeys(styles))

    outfits = generate_outfits(
        wardrobe=wardrobe_items,
        temperature=weather["temperature"],
        weather_condition=weather["weather_condition"],
        occasion=occasion,
        rain_probability=weather["rain_probability"],
        preferred_styles=styles,
        preferred_color=final_color,
        preferred_weight=final_weight,
        preferred_top=final_top,
        preferred_bottom=final_bottom,
        vibe=final_vibe or mood,
        specific_request=service_request,
        user_gender=(
            current_user.get("gender")
            or current_user.get("clothing_preference")
        ),
        top_color=top_color,
        bottom_color=bottom_color,
        one_piece=one_piece,
    )

    recommendations = []

    def serialize(item):
        if not item:
            return None

        return {
            "id": str(item.get("_id", item.get("id", ""))),
            "name": (
                item.get("name")
                or item.get("category")
                or "Clothing"
            ),
            "category": item.get("category"),
            "color": item.get("color"),
            "domain": item.get("domain"),
            "style": item.get("style"),
            "image_url": item.get("image_url"),
        }

    for outfit in outfits:
        recommendations.append(
            {
                "top": serialize(outfit.get("top")),
                "bottom": serialize(outfit.get("bottom")),
                "outfit_type": outfit.get(
                    "outfit_type",
                    "two_piece",
                ),
                "score": max(
                0,
                min(100, round(float(outfit.get("score", 0))))
                ),
                "reasons": outfit.get("reasons", []),
            }
        )

    return {
        "weather": weather,
        "occasion": occasion,
        "preferences": {
            "styles": styles,
            "preferred_color": final_color,
            "top_color": top_color,
            "bottom_color": bottom_color,
            "top_type": final_top,
            "bottom_type": final_bottom,
            "one_piece": one_piece,
            "outfit_weight": final_weight,
            "preferred_vibe": final_vibe,
            "specific_request": service_request,
            "mood": mood,
        },
        "recommendations": recommendations,
    }