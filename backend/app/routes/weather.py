# Purpose: GET /weather/forecast endpoint
from datetime import date, timedelta

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)

from app.services.authentication import (
    get_current_user
)

from app.services.weather_service import (
    get_weather_forecast
)


router = APIRouter(
    prefix="/weather",
    tags=["Weather"]
)


@router.get("/forecast")
async def weather_forecast(
    city: str = Query(
        ...,
        min_length=2,
        max_length=100
    ),

    target_date: str | None = Query(
        None,
        description=(
            "Date in YYYY-MM-DD format. "
            "Defaults to tomorrow."
        )
    ),

    current_user: dict = Depends(
        get_current_user
    ),
):

    if target_date is None:

        target_date = str(
            date.today() + timedelta(days=1)
        )

    try:

        forecast = await get_weather_forecast(
            city=city,
            target_date=target_date
        )

        return forecast

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception:

        raise HTTPException(
            status_code=502,
            detail=(
                "Weather forecast service "
                "is currently unavailable."
            )
        )