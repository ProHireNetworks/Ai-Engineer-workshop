"""
TripMate AI - Accommodation Tool
Retrieves lodging and hotel recommendations tailored to budget tiers and party sizes.
"""

from typing import Any, Dict, List, Optional
from app.schemas.trip import AccommodationOption
from app.tools.base import BaseTool
from app.tools.schemas import AccommodationSearchArgs


class SearchAccommodationTool(BaseTool):
    """Finds vetted hotels, resorts, and lodging matching travel preferences."""

    name = "search_accommodation"
    description = (
        "Search for accommodation and lodging options in a destination, categorized by "
        "budget tier, party size, ratings, and nightly pricing."
    )
    args_schema = AccommodationSearchArgs

    async def _run(
        self,
        destination: str,
        check_in: Optional[str] = None,
        check_out: Optional[str] = None,
        guests: int = 1,
        budget_tier: str = "mid",
    ) -> Dict[str, Any]:
        dest_lower = destination.lower()
        currency = "INR" if any(c in dest_lower for c in ["jaipur", "goa", "delhi", "mumbai", "india"]) else "USD"

        # Tier rate scaling
        base_rate = {"budget": 1200.0, "mid": 3500.0, "luxury": 9500.0}.get(budget_tier, 3000.0)
        if currency == "USD":
            base_rate = {"budget": 45.0, "mid": 120.0, "luxury": 350.0}.get(budget_tier, 100.0)

        if "jaipur" in dest_lower:
            options = [
                AccommodationOption(
                    name="Zostel Jaipur Heritage",
                    property_type="hostel",
                    location="Hawa Mahal Road, Jaipur",
                    price_per_night=base_rate * 0.7,
                    total_price=base_rate * 0.7 * 3,
                    currency=currency,
                    rating=4.5,
                    amenities=["Free Wi-Fi", "Rooftop Cafe", "Air Conditioning", "Luggage Storage"],
                    booking_reference_url="https://example.com/accommodations/zostel-jaipur",
                    is_mock=True,
                ),
                AccommodationOption(
                    name="Shahpura House Heritage Hotel",
                    property_type="boutique",
                    location="Bani Park, Jaipur",
                    price_per_night=base_rate * 1.2,
                    total_price=base_rate * 1.2 * 3,
                    currency=currency,
                    rating=4.7,
                    amenities=["Pool", "Heritage Decor", "Restaurant", "Complimentary Breakfast"],
                    booking_reference_url="https://example.com/accommodations/shahpura-jaipur",
                    is_mock=True,
                ),
            ]
        elif "goa" in dest_lower:
            options = [
                AccommodationOption(
                    name="Santana Beach Resort",
                    property_type="resort",
                    location="Candolim, Goa",
                    price_per_night=base_rate * 1.1,
                    total_price=base_rate * 1.1 * 3,
                    currency=currency,
                    rating=4.4,
                    amenities=["Beach Access", "Pool", "Bar", "Free Wi-Fi"],
                    booking_reference_url="https://example.com/accommodations/santana-goa",
                    is_mock=True,
                ),
                AccommodationOption(
                    name="The Hosteller Goa Candolim",
                    property_type="hostel",
                    location="Candolim, Goa",
                    price_per_night=base_rate * 0.6,
                    total_price=base_rate * 0.6 * 3,
                    currency=currency,
                    rating=4.3,
                    amenities=["Social Lounge", "Air Conditioning", "Cafe"],
                    booking_reference_url="https://example.com/accommodations/hosteller-goa",
                    is_mock=True,
                ),
            ]
        else:
            options = [
                AccommodationOption(
                    name=f"[MOCK] Central City Hotel {destination}",
                    property_type="hotel",
                    location=f"Central District, {destination}",
                    price_per_night=base_rate,
                    total_price=base_rate * 3,
                    currency=currency,
                    rating=4.2,
                    amenities=["Free Wi-Fi", "Breakfast", "Gym"],
                    booking_reference_url=f"https://example.com/accommodations/{destination.lower().replace(' ', '-')}",
                    is_mock=True,
                )
            ]

        return {
            "destination": destination,
            "guests": guests,
            "budget_tier": budget_tier,
            "total_options": len(options),
            "accommodations": [opt.model_dump() for opt in options],
            "is_mock": True,
        }

