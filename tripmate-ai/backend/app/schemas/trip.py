"""
TripMate AI - Travel Planning Schemas
Pydantic v2 schemas for trip requests, destination research, budget breakdown,
itineraries, accommodations, weather, and synthesized trip responses.
"""

from datetime import datetime, timezone
from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class TripRequest(BaseModel):
    """User submission specification for travel itinerary generation."""

    destination: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Target destination city, region, or country",
        examples=["Jaipur, India", "Kyoto, Japan"],
    )
    days: int = Field(
        ...,
        ge=1,
        le=30,
        description="Trip duration in calendar days (1 to 30 days)",
        examples=[3, 7],
    )
    budget: float = Field(
        ...,
        gt=0.0,
        description="Target total expenditure ceiling in designated currency",
        examples=[25000.0, 1500.0],
    )
    travelers: int = Field(
        default=1,
        ge=1,
        le=20,
        description="Total number of travelers participating in the trip",
    )
    currency: str = Field(
        default="INR",
        min_length=3,
        max_length=3,
        description="Three-letter ISO 4217 currency code",
        examples=["INR", "USD", "EUR", "JPY"],
    )
    interests: List[str] = Field(
        default_factory=list,
        max_length=15,
        description="Key interests or focus areas for the traveler",
        examples=[["historical forts", "local street food", "photography"]],
    )
    travel_dates: Optional[str] = Field(
        default=None,
        description="Preferred departure or travel period (e.g. 'November 2026', '2026-12-15')",
    )
    special_requirements: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Accessibility, dietary restrictions, or family travel considerations",
    )

    @field_validator("currency")
    @classmethod
    def validate_currency_code(cls, v: str) -> str:
        upper = v.strip().upper()
        if not upper.isalpha() or len(upper) != 3:
            raise ValueError("Currency must be a valid 3-letter alphabetic ISO code (e.g. INR, USD, EUR).")
        return upper

    @field_validator("destination")
    @classmethod
    def validate_destination_name(cls, v: str) -> str:
        cleaned = v.strip()
        if len(cleaned) < 2:
            raise ValueError("Destination must be at least 2 characters long.")
        return cleaned

    @model_validator(mode="after")
    def validate_budget_feasibility(self) -> "TripRequest":
        """Ensures the per-person daily budget is not unrealistically minuscule."""
        daily_per_person = self.budget / (self.days * self.travelers)
        if daily_per_person < 1.0:
            raise ValueError(
                f"Total budget of {self.budget} {self.currency} for {self.travelers} "
                f"travelers across {self.days} days yields less than 1.0 per person/day, which is unfeasible."
            )
        return self


class Attraction(BaseModel):
    """Tourist attraction, cultural landmark, or point of interest."""

    name: str = Field(..., description="Attraction name")
    category: str = Field(default="Culture", description="Category (e.g. Historical, Nature, Culinary, Adventure)")
    description: str = Field(..., description="Highlights, significance, and travel advice")
    estimated_duration_hours: float = Field(default=2.0, ge=0.5, le=12.0)
    admission_fee: float = Field(default=0.0, ge=0.0, description="Admission fee per adult")
    currency: str = Field(default="INR")
    location_area: Optional[str] = Field(default=None, description="Neighborhood or geographic zone")


class WeatherInformation(BaseModel):
    """Regional weather outlook and seasonal considerations."""

    destination: str
    season_or_period: str
    forecast_summary: str
    average_temp_celsius: float
    min_temp_celsius: float
    max_temp_celsius: float
    precipitation_chance_pct: int = Field(default=10, ge=0, le=100)
    travel_suitability: Literal["optimal", "favorable", "moderate", "challenging"] = "favorable"
    is_mock: bool = Field(default=True)


class DestinationResearch(BaseModel):
    """Synthesized research output compiled by the Research Agent."""

    destination: str
    overview: str = Field(..., description="Comprehensive destination profile and cultural context")
    country: str = Field(default="Unknown")
    attractions: List[Attraction] = Field(default_factory=list)
    recommended_activities: List[str] = Field(default_factory=list)
    local_transportation_tips: str = Field(default="Use metro, licensed taxis, or local transit.")
    best_time_to_visit: str = Field(default="October through March")
    is_mock: bool = Field(default=True)


class BudgetBreakdown(BaseModel):
    """Deterministic financial breakdown produced by the Budget Agent."""

    destination: str
    days: int
    travelers: int
    currency: str
    transportation: float = Field(..., ge=0.0)
    accommodation: float = Field(..., ge=0.0)
    food: float = Field(..., ge=0.0)
    activities: float = Field(..., ge=0.0)
    miscellaneous: float = Field(..., ge=0.0)
    total_estimated_cost: float = Field(..., ge=0.0)
    target_budget: float = Field(..., ge=0.0)
    is_within_budget: bool
    savings_or_deficit: float
    calculation_method: Literal["deterministic_python", "estimated_model"] = "deterministic_python"

    @classmethod
    def calculate(
        cls,
        destination: str,
        days: int,
        travelers: int,
        target_budget: float,
        transportation: float,
        accommodation: float,
        food: float,
        activities: float,
        miscellaneous: float,
        currency: str = "INR",
    ) -> "BudgetBreakdown":
        """Calculates total expense deterministically with strict floating-point rounding."""
        total = round(transportation + accommodation + food + activities + miscellaneous, 2)
        variance = round(target_budget - total, 2)
        within_budget = total <= target_budget

        return cls(
            destination=destination,
            days=days,
            travelers=travelers,
            currency=currency,
            transportation=round(transportation, 2),
            accommodation=round(accommodation, 2),
            food=round(food, 2),
            activities=round(activities, 2),
            miscellaneous=round(miscellaneous, 2),
            total_estimated_cost=total,
            target_budget=round(target_budget, 2),
            is_within_budget=within_budget,
            savings_or_deficit=variance,
            calculation_method="deterministic_python",
        )


class DailyItinerary(BaseModel):
    """Day-wise scheduled travel plan generated by the Itinerary Agent."""

    day_number: int = Field(..., ge=1, le=30)
    theme: str = Field(default="Exploration & Sights", description="Theme of the day")
    morning_activities: List[str] = Field(default_factory=list)
    afternoon_activities: List[str] = Field(default_factory=list)
    evening_activities: List[str] = Field(default_factory=list)
    meal_recommendations: List[str] = Field(default_factory=list)
    estimated_daily_cost: float = Field(default=0.0, ge=0.0)
    transit_tips: str = Field(default="Walking and short cab rides.")


class AccommodationOption(BaseModel):
    """Lodging recommendation produced by the Booking Assistant Agent."""

    name: str
    property_type: Literal["hotel", "resort", "hostel", "homestay", "boutique"] = "hotel"
    location: str
    price_per_night: float = Field(..., ge=0.0)
    total_price: float = Field(..., ge=0.0)
    currency: str = "INR"
    rating: float = Field(default=4.0, ge=1.0, le=5.0)
    amenities: List[str] = Field(default_factory=list)
    booking_reference_url: Optional[str] = None
    is_mock: bool = Field(default=True)


class TripResponse(BaseModel):
    """Complete structured JSON response returned to the client."""

    trip_id: str
    destination: str
    days: int
    travelers: int = 1
    currency: str = "INR"
    research: Optional[DestinationResearch] = None
    budget_analysis: Optional[BudgetBreakdown] = None
    itinerary: List[DailyItinerary] = Field(default_factory=list)
    accommodation_options: List[AccommodationOption] = Field(default_factory=list)
    approval_required: bool = False
    approval_status: Literal["PENDING", "APPROVED", "REJECTED", "NOT_REQUIRED", "MODIFICATION_REQUESTED"] = "NOT_REQUIRED"
    status: Literal["SUCCESS", "PENDING_APPROVAL", "REJECTED", "FAILED", "MODIFICATION_REQUESTED"] = "SUCCESS"
    errors: List[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

