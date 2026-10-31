from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

from app.core.configuration import settings


mongo_client = MongoClient(
    settings.MONGODB_URL,
    serverSelectionTimeoutMS=5000
)

database = mongo_client[settings.DATABASE_NAME]


def check_database_connection() -> bool:
    """Check whether Vestiq can connect to MongoDB."""
    try:
        mongo_client.admin.command("ping")
        return True
    except ConnectionFailure:
        return False


def get_database():
    """Return the Vestiq MongoDB database."""
    return database