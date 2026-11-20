
import pytest
from pydantic import ValidationError

from backend.models.schemas import (
    TravelPreferences,
    TravelStyle,
    Activity,
    BudgetAnalysis,
)


def sample_preferences():
    return TravelPreferences(
        origin="Hyderabad",
        destination="Goa",
        start_date="2026-12-10",
        end_date="2026-12-13",
        travelers=2,
        budget=15000,
        currency="INR",
        travel_style=TravelStyle.BALANCED,
        interests=["beaches", "food"],
    )


def test_valid_travel_preferences():
    preferences = sample_preferences()

    assert preferences.origin == "Hyderabad"
    assert preferences.destination == "Goa"
    assert preferences.travelers == 2


def test_invalid_travel_dates():
    with pytest.raises(ValidationError):
        TravelPreferences(
            origin="Hyderabad",
            destination="Goa",
            start_date="2026-12-15",
            end_date="2026-12-10",
            travelers=2,
            budget=15000,
        )


def test_travelers_must_be_at_least_one():
    with pytest.raises(ValidationError):
        TravelPreferences(
            origin="Hyderabad",
            destination="Goa",
            start_date="2026-12-10",
            end_date="2026-12-13",
            travelers=0,
            budget=15000,
        )


def test_activity_default_cost():
    activity = Activity(
        time="10:00 AM",
        title="Beach Visit",
        description="Enjoy the beach.",
    )

    assert activity.estimated_cost == 0


def test_budget_analysis():
    analysis = BudgetAnalysis(
        total_budget=15000,
        estimated_total_cost=12000,
        remaining_budget=3000,
        within_budget=True,
        expense_breakdown={},
        recommendations=["Keep extra money for emergencies."],
    )

    assert analysis.within_budget is True
    assert analysis.remaining_budget == 3000
