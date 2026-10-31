import httpx

from datetime import datetime, timedelta, timezone

from app.core.configuration import settings


FORECAST_URL = (
    "https://api.openweathermap.org/data/2.5/forecast"
)


async def get_weather_forecast(
    city: str,
    target_date: str,
) -> dict:

    if not settings.WEATHER_API_KEY:
        raise ValueError(
            "WEATHER_API_KEY is not configured."
        )

    try:
        requested_date = datetime.strptime(
            target_date,
            "%Y-%m-%d"
        ).date()

    except ValueError:
        raise ValueError(
            "target_date must be in YYYY-MM-DD format."
        )

    params = {
        "q": city,
        "appid": settings.WEATHER_API_KEY,
        "units": "metric",
    }

    async with httpx.AsyncClient(
        timeout=10
    ) as client:

        response = await client.get(
            FORECAST_URL,
            params=params,
        )

    if response.status_code != 200:

        try:
            error_data = response.json()

        except Exception:
            error_data = {}

        raise ValueError(
            error_data.get(
                "message",
                "Unable to fetch weather forecast."
            )
        )

    data = response.json()

    forecast_list = data.get(
        "list",
        []
    )

    if not forecast_list:
        raise ValueError(
            "No forecast data available."
        )

    # OpenWeather provides the city's UTC offset.
    # This lets us compare forecast timestamps
    # using the city's local date.
    city_timezone_offset = (
        data.get("city", {})
        .get("timezone", 0)
    )

    city_timezone = timezone(
        timedelta(
            seconds=city_timezone_offset
        )
    )

    selected_forecasts = []

    for forecast in forecast_list:

        forecast_time = datetime.fromtimestamp(
            forecast["dt"],
            timezone.utc
        ).astimezone(
            city_timezone
        )

        if forecast_time.date() == requested_date:
            selected_forecasts.append(
                forecast
            )

    if not selected_forecasts:
        raise ValueError(
            "Weather forecast is not available "
            "for the selected date. "
            "The forecast API currently supports "
            "a limited future window."
        )

    temperatures = [
        item["main"]["temp"]
        for item in selected_forecasts
    ]

    feels_like = [
        item["main"]["feels_like"]
        for item in selected_forecasts
    ]

    print("WEATHER DEBUG CITY:", city)
    print("WEATHER DEBUG DATE:", target_date)

    for item in selected_forecasts:
        print({
            "time": datetime.fromtimestamp(
            item["dt"], timezone.utc
            ).astimezone(city_timezone).strftime(
                "%Y-%m-%d %H:%M"
            ),
        "temperature": item.get("main", {}).get("temp"),
        "condition": item.get("weather", [{}])[0].get("main"),
        "rain_probability": item.get("pop"),
        })

    weather_conditions = []

    for item in selected_forecasts:

        weather = item.get(
            "weather",
            []
        )

        if weather:
            weather_conditions.append(
                weather[0]["main"]
            )

    average_temperature = (
        sum(temperatures)
        / len(temperatures)
    )

   
    average_feels_like = (
        sum(feels_like)
        / len(feels_like)
    )

    rain_probabilities = [
        item.get("pop", 0)
        for item in selected_forecasts
    ]

    rain_probability = max(
        rain_probabilities
    )

    if weather_conditions:

        weather_condition = max(
            set(weather_conditions),
            key=weather_conditions.count
        )

    else:
        weather_condition = "Unknown"

    rain_expected = (
        rain_probability >= 0.40
        or weather_condition.lower()
        in {
            "rain",
            "drizzle",
            "thunderstorm",
        }
    )

    return {
        "city": (
            data.get("city", {})
            .get("name", city)
        ),

        "date": target_date,

        "temperature": round(
            average_temperature,
            1
        ),

        "feels_like": round(
            average_feels_like,
            1
        ),

        "rain_probability": round(
            rain_probability * 100,
            1
        ),

        "rain_expected": rain_expected,

        "weather_condition":
            weather_condition,

        "forecast_points":
            len(selected_forecasts),
    }