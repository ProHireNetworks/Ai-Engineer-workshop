"""
TripMate AI - Tool Argument Schemas
Pydantic v2 schemas enforcing strict validation on inputs provided to tools.
"""

from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator


class DestinationSearchArgs(BaseModel):
    """Arguments for search_destination tool."""

    destination: str = Field(
        ..., min_length=2, max_length=100, description="City, region, or country to search"
    )
    interests: List[str] = Field(
        default_factory=list, description="Traveler interests to bias search results"
    )


class AttractionsSearchArgs(BaseModel):
    """Arguments for search_attractions tool."""

    destination: str = Field(
        ..., min_length=2, max_length=100, description="Destination to discover attractions in"
    )
    category: Optional[str] = Field(
        default=None, description="Optional category filter (e.g. Historical, Nature, Food, Art)"
    )
    limit: int = Field(default=5, ge=1, le=20, description="Maximum number of attractions to return")


class WeatherArgs(BaseModel):
    """Arguments for get_weather tool."""

    destination: str = Field(
        ..., min_length=2, max_length=100, description="Destination city or region"
    )
    travel_date: Optional[str] = Field(
        default=None, description="Travel date or month (e.g. '2026-11-25', 'November')"
    )


class BudgetCalculatorArgs(BaseModel):
    """Arguments for calculate_trip_budget tool."""

    transportation: float = Field(..., ge=0.0, description="Estimated transportation expenditure")
    accommodation: float = Field(..., ge=0.0, description="Estimated accommodation expenditure")
    food: float = Field(..., ge=0.0, description="Estimated food and dining expenditure")
    activities: float = Field(..., ge=0.0, description="Estimated tours, admissions, and activities")
    miscellaneous: float = Field(..., ge=0.0, description="Contingency and shopping allowance")
    currency: str = Field(default="INR", min_length=3, max_length=3, description="ISO currency code")
    target_budget: Optional[float] = Field(default=None, ge=0.0, description="User target budget to evaluate against")
    days: int = Field(default=1, ge=1, le=30, description="Total days")
    travelers: int = Field(default=1, ge=1, le=20, description="Number of travelers")

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        return v.strip().upper()


class TravelTimeArgs(BaseModel):
    """Arguments for estimate_travel_time tool."""

    origin: str = Field(..., min_length=2, description="Departure location")
    destination: str = Field(..., min_length=2, description="Arrival location")
    mode: Literal["driving", "transit", "flight", "walking"] = Field(
        default="driving", description="Primary mode of transportation"
    )


class AccommodationSearchArgs(BaseModel):
    """Arguments for search_accommodation tool."""

    destination: str = Field(
        ..., min_length=2, max_length=100, description="City or locality to find lodging in"
    )
    check_in: Optional[str] = Field(default=None, description="Check-in date (YYYY-MM-DD)")
    check_out: Optional[str] = Field(default=None, description="Check-out date (YYYY-MM-DD)")
    guests: int = Field(default=1, ge=1, le=20, description="Number of guests")
    budget_tier: Literal["budget", "mid", "luxury"] = Field(
        default="mid", description="Price tier for accommodation"
    )


class RAGSearchArgs(BaseModel):
    """Arguments for retrieve_travel_knowledge tool."""

    query: str = Field(..., min_length=2, description="Semantic search query or question")
    destination: Optional[str] = Field(
        default=None, description="Optional destination filter (e.g. 'Jaipur', 'Goa')"
    )
    top_k: int = Field(default=3, ge=1, le=10, description="Number of relevant chunks to retrieve")

