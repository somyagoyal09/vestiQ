from pathlib import Path
import tempfile

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

import sys

PROJECT_ROOT = Path(__file__).resolve().parents[4]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai.inference.predict import predict_clothing


router = APIRouter(
    prefix="/wardrobe",
    tags=["Wardrobe"]
)


@router.post(
    "/items",
    response_model=ClothingResponse,
    status_code=status.HTTP_201_CREATED
)
async def add_clothing_item(
    name: str = Form(...),
    category: str | None = Form(None),
    color: str | None = Form(None),
    image: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    # Validate image
    if (
        not image.content_type
        or not image.content_type.startswith("image/")
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only image files are allowed."
        )

    # Save uploaded image temporarily for ML prediction
    suffix = Path(image.filename or ".jpg").suffix

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=suffix
    ) as temp_file:

        temp_path = temp_file.name

        content = await image.read()
        temp_file.write(content)

    try:
        # ML prediction
        prediction = predict_clothing(temp_path)

        predicted_category = prediction["category"]
        confidence = prediction["confidence"]

        # If user didn't provide category,
        # use ML prediction automatically.
        final_category = (
            category.strip()
            if category and category.strip()
            else predicted_category
        )

        # Upload image to Cloudinary
        with open(temp_path, "rb") as image_file:
            image_url = upload_clothing_image(image_file)

        # Save clothing item
        database = get_database()

        clothing_document = create_clothing_document(
            user_id=str(current_user["_id"]),
            name=name,
            category=final_category,
            color=color,
            image_url=image_url,
        )

        # Store ML information also
        clothing_document["prediction"] = {
            "category": predicted_category,
            "confidence": confidence,
        }

        database.clothing.insert_one(
            clothing_document
        )

        return {
            "id": str(clothing_document["_id"]),
            "name": clothing_document["name"],
            "category": clothing_document["category"],
            "color": clothing_document["color"],
            "image_url": clothing_document["image_url"],
        }

    finally:
        # Delete temporary image
        Path(temp_path).unlink(
            missing_ok=True
        )


@router.get(
    "/items",
    response_model=list[ClothingResponse]
)
def get_wardrobe_items(
    current_user: dict = Depends(get_current_user),
):
    database = get_database()

    items = database.clothing.find({
        "user_id": current_user["_id"]
    })

    return [
        {
            "id": str(item["_id"]),
            "name": item["name"],
            "category": item["category"],
            "color": item.get("color"),
            "image_url": item["image_url"],
        }
        for item in items
    ]