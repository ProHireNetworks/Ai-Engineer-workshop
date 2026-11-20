
from backend.models.schemas import (
    TravelPreferences,
    TravelItinerary,
    BudgetAnalysis,
)


def analyze_budget(
    preferences: TravelPreferences,
    itinerary: TravelItinerary,
) -> BudgetAnalysis:
    """Analyze the itinerary cost against the user's travel budget."""

    estimated_cost = itinerary.total_estimated_cost
    total_budget = preferences.budget

    remaining = total_budget - estimated_cost

    recommendations = []

    if remaining < 0:
        recommendations.append(
            "Reduce accommodation, food, or activity expenses "
            "to stay within budget."
        )
    else:
        recommendations.append(
            "The estimated trip cost is within the specified budget."
        )

    if estimated_cost > total_budget * 0.9:
        recommendations.append(
            "Keep some extra money for unexpected expenses."
        )

    return BudgetAnalysis(
        total_budget=total_budget,
        estimated_total_cost=estimated_cost,
        remaining_budget=remaining,
        within_budget=estimated_cost <= total_budget,
        expense_breakdown={},
        recommendations=recommendations,
    )
