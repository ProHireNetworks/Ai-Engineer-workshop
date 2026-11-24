"""
TripMate AI - Travel Search Tools
Implementations for destination discovery, attraction lookup, and transit time estimation.
"""

from typing import Any, Dict, List, Optional
from app.schemas.trip import Attraction
from app.tools.base import BaseTool
from app.tools.schemas import (
    AttractionsSearchArgs,
    DestinationSearchArgs,
    TravelTimeArgs,
)


class SearchDestinationTool(BaseTool):
    """Discovers destination culture, geography, climate, and highlights."""

    name = "search_destination"
    description = (
        "Search comprehensive travel information for a destination city or country, "
        "including cultural context, highlights, and regional travel tips."
    )
    args_schema = DestinationSearchArgs

    async def _run(self, destination: str, interests: List[str] = None) -> Dict[str, Any]:
        interests = interests or []
        interests_str = ", ".join(interests) if interests else "general sights"

        return {
            "destination": destination,
            "overview": (
                f"[MOCK DATA] {destination} is renowned for its vibrant heritage, rich culinary culture, "
                f"and distinct architectural landmarks. Tailored to interests in {interests_str}."
            ),
            "best_time_to_visit": "October to March (pleasant winter climate)",
            "local_currency": "INR" if "india" in destination.lower() or any(c in destination.lower() for c in ["jaipur", "goa", "delhi", "mumbai", "kerala"]) else "USD",
            "transport_overview": "Local metro, auto-rickshaws, and rideshares are easily accessible.",
            "is_mock": True,
        }


class SearchAttractionsTool(BaseTool):
    """Finds top tourist sights, cultural landmarks, and activities."""

    name = "search_attractions"
    description = (
        "Retrieve curated tourist attractions, monuments, museums, and natural landmarks "
        "for a given destination with admission fees and estimated visit durations."
    )
    args_schema = AttractionsSearchArgs

    async def _run(
        self, destination: str, category: Optional[str] = None, limit: int = 5
    ) -> Dict[str, Any]:
        dest_lower = destination.lower()

        # Destination-specific sample repository
        if "jaipur" in dest_lower:
            all_attractions = [
                Attraction(
                    name="Amber Fort",
                    category="Historical",
                    description="Majestic 16th-century hilltop palace fort with Maota Lake views.",
                    estimated_duration_hours=3.0,
                    admission_fee=500.0,
                    currency="INR",
                    location_area="Amer",
                ),
                Attraction(
                    name="Hawa Mahal",
                    category="Historical",
                    description="Iconic five-story pink sandstone 'Palace of Winds' with 953 jharokhas.",
                    estimated_duration_hours=1.5,
                    admission_fee=200.0,
                    currency="INR",
                    location_area="Old City",
                ),
                Attraction(
                    name="City Palace",
                    category="Culture",
                    description="Royal residence complex blending Rajasthani and Mughal architectural styles.",
                    estimated_duration_hours=2.5,
                    admission_fee=300.0,
                    currency="INR",
                    location_area="Old City",
                ),
                Attraction(
                    name="Jantar Mantar",
                    category="Science & History",
                    description="UNESCO World Heritage 18th-century astronomical observatory.",
                    estimated_duration_hours=1.5,
                    admission_fee=200.0,
                    currency="INR",
                    location_area="Old City",
                ),
                Attraction(
                    name="Nahargarh Fort",
                    category="Scenic View",
                    description="Fort perched atop the Aravalli hills offering panoramic sunset vistas.",
                    estimated_duration_hours=2.0,
                    admission_fee=200.0,
                    currency="INR",
                    location_area="Aravalli Hills",
                ),
            ]
        elif "goa" in dest_lower:
            all_attractions = [
                Attraction(
                    name="Fort Aguada",
                    category="Historical",
                    description="17th-century Portuguese fort and lighthouse overlooking Sinquerim Beach.",
                    estimated_duration_hours=2.0,
                    admission_fee=100.0,
                    currency="INR",
                    location_area="North Goa",
                ),
                Attraction(
                    name="Basilica of Bom Jesus",
                    category="Culture",
                    description="UNESCO World Heritage baroque church holding the mortal remains of St. Francis Xavier.",
                    estimated_duration_hours=1.5,
                    admission_fee=0.0,
                    currency="INR",
                    location_area="Old Goa",
                ),
                Attraction(
                    name="Dudhsagar Waterfalls",
                    category="Nature",
                    description="Four-tiered cascade located on the Mandovi River amidst lush Western Ghats.",
                    estimated_duration_hours=4.0,
                    admission_fee=500.0,
                    currency="INR",
                    location_area="South Goa",
                ),
                Attraction(
                    name="Anjuna Flea Market",
                    category="Shopping & Food",
                    description="Lively coastal market with handicrafts, spices, bohemian attire, and live music.",
                    estimated_duration_hours=2.5,
                    admission_fee=0.0,
                    currency="INR",
                    location_area="Anjuna",
                ),
            ]
        else:
            all_attractions = [
                Attraction(
                    name=f"[MOCK] Historic Center of {destination}",
                    category="Culture",
                    description=f"Central heritage square with landmark architecture and local cafes.",
                    estimated_duration_hours=2.5,
                    admission_fee=0.0,
                    currency="INR",
                    location_area="City Center",
                ),
                Attraction(
                    name=f"[MOCK] National Museum of {destination}",
                    category="Museum",
                    description=f"Premier cultural exhibition showcasing local regional artifacts.",
                    estimated_duration_hours=2.0,
                    admission_fee=250.0,
                    currency="INR",
                    location_area="Museum District",
                ),
                Attraction(
                    name=f"[MOCK] Scenic Viewpoint of {destination}",
                    category="Nature",
                    description=f"Panoramic elevated viewpoint over {destination}.",
                    estimated_duration_hours=1.5,
                    admission_fee=100.0,
                    currency="INR",
                    location_area="Highlands",
                ),
            ]

        # Filter by category if requested
        if category:
            filtered = [a for a in all_attractions if category.lower() in a.category.lower()]
            if filtered:
                all_attractions = filtered

        selected = all_attractions[:limit]
        return {
            "destination": destination,
            "total_found": len(selected),
            "attractions": [a.model_dump() for a in selected],
            "is_mock": True,
        }


class EstimateTravelTimeTool(BaseTool):
    """Calculates transit distance, duration, and routing recommendations."""

    name = "estimate_travel_time"
    description = (
        "Estimate travel duration, approximate distance, and routing considerations "
        "between two locations by driving, transit, flight, or walking."
    )
    args_schema = TravelTimeArgs

    async def _run(self, origin: str, destination: str, mode: str = "driving") -> Dict[str, Any]:
        # Deterministic simulation based on mode
        speed_and_unit = {
            "walking": {"speed_kmh": 5.0, "notes": "Leisurely pedestrian route."},
            "driving": {"speed_kmh": 40.0, "notes": "Subject to urban traffic conditions."},
            "transit": {"speed_kmh": 30.0, "notes": "Public bus / suburban rail transit."},
            "flight": {"speed_kmh": 500.0, "notes": "Includes airport boarding buffers."},
        }
        profile = speed_and_unit.get(mode, speed_and_unit["driving"])

        # Simulated distance calculation
        simulated_km = 15.0 if mode != "flight" else 350.0
        hours = simulated_km / profile["speed_kmh"]
        minutes = int(round(hours * 60))

        return {
            "origin": origin,
            "destination": destination,
            "mode": mode,
            "distance_km": simulated_km,
            "estimated_minutes": minutes,
            "estimated_formatted": f"{minutes // 60}h {minutes % 60}m" if minutes >= 60 else f"{minutes} mins",
            "notes": profile["notes"],
            "is_mock": True,
        }

