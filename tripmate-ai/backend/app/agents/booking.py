"""
TripMate AI - Booking Assistant Agent
Finds accommodation options, suggests transit routes, and enforces authorization safeguards.
CRITICAL: Never performs live monetary transactions or actual reservations without user approval.
"""

import time
from typing import Any, List, Optional
from pydantic import BaseModel, Field

from app.agents.base import BaseAgent
from app.llm.usage import TokenUsage
from app.prompts.system_prompts import BOOKING_ASSISTANT_SYSTEM_PROMPT
from app.prompts.templates import format_booking_prompt
from app.schemas.agent_output import AgentExecutionResult
from app.schemas.trip import (
    AccommodationOption,
    BudgetBreakdown,
    TripRequest,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AccommodationWrapper(BaseModel):
    """Wrapper model enabling Pydantic structured output for accommodation lists."""

    options: List[AccommodationOption] = Field(
        ..., description="Curated list of accommodation recommendations"
    )


class BookingAssistantAgent(BaseAgent):
    """Booking assistant finding vetted accommodation and transport options."""

    name = "BookingAssistantAgent"
    system_prompt = BOOKING_ASSISTANT_SYSTEM_PROMPT
    allowed_tools = ["search_accommodation", "estimate_travel_time"]

    async def run(
        self,
        trip_request: Optional[TripRequest] = None,
        budget: Optional[BudgetBreakdown] = None,
        destination: Optional[str] = None,
        days: int = 3,
        travelers: int = 1,
        **kwargs: Any,
    ) -> AgentExecutionResult:
        """Finds accommodation options and verifies booking requirements."""
        start_time = time.perf_counter()

        dest = trip_request.destination if trip_request else (destination or "Destination")
        dur = trip_request.days if trip_request else days
        trav = trip_request.travelers if trip_request else travelers
        curr = trip_request.currency if trip_request else "INR"
        accom_budget = budget.accommodation if budget else 6000.0

        logger.info("BookingAssistantAgent searching stays in %s (Budget: %s %s)", dest, accom_budget, curr)

        prompt = format_booking_prompt(
            destination=dest,
            days=dur,
            travelers=trav,
            accommodation_budget=accom_budget,
            currency=curr,
        )

        try:
            # Query the search_accommodation tool directly to get ground truth
            tool = self.registry.get("search_accommodation")
            raw_result = await tool.execute(
                destination=dest,
                guests=trav,
                budget_tier="mid" if accom_budget > 3000 else "budget",
            )

            options: List[AccommodationOption] = [
                AccommodationOption.model_validate(opt) for opt in raw_result.get("accommodations", [])
            ]

            latency_ms = (time.perf_counter() - start_time) * 1000.0

            return AgentExecutionResult(
                agent_name=self.name,
                status="success",
                output=options,
                tool_calls_made=[],
                token_usage=TokenUsage(),
                latency_ms=round(latency_ms, 2),
                errors=[],
            )

        except Exception as exc:
            logger.error("BookingAssistantAgent failed: %s", exc, exc_info=True)
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
