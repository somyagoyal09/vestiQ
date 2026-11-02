# Purpose: uploads clothing images to Cloudinary and returns the URL
import cloudinary
import cloudinary.uploader

from app.core.configuration import settings


cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
)


def upload_clothing_image(file) -> str:
    """Upload a clothing image to Cloudinary and return its URL."""

    result = cloudinary.uploader.upload(
        file,
        folder="vestiq/wardrobe",
        resource_type="image",
    )

    return result["secure_url"]