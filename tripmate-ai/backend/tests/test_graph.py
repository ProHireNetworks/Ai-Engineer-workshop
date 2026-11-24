"""
Unit and integration tests for LangGraph StateGraph, nodes, and state reducers.
"""

import pytest
from app.graph.nodes import (
    approval_node,
    finalize_node,
    validation_node,
)
from app.graph.state import TripState, list_append_reducer
from app.graph.workflow import (
    build_trip_graph,
    route_after_validation,
    trip_graph_direct,
)
from app.schemas.agent_output import AgentExecutionResult
from app.schemas.trip import (
    AccommodationOption,
    BudgetBreakdown,
    DailyItinerary,
    DestinationResearch,
    TripRequest,
)


def test_list_append_reducer():
    """Verify state reducer accumulates items without clobbering previous list elements."""
    base = ["item1", "item2"]
    res1 = list_append_reducer(base, ["item3"])
    assert res1 == ["item1", "item2", "item3"]

    # When None or empty
    assert list_append_reducer(None, ["new"]) == ["new"]
    assert list_append_reducer(base, None) == ["item1", "item2"]


def test_validation_node_logic():
    """Verify validation node flags missing itinerary days or budget overages."""
    req = TripRequest(destination="Jaipur", days=3, budget=30000.0)

    # Incomplete itinerary (only 1 day instead of 3)
    state_invalid: TripState = {
        "trip_id": "test-val-1",
        "user_request": req,
        "itinerary": [
            DailyItinerary(
                day_number=1,
                theme="Arrival",
                morning_activities=["Arrival"],
                afternoon_activities=["City Palace"],
                evening_activities=["Market"],
            )
        ],
        "budget_analysis": BudgetBreakdown.calculate(
            destination="Jaipur",
            days=3,
            travelers=1,
            target_budget=30000.0,
            transportation=5000,
            accommodation=10000,
            food=5000,
            activities=3000,
            miscellaneous=2000,
        ),
        "accommodation_options": [
            AccommodationOption(
                name="Heritage Haveli",
                property_type="hotel",
                location="Jaipur Old City",
                price_per_night=3000.0,
                total_price=9000.0,
            )
        ],
        "revision_count": 0,
    }

    result = validation_node(state_invalid)
    assert result["is_valid"] is False
    assert result["revision_count"] == 1
    assert any("mismatch" in e for e in result["errors"])

    # Valid state
    state_valid: TripState = {
        "trip_id": "test-val-2",
        "user_request": req,
        "itinerary": [
            DailyItinerary(
                day_number=1,
                theme="Day 1",
                morning_activities=["Palace"],
                afternoon_activities=["Fort"],
                evening_activities=["Bazaar"],
            ),
            DailyItinerary(
                day_number=2,
                theme="Day 2",
                morning_activities=["Museum"],
                afternoon_activities=["Hawa Mahal"],
                evening_activities=["Dinner"],
            ),
            DailyItinerary(
                day_number=3,
                theme="Day 3",
                morning_activities=["Jantar Mantar"],
                afternoon_activities=["Crafts"],
                evening_activities=["Departure"],
            ),
        ],
        "budget_analysis": BudgetBreakdown.calculate(
            destination="Jaipur",
            days=3,
            travelers=1,
            target_budget=30000.0,
            transportation=5000,
            accommodation=10000,
            food=5000,
            activities=3000,
            miscellaneous=2000,
        ),
        "accommodation_options": [
            AccommodationOption(
                name="Heritage Haveli",
                property_type="hotel",
                location="Jaipur Old City",
                price_per_night=3000.0,
                total_price=9000.0,
            )
        ],
        "revision_count": 0,
    }
    result_valid = validation_node(state_valid)
    assert result_valid["is_valid"] is True
    assert result_valid["errors"] == []


def test_route_after_validation():
    """Verify conditional edge routing rules."""
    # Invalid with revisions remaining -> itinerary
    assert route_after_validation({"is_valid": False, "revision_count": 1}) == "itinerary"

    # Invalid with max revisions -> finalize
    assert route_after_validation({"is_valid": False, "revision_count": 3}) == "finalize"

    # Valid with PENDING approval -> approval
    assert (
        route_after_validation({"is_valid": True, "approval_status": "PENDING"}) == "approval"
    )

    # Valid and approved -> finalize
    assert (
        route_after_validation({"is_valid": True, "approval_status": "APPROVED"}) == "finalize"
    )
    assert (
        route_after_validation({"is_valid": True, "approval_status": "NOT_REQUIRED"}) == "finalize"
    )


def test_finalize_node():
    """Verify finalize node produces valid TripResponse."""
    req = TripRequest(destination="Jaipur", days=3, budget=30000.0)
    research = DestinationResearch(
        destination="Jaipur",
        overview="Pink City with magnificent royal heritage.",
        country="India",
    )
    budget = BudgetBreakdown.calculate(
        destination="Jaipur",
        days=3,
        travelers=1,
        target_budget=30000.0,
        transportation=5000,
        accommodation=10000,
        food=5000,
        activities=3000,
        miscellaneous=2000,
    )
    state: TripState = {
        "trip_id": "trip-fin-123",
        "user_request": req,
        "destination_research": research,
        "budget_analysis": budget,
        "is_valid": True,
        "approval_status": "APPROVED",
        "itinerary": [],
        "accommodation_options": [],
        "agent_results": [],
    }

    res = finalize_node(state)
    final_resp = res["final_response"]
    assert final_resp is not None
    assert final_resp.trip_id == "trip-fin-123"
    assert final_resp.destination == "Jaipur"
    assert final_resp.status == "SUCCESS"


@pytest.mark.asyncio
async def test_end_to_end_graph_execution():
    """Test full multi-agent StateGraph execution without interrupts."""
    req = TripRequest(
        destination="Jaipur",
        days=3,
        budget=35000.0,
        currency="INR",
        interests=["culture", "palaces"],
    )
    initial_state: TripState = {
        "trip_id": "test-e2e-trip-1",
        "user_request": req,
        "approval_status": "NOT_REQUIRED",
        "revision_count": 0,
    }

    config = {"configurable": {"thread_id": "test-e2e-thread-1"}}
    final_state = await trip_graph_direct.ainvoke(initial_state, config=config)

    assert final_state["current_stage"] == "finalized"
    assert final_state["destination_research"] is not None
    assert final_state["budget_analysis"] is not None
    assert len(final_state["itinerary"]) == 3
    assert len(final_state["accommodation_options"]) >= 1
    assert final_state["final_response"] is not None
    assert final_state["final_response"].status in ("SUCCESS", "PENDING_APPROVAL")
    assert len(final_state["agent_results"]) >= 4
