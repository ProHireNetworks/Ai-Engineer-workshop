"""
TripMate AI - Pydantic Structured Outputs Test Suite
Tests for TripRequest, BudgetBreakdown, DailyItinerary, DestinationResearch,
and API validation endpoint.
"""

import pytest
from starlette.testclient import TestClient

from app.schemas.trip import (
    AccommodationOption,
    Attraction,
    BudgetBreakdown,
    DailyItinerary,
    DestinationResearch,
    TripRequest,
    TripResponse,
    WeatherInformation,
)
from app.services.tool_calling_service import ToolCallingService


def test_trip_request_valid():
    """Verify standard valid TripRequest succeeds."""
    req = TripRequest(
        destination="Jaipur, Rajasthan",
        days=3,
        budget=15000.0,
        travelers=2,
        currency="inr",
        interests=["forts", "palaces"],
    )
    assert req.currency == "INR"
    assert req.destination == "Jaipur, Rajasthan"
    assert req.days == 3


def test_trip_request_invalid_currency():
    """Verify invalid currency code is rejected."""
    with pytest.raises(ValueError):
        TripRequest(
            destination="Paris",
            days=4,
            budget=1000.0,
            currency="EURO",  # Should be 3 chars
        )


def test_trip_request_invalid_duration():
    """Verify duration bounds (<1 or >30) are rejected."""
    with pytest.raises(ValueError):
        TripRequest(destination="Tokyo", days=0, budget=5000.0)

    with pytest.raises(ValueError):
        TripRequest(destination="Tokyo", days=35, budget=5000.0)


def test_trip_request_unrealistic_budget():
    """Verify budget validator flags unfeasible budget ($0.50 per person per day)."""
    with pytest.raises(ValueError) as exc_info:
        TripRequest(destination="Goa", days=10, budget=2.0, travelers=2)
    assert "unfeasible" in str(exc_info.value)


def test_deterministic_budget_breakdown_math():
    """Verify BudgetBreakdown computes exact totals without rounding errors."""
    b = BudgetBreakdown.calculate(
        destination="Kyoto",
        days=5,
        travelers=2,
        target_budget=50000.0,
        transportation=10000.50,
        accommodation=20000.25,
        food=12000.00,
        activities=5000.00,
        miscellaneous=1500.00,
        currency="INR",
    )
    assert b.total_estimated_cost == 48500.75
    assert b.is_within_budget is True
    assert b.savings_or_deficit == 1499.25
    assert b.calculation_method == "deterministic_python"


def test_api_trip_validate_endpoint_valid(client: TestClient):
    """Verify POST /api/v1/trips/validate with valid body returns 200."""
    payload = {
        "destination": "Goa, India",
        "days": 4,
        "budget": 20000.0,
        "travelers": 2,
        "currency": "INR",
        "interests": ["beaches", "seafood"],
    }
    response = client.post("/api/v1/trips/validate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["validated_request"]["destination"] == "Goa, India"


def test_api_trip_validate_endpoint_invalid(client: TestClient):
    """Verify POST /api/v1/trips/validate with invalid body returns 422."""
    payload = {
        "destination": "",  # Too short
        "days": 50,         # Out of range
        "budget": -100.0,   # Negative
    }
    response = client.post("/api/v1/trips/validate", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_tool_calling_service_structured():
    """Verify ToolCallingService.run_structured enforces target Pydantic schema."""
    service = ToolCallingService()
    plan, tool_results, usage = await service.run_structured(
        user_prompt="Plan a trip to Jaipur",
        response_model=DailyItinerary,
        enable_tools=True,
    )
    assert isinstance(plan, DailyItinerary)
    assert plan.day_number >= 1
    assert len(tool_results) > 0

