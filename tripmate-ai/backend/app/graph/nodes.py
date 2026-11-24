"""
TripMate AI - LangGraph Orchestration Nodes
Implements execution nodes for Research, Budget, Itinerary, Booking, Validation, Approval, and Finalization.
"""

from typing import Any, Dict, List, Optional
import uuid

from app.agents.booking import BookingAssistantAgent
from app.agents.budget import BudgetAgent
from app.agents.itinerary import ItineraryAgent
from app.agents.research import ResearchAgent
from app.graph.state import TripState
from app.schemas.agent_output import AgentExecutionResult
from app.schemas.trip import (
    AccommodationOption,
    BudgetBreakdown,
    DailyItinerary,
    DestinationResearch,
    TripRequest,
    TripResponse,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def research_node(state: TripState) -> Dict[str, Any]:
    """Autonomous Research Agent Node: discovers attractions and destination context."""
    logger.info("Executing Research Node for trip: %s", state.get("trip_id"))
    req: Optional[TripRequest] = state.get("user_request")
    rag_ctx: Optional[str] = state.get("retrieved_context")

    agent = ResearchAgent()
    try:
        result: AgentExecutionResult = await agent.run(
            trip_request=req,
            rag_context=rag_ctx,
        )
        research_data: Optional[DestinationResearch] = None
        if result.output:
            if isinstance(result.output, DestinationResearch):
                research_data = result.output
            elif isinstance(result.output, dict):
                research_data = DestinationResearch.model_validate(result.output)

        return {
            "destination_research": research_data,
            "agent_results": [result],
            "current_stage": "research",
        }
    except Exception as exc:
        err_msg = f"Research Node failed: {exc}"
        logger.error(err_msg, exc_info=True)
        return {
            "errors": [err_msg],
            "current_stage": "research",
        }


async def budget_node(state: TripState) -> Dict[str, Any]:
    """Autonomous Budget Agent Node: calculates categorical deterministic breakdown."""
    logger.info("Executing Budget Node for trip: %s", state.get("trip_id"))
    req: Optional[TripRequest] = state.get("user_request")

    agent = BudgetAgent()
    try:
        result: AgentExecutionResult = await agent.run(trip_request=req)
        budget_data: Optional[BudgetBreakdown] = None
        if result.output:
            if isinstance(result.output, BudgetBreakdown):
                budget_data = result.output
            elif isinstance(result.output, dict):
                budget_data = BudgetBreakdown.model_validate(result.output)

        return {
            "budget_analysis": budget_data,
            "agent_results": [result],
            "current_stage": "budget",
        }
    except Exception as exc:
        err_msg = f"Budget Node failed: {exc}"
        logger.error(err_msg, exc_info=True)
        return {
            "errors": [err_msg],
            "current_stage": "budget",
        }


async def itinerary_node(state: TripState) -> Dict[str, Any]:
    """Autonomous Itinerary Agent Node: synthesizes research and budget into daily plans."""
    logger.info("Executing Itinerary Node for trip: %s", state.get("trip_id"))
    req: Optional[TripRequest] = state.get("user_request")
    research: Optional[DestinationResearch] = state.get("destination_research")
    budget: Optional[BudgetBreakdown] = state.get("budget_analysis")

    agent = ItineraryAgent()
    try:
        result: AgentExecutionResult = await agent.run(
            trip_request=req,
            research=research,
            budget=budget,
        )
        days_list: List[DailyItinerary] = []
        if result.output:
            if isinstance(result.output, list):
                days_list = [
                    d if isinstance(d, DailyItinerary) else DailyItinerary.model_validate(d)
                    for d in result.output
                ]
            elif isinstance(result.output, dict) and "itinerary_days" in result.output:
                days_list = [
                    d if isinstance(d, DailyItinerary) else DailyItinerary.model_validate(d)
                    for d in result.output["itinerary_days"]
                ]

        return {
            "itinerary": days_list,
            "agent_results": [result],
            "current_stage": "itinerary",
        }
    except Exception as exc:
        err_msg = f"Itinerary Node failed: {exc}"
        logger.error(err_msg, exc_info=True)
        return {
            "errors": [err_msg],
            "current_stage": "itinerary",
        }


async def booking_node(state: TripState) -> Dict[str, Any]:
    """Booking Assistant Agent Node: searches accommodations and transit safeguards."""
    logger.info("Executing Booking Node for trip: %s", state.get("trip_id"))
    req: Optional[TripRequest] = state.get("user_request")
    budget: Optional[BudgetBreakdown] = state.get("budget_analysis")

    agent = BookingAssistantAgent()
    try:
        result: AgentExecutionResult = await agent.run(
            trip_request=req,
            budget=budget,
        )
        options: List[AccommodationOption] = []
        if result.output:
            if isinstance(result.output, list):
                options = [
                    o if isinstance(o, AccommodationOption) else AccommodationOption.model_validate(o)
                    for o in result.output
                ]
            elif isinstance(result.output, dict) and "options" in result.output:
                options = [
                    o if isinstance(o, AccommodationOption) else AccommodationOption.model_validate(o)
                    for o in result.output["options"]
                ]

        return {
            "accommodation_options": options,
            "agent_results": [result],
            "current_stage": "booking",
        }
    except Exception as exc:
        err_msg = f"Booking Node failed: {exc}"
        logger.error(err_msg, exc_info=True)
        return {
            "errors": [err_msg],
            "current_stage": "booking",
        }


def validation_node(state: TripState) -> Dict[str, Any]:
    """Validation Node: verifies completeness, budget bounds, and itinerary alignment."""
    logger.info("Executing Validation Node for trip: %s", state.get("trip_id"))
    req: Optional[TripRequest] = state.get("user_request")
    budget: Optional[BudgetBreakdown] = state.get("budget_analysis")
    itinerary: Optional[List[DailyItinerary]] = state.get("itinerary")
    options: Optional[List[AccommodationOption]] = state.get("accommodation_options")
    existing_errors: List[str] = list(state.get("errors") or [])
    new_errors: List[str] = []

    expected_days = req.days if req else 3
    actual_days = len(itinerary or [])
    if actual_days < expected_days:
        new_errors.append(f"Itinerary day count mismatch: expected {expected_days}, got {actual_days}")

    if req and budget:
        if budget.total_estimated_cost > req.budget * 1.20:
            new_errors.append(
                f"Budget exceeded: estimated {budget.total_estimated_cost} exceeds limit {req.budget * 1.20}"
            )

    if not options or len(options) == 0:
        new_errors.append("No valid accommodation options found")

    is_valid = len(new_errors) == 0
    revision_count = state.get("revision_count", 0)
    if not is_valid:
        revision_count += 1
        logger.warning(
            "Validation failed for trip %s: %s (revision %d)",
            state.get("trip_id"),
            new_errors,
            revision_count,
        )
    else:
        logger.info("Validation passed successfully for trip: %s", state.get("trip_id"))

    return {
        "is_valid": is_valid,
        "errors": new_errors,
        "revision_count": revision_count,
        "current_stage": "validation",
    }


def approval_node(state: TripState) -> Dict[str, Any]:
    """
    Human-in-the-Loop Approval Node.
    Executed when resumed from an interrupt. Records user decision.
    """
    trip_id = state.get("trip_id")
    approval_status = state.get("approval_status", "PENDING")
    comment = state.get("approval_comment")
    logger.info(
        "Executing Approval Node for trip %s: Status=%s, Comment=%s",
        trip_id,
        approval_status,
        comment,
    )

    return {
        "approval_status": approval_status,
        "approval_comment": comment,
        "current_stage": "approval",
    }


def finalize_node(state: TripState) -> Dict[str, Any]:
    """Finalize Node: compiles the comprehensive TripResponse output."""
    logger.info("Executing Finalize Node for trip: %s", state.get("trip_id"))
    req: Optional[TripRequest] = state.get("user_request")
    trip_id = state.get("trip_id") or str(uuid.uuid4())
    is_valid = state.get("is_valid", True)
    approval_status = state.get("approval_status", "NOT_REQUIRED")
    errors = state.get("errors") or []

    # Determine status
    if not is_valid and len(errors) > 0:
        status = "FAILED"
    elif approval_status == "REJECTED":
        status = "REJECTED"
    elif approval_status == "MODIFICATION_REQUESTED":
        status = "MODIFICATION_REQUESTED"
    elif approval_status == "PENDING":
        status = "PENDING_APPROVAL"
    else:
        status = "SUCCESS"

    final_resp = TripResponse(
        trip_id=trip_id,
        destination=req.destination if req else "Unknown",
        days=req.days if req else 3,
        travelers=req.travelers if req else 1,
        currency=req.currency if req else "INR",
        research=state.get("destination_research"),
        budget_analysis=state.get("budget_analysis"),
        itinerary=state.get("itinerary") or [],
        accommodation_options=state.get("accommodation_options") or [],
        approval_required=(approval_status == "PENDING"),
        approval_status=approval_status,
        status=status,
        errors=errors,
    )

    return {
        "final_response": final_resp,
        "current_stage": "finalized",
    }
