"""
TripMate AI - LangGraph Shared State
TypedDict state schema and reducer functions for multi-agent travel planning.
"""

from typing import Annotated, Any, Dict, List, Literal, Optional, TypedDict
from app.schemas.agent_output import AgentExecutionResult
from app.schemas.trip import (
    AccommodationOption,
    BudgetBreakdown,
    DailyItinerary,
    DestinationResearch,
    TripRequest,
    TripResponse,
)


def list_append_reducer(
    current: Optional[List[Any]], new_items: Optional[List[Any]]
) -> List[Any]:
    """Reducer that accumulates items across agent nodes without overwriting history."""
    current_list = list(current or [])
    if new_items:
        current_list.extend(new_items)
    return current_list


def last_value_reducer(current: Any, new_value: Any) -> Any:
    """Reducer that accepts the latest non-null value during concurrent steps."""
    return new_value if new_value is not None else current


class TripState(TypedDict, total=False):
    """Shared execution context threaded across all graph nodes."""

    trip_id: str
    user_request: TripRequest
    destination_research: Optional[DestinationResearch]
    budget_analysis: Optional[BudgetBreakdown]
    itinerary: Optional[List[DailyItinerary]]
    accommodation_options: Optional[List[AccommodationOption]]
    retrieved_context: Optional[str]
    agent_results: Annotated[List[AgentExecutionResult], list_append_reducer]
    errors: Annotated[List[str], list_append_reducer]
    approval_status: Literal["PENDING", "APPROVED", "REJECTED", "NOT_REQUIRED", "MODIFICATION_REQUESTED"]
    approval_comment: Optional[str]
    current_stage: Annotated[str, last_value_reducer]
    revision_count: int
    is_valid: bool
    final_response: Optional[TripResponse]
