
from datetime import date
from enum import Enum

from pydantic import BaseModel, Field, model_validator


class TravelStyle(str, Enum):
    BUDGET = "budget"
    BALANCED = "balanced"
    LUXURY = "luxury"
    ADVENTURE = "adventure"


class TravelPreferences(BaseModel):
    """User travel preferences."""

    origin: str = Field(..., min_length=2)
    destination: str = Field(..., min_length=2)

    start_date: date
    end_date: date

    travelers: int = Field(default=1, ge=1, le=20)
    budget: float = Field(..., gt=0)

    currency: str = "INR"
    travel_style: TravelStyle = TravelStyle.BALANCED

    interests: list[str] = Field(default_factory=list)
    special_requirements: str | None = None

    @model_validator(mode="after")
    def validate_dates(self):
        if self.end_date < self.start_date:
            raise ValueError("End date cannot be before start date")
        return self


class Activity(BaseModel):
    """Individual travel activity."""

    time: str
    title: str
    description: str
    location: str | None = None
    estimated_cost: float = Field(default=0, ge=0)


class DayPlan(BaseModel):
    """One day of the travel itinerary."""

    day_number: int = Field(..., ge=1)
    date: date
    title: str
    activities: list[Activity] = Field(default_factory=list)


class TravelItinerary(BaseModel):
    """Complete travel itinerary."""

    destination: str
    summary: str
    total_estimated_cost: float = Field(..., ge=0)
    currency: str = "INR"
    days: list[DayPlan] = Field(default_factory=list)
    tips: list[str] = Field(default_factory=list)
class ResearchResult(BaseModel):
    """Research information about a travel destination."""

    destination: str
    overview: str
    attractions: list[str] = Field(default_factory=list)
    local_foods: list[str] = Field(default_factory=list)
    transportation: list[str] = Field(default_factory=list)
    travel_tips: list[str] = Field(default_factory=list)
    important_notes: list[str] = Field(default_factory=list)

class BudgetAnalysis(BaseModel):
    """Budget breakdown and analysis for a trip."""

    total_budget: float = Field(..., gt=0)
    estimated_total_cost: float = Field(..., ge=0)
    remaining_budget: float
    within_budget: bool
    expense_breakdown: dict[str, float] = Field(default_factory=dict)
    recommendations: list[str] = Field(default_factory=list)

class TripPlanResponse(BaseModel):
    """Complete response from the TripMate AI multi-agent workflow."""

    research: ResearchResult
    itinerary: TravelItinerary
    budget_analysis: BudgetAnalysis
