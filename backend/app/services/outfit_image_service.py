# Purpose: builds an outfit collage from two item images (not used by app code yet)
from io import BytesIO
import base64
from uuid import uuid4

import httpx
from PIL import Image, ImageOps, ImageDraw
import cloudinary.uploader

# Ensure the project Cloudinary configuration is loaded before upload.
import app.services.cloudinary_service  # noqa: F401


def _download_image(url: str) -> Image.Image:
    response = httpx.get(url, timeout=20, follow_redirects=True)
    response.raise_for_status()
    return Image.open(BytesIO(response.content)).convert("RGB")


def create_outfit_collage(top_url: str, bottom_url: str | None = None) -> str:
    """Create a simple visual outfit board from wardrobe images and upload it to Cloudinary."""
    images = [_download_image(top_url)]
    if bottom_url:
        images.append(_download_image(bottom_url))

    card_width = 520
    card_height = 620
    gap = 16
    canvas_width = card_width * len(images) + gap * (len(images) - 1)
    canvas = Image.new("RGB", (canvas_width, card_height), "white")

    for index, image in enumerate(images):
        fitted = ImageOps.fit(image, (card_width, card_height - 60), method=Image.Resampling.LANCZOS)
        x = index * (card_width + gap)
        canvas.paste(fitted, (x, 0))
        draw = ImageDraw.Draw(canvas)
        draw.text((x + 16, card_height - 42), "Vestiq outfit", fill="black")

    buffer = BytesIO()
    canvas.save(buffer, format="JPEG", quality=88)
    buffer.seek(0)

    try:
        result = cloudinary.uploader.upload(
            buffer,
            folder="vestiq/outfits",
            public_id=f"outfit_{uuid4().hex}",
            resource_type="image",
        )
        return result["secure_url"]
    except Exception:
        # Keep the recommendation UI functional even if Cloudinary is
        # temporarily unavailable. The browser can render this generated
        # collage directly as a data URL.
        encoded = base64.b64encode(
            buffer.getvalue()
        ).decode("ascii")
        return f"data:image/jpeg;base64,{encoded}"
