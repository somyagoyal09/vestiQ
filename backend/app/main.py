# Purpose: creates the FastAPI app, enables CORS and registers all routers
from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware
from app.core.configuration import settings
from app.database.database_connection import check_database_connection
from app.routes.authentication import router as authentication_router
from app.routes.wardrobe import router as wardrobe_router
from app.routes.weather import router as weather_router
from app.routes.recommendations import router as recommendations_router
from app.routes.stylist import router as stylist_router
from app.routes.set_password import router as set_password_router

application = FastAPI(
    title=settings.APP_NAME,
    description="Intelligent Clothing & Personal Styling API",
    version="1.0.0"
)

application.add_middleware(
    CORSMiddleware,
    allow_origins=[
    settings.FRONTEND_URL.rstrip("/"),
    "https://vestiq-h9lb.onrender.com",
    "http://localhost:5173",
],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


application.include_router(authentication_router)
application.include_router(wardrobe_router)
application.include_router(weather_router)
application.include_router(recommendations_router)
application.include_router(stylist_router)
application.include_router(set_password_router)

@application.get("/")
def home():
    return {
        "application": settings.APP_NAME,
        "status": "running"
    }


@application.get("/health")
def health_check():
    mongodb_status = check_database_connection()

    return {
        "application": settings.APP_NAME,
        "api_status": "healthy",
        "mongodb_status": "connected" if mongodb_status else "disconnected"
    }