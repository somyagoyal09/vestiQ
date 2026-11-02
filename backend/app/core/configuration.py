# Purpose: loads settings from environment variables
import os

from dotenv import load_dotenv

load_dotenv()


class ApplicationSettings:
    APP_NAME = os.getenv("APP_NAME", "Vestiq")
    APP_ENV = os.getenv("APP_ENV", "development")
    DEBUG = os.getenv("DEBUG", "true").lower() == "true"

    MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    DATABASE_NAME = os.getenv("DATABASE_NAME", "vestiq_db")

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "development-secret-key")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

    CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "")
    CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY", "")
    CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET", "")
    WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "")

    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
    
    # AI Stylist configuration
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "anthropic").lower().strip()
    LLM_API_KEY = os.getenv("LLM_API_KEY", "") or os.getenv("ANTHROPIC_API_KEY", "")
    LLM_MODEL = os.getenv("LLM_MODEL", "claude-haiku-5-5")
    LLM_TIMEOUT_SECONDS = float(os.getenv("LLM_TIMEOUT_SECONDS", "30"))
    LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "900"))
    STYLIST_USE_WARDROBE = os.getenv("STYLIST_USE_WARDROBE", "true").lower() == "true"

    STYLIST_HISTORY_LIMIT = int(os.getenv("STYLIST_HISTORY_LIMIT", "50"))
    STYLIST_CONTEXT_MESSAGES = int(os.getenv("STYLIST_CONTEXT_MESSAGES", "12"))
    STYLIST_CONTEXT_CHAR_BUDGET = int(os.getenv("STYLIST_CONTEXT_CHAR_BUDGET", "8000"))


    DISABLE_AUTH = os.getenv("DISABLE_AUTH", "true").lower() == "true"
    DEMO_USER_EMAIL = os.getenv("DEMO_USER_EMAIL", "vestiqdemo@gmail.com")

    # OAuth
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI = os.getenv(
        "GOOGLE_REDIRECT_URI",
        "http://127.0.0.1:8000/auth/google/callback",
    )

    INSTAGRAM_CLIENT_ID = os.getenv("INSTAGRAM_CLIENT_ID", "")
    INSTAGRAM_CLIENT_SECRET = os.getenv("INSTAGRAM_CLIENT_SECRET", "")
    INSTAGRAM_REDIRECT_URI = os.getenv(
        "INSTAGRAM_REDIRECT_URI",
        "http://127.0.0.1:8000/auth/instagram/callback",
    )
    INSTAGRAM_GRAPH_VERSION = os.getenv("INSTAGRAM_GRAPH_VERSION", "v24.0")


settings = ApplicationSettings()
