"""
TripMate AI - Budget Agent
Computes categorical expenditure estimates and enforces deterministic arithmetic.
"""

import time
from typing import Any, Optional

from app.agents.base import BaseAgent
from app.llm.usage import TokenUsage
from app.prompts.system_prompts import BUDGET_AGENT_SYSTEM_PROMPT
from app.prompts.templates import format_budget_prompt
from app.schemas.agent_output import AgentExecutionResult
from app.schemas.trip import BudgetBreakdown, DestinationResearch, TripRequest
from app.utils.logger import get_logger

logger = get_logger(__name__)


class BudgetAgent(BaseAgent):
    """Financial calculation agent using deterministic Python budgeting."""

    name = "BudgetAgent"
    system_prompt = BUDGET_AGENT_SYSTEM_PROMPT
    allowed_tools = ["calculate_trip_budget"]

    async def run(
        self,
        trip_request: Optional[TripRequest] = None,
        destination: Optional[str] = None,
        days: int = 3,
        budget: float = 20000.0,
        travelers: int = 1,
        currency: str = "INR",
        research: Optional[DestinationResearch] = None,
        **kwargs: Any,
    ) -> AgentExecutionResult:
        """Calculates deterministic budget breakdown for the trip."""
        start_time = time.perf_counter()

        dest = trip_request.destination if trip_request else (destination or "Destination")
        dur = trip_request.days if trip_request else days
        curr = trip_request.currency if trip_request else currency
        target_b = trip_request.budget if trip_request else budget
        trav = trip_request.travelers if trip_request else travelers

        logger.info("BudgetAgent calculating budget for %s (Target: %s %s)", dest, target_b, curr)

        try:
            # Deterministic categorical ratio allocations
            # Lodging ~35%, Transport ~25%, Food ~22%, Activities ~12%, Misc ~6%
            alloc_transport = round(target_b * 0.25, 2)
            alloc_accom = round(target_b * 0.35, 2)
            alloc_food = round(target_b * 0.22, 2)
            alloc_activities = round(target_b * 0.12, 2)
            alloc_misc = round(target_b * 0.06, 2)

            # Invoke calculate_trip_budget tool deterministically
            tool_call_input = {
                "transportation": alloc_transport,
                "accommodation": alloc_accom,
                "food": alloc_food,
                "activities": alloc_activities,
                "miscellaneous": alloc_misc,
                "currency": curr,
                "target_budget": target_b,
                "days": dur,
                "travelers": trav,
            }

            calc_tool = self.registry.get("calculate_trip_budget")
            raw_result = await calc_tool.execute(**tool_call_input)

            budget_model = BudgetBreakdown(
                destination=dest,
                days=dur,
                travelers=trav,
                currency=curr,
                transportation=raw_result["transportation"],
                accommodation=raw_result["accommodation"],
                food=raw_result["food"],
                activities=raw_result["activities"],
                miscellaneous=raw_result["miscellaneous"],
                total_estimated_cost=raw_result["total_estimated_cost"],
                target_budget=raw_result["target_budget"],
                is_within_budget=raw_result["is_within_budget"],
                savings_or_deficit=raw_result["savings_or_deficit"],
                calculation_method="deterministic_python",
            )

            latency_ms = (time.perf_counter() - start_time) * 1000.0

            return AgentExecutionResult(
                agent_name=self.name,
                status="success",
                output=budget_model,
                tool_calls_made=[],
                token_usage=TokenUsage(),
                latency_ms=round(latency_ms, 2),
                errors=[],
            )

        except Exception as exc:
            logger.error("BudgetAgent calculation failed: %s", exc, exc_info=True)
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            return AgentExecutionResult(
                agent_name=self.name,
                status="failure",
                output=None,
                tool_calls_made=[],
                token_usage=TokenUsage(),
                latency_ms=round(latency_ms, 2),
                errors=[str(exc)],
            )
