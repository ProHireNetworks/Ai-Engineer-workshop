"""
TripMate AI - Research Agent
Discovers destination profile, tourist attractions, activities, and regional advice.
"""

import time
from typing import Any, List, Optional

from app.agents.base import BaseAgent
from app.llm.usage import TokenUsage
from app.prompts.system_prompts import RESEARCH_AGENT_SYSTEM_PROMPT
from app.prompts.templates import format_research_prompt
from app.schemas.agent_output import AgentExecutionResult
from app.schemas.trip import Attraction, DestinationResearch, TripRequest
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ResearchAgent(BaseAgent):
    """Autonomous agent tasked with destination discovery and attraction curation."""

    name = "ResearchAgent"
    system_prompt = RESEARCH_AGENT_SYSTEM_PROMPT
    allowed_tools = ["search_destination", "search_attractions", "retrieve_travel_knowledge"]

    async def run(
        self,
        trip_request: Optional[TripRequest] = None,
        destination: Optional[str] = None,
        days: int = 3,
        interests: Optional[List[str]] = None,
        travelers: int = 1,
        rag_context: Optional[str] = None,
        **kwargs: Any,
    ) -> AgentExecutionResult:
        """Executes research workflow for destination and attractions."""
        start_time = time.perf_counter()

        dest = trip_request.destination if trip_request else (destination or "Unknown Destination")
        dur = trip_request.days if trip_request else days
        trav = trip_request.travelers if trip_request else travelers
        ints = trip_request.interests if trip_request else (interests or [])

        logger.info("ResearchAgent executing for '%s' (%d days)", dest, dur)

        prompt = format_research_prompt(
            destination=dest,
            days=dur,
            interests=ints,
            travelers=trav,
        )

        if rag_context:
            prompt += f"\n\n### Curated Tourism Knowledge Base:\n{rag_context}"

        try:
            output_model, tool_results, usage = await self.execute_reasoning_cycle(
                user_prompt=prompt,
                response_model=DestinationResearch,
                max_rounds=3,
            )

            latency_ms = (time.perf_counter() - start_time) * 1000.0

            # Ensure model fields match destination
            output_model.destination = dest

            return AgentExecutionResult(
                agent_name=self.name,
                status="success",
                output=output_model,
                tool_calls_made=tool_results,
                token_usage=usage,
                latency_ms=round(latency_ms, 2),
                errors=[],
            )

        except Exception as exc:
            logger.error("ResearchAgent failed: %s", exc, exc_info=True)
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
