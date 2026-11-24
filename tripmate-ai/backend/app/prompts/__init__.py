"""TripMate AI Prompts Package."""

from app.prompts.system_prompts import (
    BOOKING_ASSISTANT_SYSTEM_PROMPT,
    BUDGET_AGENT_SYSTEM_PROMPT,
    ITINERARY_AGENT_SYSTEM_PROMPT,
    PROMPT_GUARD_SYSTEM_PROMPT,
    RESEARCH_AGENT_SYSTEM_PROMPT,
)
from app.prompts.templates import (
    format_booking_prompt,
    format_budget_prompt,
    format_itinerary_prompt,
    format_research_prompt,
)

__all__ = [
    "RESEARCH_AGENT_SYSTEM_PROMPT",
    "BUDGET_AGENT_SYSTEM_PROMPT",
    "ITINERARY_AGENT_SYSTEM_PROMPT",
    "BOOKING_ASSISTANT_SYSTEM_PROMPT",
    "PROMPT_GUARD_SYSTEM_PROMPT",
    "format_research_prompt",
    "format_budget_prompt",
    "format_itinerary_prompt",
    "format_booking_prompt",
]

