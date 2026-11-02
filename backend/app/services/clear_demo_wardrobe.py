# Purpose: helper that clears the demo user's wardrobe (not used by app code)
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from app.core.configuration import settings
from app.database.database_connection import get_database


DEMO_EMAIL = (
    settings.DEMO_USER_EMAIL
    or "vestiqdemo@gmail.com"
).lower().strip()


database = get_database()

user = database.users.find_one(
    {
        "email": DEMO_EMAIL
    }
)

if not user:
    print(
        f"Demo user not found: {DEMO_EMAIL}"
    )
    raise SystemExit(1)


result = database.clothing.delete_many(
    {
        "user_id": user["_id"]
    }
)


print("=" * 50)
print("Vestiq demo wardrobe cleanup")
print("=" * 50)
print(f"User: {DEMO_EMAIL}")
print(
    f"Deleted clothing items: {result.deleted_count}"
)
print("=" * 50)
print("Wardrobe is now empty.")
print("=" * 50)