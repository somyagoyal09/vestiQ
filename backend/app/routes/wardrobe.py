# Purpose: wardrobe endpoints: add item, list, worn/unworn, delete
from pathlib import Path
from datetime import datetime, timezone

from bson import ObjectId
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)

from app.database.database_connection import get_database
from app.models.clothing import create_clothing_document
from app.schemas.clothing import ClothingResponse
from app.services.authentication import get_current_user
from app.services.cloudinary_service import upload_clothing_image


router = APIRouter(
    prefix="/wardrobe",
    tags=["Wardrobe"],
)

# Canonical domain values. Matches recommendation_service.infer_domain().
ALLOWED_DOMAINS = {"western", "traditional", "indo_western", "fusion", "other"}


def serialize_item(item: dict) -> dict:
    return {
        "id": str(item["_id"]),
        "name": item.get("name", "Clothing Item"),
        "category": item.get("category"),
        "color": item.get("color"),
        "image_url": item.get("image_url", ""),
        "style": item.get("style"),
        "outfit_weight": item.get("outfit_weight"),
        "occasion_tags": item.get("occasion_tags", []),
        "domain": item.get("domain"),
        "prediction": item.get("prediction"),
        "created_at": item.get("created_at"),
        "last_worn_at": item.get("last_worn_at"),
    }


@router.post(
    "/items",
    response_model=ClothingResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_clothing_item(
    name: str = Form(...),
    domain: str = Form(""),
    category: str = Form(""),
    color: str | None = Form(None),
    style: str | None = Form(None),
    outfit_weight: str | None = Form(None),
    occasion_tags: str | None = Form(None),
    image: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    # -----------------------------
    # Validate image
    # -----------------------------
    if (
        not image.content_type
        or not image.content_type.startswith("image/")
    ):
        raise HTTPException(
            status_code=400,
            detail="Please upload a valid image file.",
        )

    # -----------------------------
    # Clean user-confirmed values
    # -----------------------------
    final_name = name.strip()
    # Same normalisation as the recommendation system: "indo-western" -> "indo_western".
    final_domain = (
        domain.strip().lower().replace("-", "_").replace("/", "_").replace(" ", "_")
    )
    final_category = category.strip().lower()
    final_color = color.strip().lower() if color else None
    final_style = style.strip().lower() if style else None
    final_weight = (
        outfit_weight.strip().lower()
        if outfit_weight
        else None
    )

    if not final_name:
        raise HTTPException(
            status_code=400,
            detail="Clothing name is required.",
        )

    if final_domain not in ALLOWED_DOMAINS:
        raise HTTPException(
            status_code=400,
            detail="Domain must be one of: western, traditional, indo-western, fusion, other.",
        )

    if not final_category:
        raise HTTPException(
            status_code=400,
            detail="Please enter a clothing type.",
        )

    if not final_color:
        raise HTTPException(
            status_code=400,
            detail="Please enter a clothing color.",
        )

    # -----------------------------
    # Occasion tags
    # -----------------------------
    tags = [
        tag.strip().lower()
        for tag in (occasion_tags or "").split(",")
        if tag.strip()
    ]

    temp_path = None

    try:
        # -----------------------------
        # Save image temporarily
        # -----------------------------
        suffix = (
            Path(image.filename or "upload.jpg").suffix
            or ".jpg"
        )

        import tempfile

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix,
        ) as temp_file:
            temp_path = temp_file.name
            temp_file.write(await image.read())

        # -----------------------------
        # Upload directly to Cloudinary
        # -----------------------------
        image_url = upload_clothing_image(temp_path)

        # -----------------------------
        # Create MongoDB document
        # -----------------------------
        document = create_clothing_document(
            user_id=str(current_user["_id"]),
            name=final_name,
            category=final_category,
            image_url=image_url,
            color=final_color,
        )

        # User-confirmed metadata
        document["domain"] = final_domain
        document["style"] = final_style
        document["outfit_weight"] = final_weight
        document["occasion_tags"] = tags

        # AI is NOT authoritative during upload.
        document["prediction"] = None

        database = get_database()

        database.clothing.insert_one(document)

        return serialize_item(document)

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to add clothing item: {error}",
        )

    finally:
        if temp_path:
            try:
                Path(temp_path).unlink(
                    missing_ok=True
                )
            except Exception:
                pass


@router.get(
    "/items",
    response_model=list[ClothingResponse],
)
def get_clothing_items(
    current_user: dict = Depends(get_current_user),
):
    database = get_database()

    items = database.clothing.find(
        {
            "user_id": current_user["_id"]
        }
    ).sort(
        "created_at",
        -1,
    )

    return [
        serialize_item(item)
        for item in items
    ]


@router.post(
    "/items/{item_id}/worn"
)
def mark_item_as_worn(
    item_id: str,
    current_user: dict = Depends(get_current_user),
):
    try:
        object_id = ObjectId(item_id)

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid clothing item id.",
        )

    database = get_database()

    result = database.clothing.update_one(
        {
            "_id": object_id,
            "user_id": current_user["_id"],
        },
        {
            "$set": {
                "last_worn_at": datetime.now(
                    timezone.utc
                )
            }
        },
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=404,
            detail="Clothing item not found.",
        )

    return {
        "message": "Clothing marked as worn today."
    }


@router.post("/items/{item_id}/unworn")
def undo_item_worn(item_id: str, current_user: dict = Depends(get_current_user)):
    try:
        object_id = ObjectId(item_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid clothing item id.")
    database = get_database()
    result = database.clothing.update_one(
        {"_id": object_id, "user_id": current_user["_id"]},
        {"$set": {"last_worn_at": None}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Clothing item not found.")
    return {"message": "Worn status removed."}


@router.delete("/items/{item_id}")
def delete_clothing_item(item_id: str, current_user: dict = Depends(get_current_user)):
    try:
        object_id = ObjectId(item_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid clothing item id.")
    database = get_database()
    result = database.clothing.delete_one(
        {"_id": object_id, "user_id": current_user["_id"]}
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Clothing item not found.")
    return {"message": "Clothing item deleted."}