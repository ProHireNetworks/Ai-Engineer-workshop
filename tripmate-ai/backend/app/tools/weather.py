"""
TripMate AI - Weather Tool
Retrieves seasonal climate summaries and destination forecasts.
"""

from typing import Any, Dict, Optional
from app.schemas.trip import WeatherInformation
from app.tools.base import BaseTool
from app.tools.schemas import WeatherArgs


class GetWeatherTool(BaseTool):
    """Provides weather outlook, temperature ranges, and travel climate advisories."""

    name = "get_weather"
    description = (
        "Get seasonal weather forecasts and climate insights for a destination, "
        "including expected temperature ranges, precipitation likelihood, and travel suitability."
    )
    args_schema = WeatherArgs

    async def _run(
        self, destination: str, travel_date: Optional[str] = None
    ) -> Dict[str, Any]:
        dest_lower = destination.lower()
        date_label = travel_date or "Current Season"

        if "jaipur" in dest_lower or "rajasthan" in dest_lower:
            weather = WeatherInformation(
                destination=destination,
                season_or_period=date_label,
                forecast_summary="Sunny with clear skies and mild, pleasant evenings.",
                average_temp_celsius=22.0,
                min_temp_celsius=14.0,
                max_temp_celsius=28.0,
                precipitation_chance_pct=5,
                travel_suitability="optimal",
                is_mock=True,
            )
        elif "goa" in dest_lower:
            weather = WeatherInformation(
                destination=destination,
                season_or_period=date_label,
                forecast_summary="Warm and tropical with gentle coastal sea breezes.",
                average_temp_celsius=28.0,
                min_temp_celsius=23.0,
                max_temp_celsius=32.0,
                precipitation_chance_pct=15,
                travel_suitability="optimal",
                is_mock=True,
            )
        else:
            weather = WeatherInformation(
                destination=destination,
                season_or_period=date_label,
                forecast_summary=f"Pleasant seasonal climate in {destination}.",
                average_temp_celsius=21.0,
                min_temp_celsius=15.0,
                max_temp_celsius=26.0,
                precipitation_chance_pct=20,
                travel_suitability="favorable",
                is_mock=True,
            )

        return weather.model_dump()

