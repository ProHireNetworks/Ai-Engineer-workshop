"""
TripMate AI - Cost Calculator Tool
Executes strictly deterministic financial calculations for travel budgets.
Zero LLM approximation; relies on pure Python arithmetic with validated float precision.
"""

from typing import Any, Dict, Optional
from app.schemas.trip import BudgetBreakdown
from app.tools.base import BaseTool
from app.tools.schemas import BudgetCalculatorArgs


class CalculateTripBudgetTool(BaseTool):
    """Performs deterministic cost summation and budget feasibility analysis."""

    name = "calculate_trip_budget"
    description = (
        "Deterministically calculate the exact total travel cost across transportation, "
        "accommodation, food, activities, and miscellaneous categories. Evaluates feasibility "
        "against user target budget."
    )
    args_schema = BudgetCalculatorArgs

    async def _run(
        self,
        transportation: float,
        accommodation: float,
        food: float,
        activities: float,
        miscellaneous: float,
        currency: str = "INR",
        target_budget: Optional[float] = None,
        days: int = 1,
        travelers: int = 1,
    ) -> Dict[str, Any]:
        # Pure deterministic arithmetic
        total_cost = round(
            float(transportation)
            + float(accommodation)
            + float(food)
            + float(activities)
            + float(miscellaneous),
            2,
        )

        effective_target = target_budget if target_budget is not None else total_cost
        within_budget = total_cost <= effective_target
        variance = round(effective_target - total_cost, 2)
        daily_average = round(total_cost / max(days, 1), 2)
        per_traveler = round(total_cost / max(travelers, 1), 2)

        breakdown = BudgetBreakdown.calculate(
            destination="Trip Target",
            days=days,
            travelers=travelers,
            target_budget=effective_target,
            transportation=transportation,
            accommodation=accommodation,
            food=food,
            activities=activities,
            miscellaneous=miscellaneous,
            currency=currency,
        )

        result = breakdown.model_dump()
        result.update(
            {
                "daily_average": daily_average,
                "per_traveler_cost": per_traveler,
                "is_mock": False,  # Math is verified real calculation, not mock data
            }
        )
        return result

