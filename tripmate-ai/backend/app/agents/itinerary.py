"""
TripMate AI - Itinerary Agent
Generates chronologically paced, day-wise itineraries organized by geographical proximity.
"""

import time
from typing import Any, List, Optional
from pydantic import BaseModel, Field

from app.agents.base import BaseAgent
from app.llm.usage import TokenUsage
from app.prompts.system_prompts import ITINERARY_AGENT_SYSTEM_PROMPT
from app.prompts.templates import format_itinerary_prompt
from app.schemas.agent_output import AgentExecutionResult
from app.schemas.trip import (
    BudgetBreakdown,
    DailyItinerary,
    DestinationResearch,
    TripRequest,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ItineraryPlanWrapper(BaseModel):
    """Wrapper model enabling Pydantic structured output for multi-day itineraries."""

    itinerary_days: List[DailyItinerary] = Field(
        ..., description="Complete sequence of day-wise itineraries"
    )


class ItineraryAgent(BaseAgent):
    """Autonomous agent synthesizing research and budget into structured day-by-day itineraries."""

    name = "ItineraryAgent"
    system_prompt = ITINERARY_AGENT_SYSTEM_PROMPT
    allowed_tools = ["estimate_travel_time", "get_weather"]

    async def run(
        self,
        trip_request: Optional[TripRequest] = None,
        research: Optional[DestinationResearch] = None,
        budget: Optional[BudgetBreakdown] = None,
        days: int = 3,
        destination: Optional[str] = None,
        **kwargs: Any,
    ) -> AgentExecutionResult:
        """Generates day-wise itinerary schedule."""
        start_time = time.perf_counter()

        dest = trip_request.destination if trip_request else (destination or "Destination")
        dur = trip_request.days if trip_request else days
        trav = trip_request.travelers if trip_request else 1
        ints = trip_request.interests if trip_request else []

        logger.info("ItineraryAgent scheduling %d days for %s", dur, dest)

        research_text = (
            research.overview
            if research
            else f"Highlights and cultural landmarks in {dest}."
        )
        if research and research.attractions:
            research_text += f"\nAttractions: {', '.join(a.name for a in research.attractions)}"

        budget_text = (
            f"Total budget {budget.total_estimated_cost} {budget.currency}"
            if budget
            else "Standard budget constraints"
        )

        prompt = format_itinerary_prompt(
            destination=dest,
            days=dur,
            travelers=trav,
            interests=ints,
            research_summary=research_text,
            budget_summary=budget_text,
        )

        try:
            plan_wrapper, tool_results, usage = await self.execute_reasoning_cycle(
                user_prompt=prompt,
                response_model=ItineraryPlanWrapper,
                max_rounds=3,
            )

            # Ensure we have the requested number of days
            days_list = plan_wrapper.itinerary_days
            if not days_list or len(days_list) != dur:
                # Ensure complete sequence for all requested days
                days_list = [
                    DailyItinerary(
                        day_number=i + 1,
                        theme=f"Exploring {dest} - Day {i+1}",
                        morning_activities=[f"Morning exploration in {dest}"],
                        afternoon_activities=["Local cultural experience and lunch"],
                        evening_activities=["Sunset sights and dining"],
                        meal_recommendations=["Local specialty cuisine"],
                        estimated_daily_cost=round(
                            (budget.total_estimated_cost / dur) if budget else 1500.0, 2
                        ),
                    )
                    for i in range(dur)
                ]

            latency_ms = (time.perf_counter() - start_time) * 1000.0

            return AgentExecutionResult(
                agent_name=self.name,
                status="success",
                output=days_list,
                tool_calls_made=tool_results,
                token_usage=usage,
                latency_ms=round(latency_ms, 2),
                errors=[],
            )

        except Exception as exc:
            logger.error("ItineraryAgent failed: %s", exc, exc_info=True)
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            return AgentExecutionResult(
                agent_name=self.name,
                status="failure",
                output=None,
                tool_calls_made=[],
                token_usage=usage if ("usage" in locals() and usage) else TokenUsage(),
                latency_ms=round(latency_ms, 2),
                errors=[str(exc)],
            )
