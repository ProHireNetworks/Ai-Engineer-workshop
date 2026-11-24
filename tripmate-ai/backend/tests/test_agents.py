"""
TripMate AI - Multi-Agent Test Suite (Phase 4)
Tests for independent agent execution: ResearchAgent, BudgetAgent, ItineraryAgent,
BookingAssistantAgent, and tool permission scoping.
"""

import pytest
from app.agents.booking import BookingAssistantAgent
from app.agents.budget import BudgetAgent
from app.agents.itinerary import ItineraryAgent
from app.agents.research import ResearchAgent
from app.schemas.agent_output import AgentExecutionResult
from app.schemas.trip import (
    AccommodationOption,
    BudgetBreakdown,
    DailyItinerary,
    DestinationResearch,
    TripRequest,
)


@pytest.fixture
def sample_trip_request():
    return TripRequest(
        destination="Jaipur, Rajasthan",
        days=3,
        budget=20000.0,
        travelers=2,
        currency="INR",
        interests=["forts", "culture", "street food"],
    )


@pytest.mark.asyncio
async def test_research_agent_run(sample_trip_request):
    """Verify ResearchAgent executes and outputs DestinationResearch."""
    agent = ResearchAgent()
    result = await agent.run(trip_request=sample_trip_request)

    assert isinstance(result, AgentExecutionResult)
    assert result.status == "success"
    assert isinstance(result.output, DestinationResearch)
    assert result.output.destination == sample_trip_request.destination
    assert len(result.output.overview) > 0


@pytest.mark.asyncio
async def test_budget_agent_run(sample_trip_request):
    """Verify BudgetAgent performs deterministic budget arithmetic."""
    agent = BudgetAgent()
    result = await agent.run(trip_request=sample_trip_request)

    assert isinstance(result, AgentExecutionResult)
    assert result.status == "success"
    assert isinstance(result.output, BudgetBreakdown)
    breakdown = result.output

    # Verify deterministic summation
    expected_sum = round(
        breakdown.transportation
        + breakdown.accommodation
        + breakdown.food
        + breakdown.activities
        + breakdown.miscellaneous,
        2,
    )
    assert breakdown.total_estimated_cost == expected_sum
    assert breakdown.calculation_method == "deterministic_python"
    assert breakdown.currency == "INR"


@pytest.mark.asyncio
async def test_itinerary_agent_run(sample_trip_request):
    """Verify ItineraryAgent outputs a day-wise itinerary schedule."""
    # Run research and budget first to provide context
    res_agent = ResearchAgent()
    bud_agent = BudgetAgent()
    res_out = (await res_agent.run(trip_request=sample_trip_request)).output
    bud_out = (await bud_agent.run(trip_request=sample_trip_request)).output

    itin_agent = ItineraryAgent()
    result = await itin_agent.run(
        trip_request=sample_trip_request,
        research=res_out,
        budget=bud_out,
    )

    assert isinstance(result, AgentExecutionResult)
    assert result.status == "success"
    days_list = result.output
    assert isinstance(days_list, list)
    assert len(days_list) == sample_trip_request.days
    assert all(isinstance(day, DailyItinerary) for day in days_list)
    assert days_list[0].day_number == 1


@pytest.mark.asyncio
async def test_booking_assistant_agent_run(sample_trip_request):
    """Verify BookingAssistantAgent outputs lodging recommendations."""
    bud_agent = BudgetAgent()
    bud_out = (await bud_agent.run(trip_request=sample_trip_request)).output

    booking_agent = BookingAssistantAgent()
    result = await booking_agent.run(
        trip_request=sample_trip_request,
        budget=bud_out,
    )

    assert isinstance(result, AgentExecutionResult)
    assert result.status == "success"
    options = result.output
    assert isinstance(options, list)
    assert len(options) > 0
    assert all(isinstance(opt, AccommodationOption) for opt in options)
    assert options[0].price_per_night > 0


def test_agent_tool_scoping():
    """Verify agents are strictly restricted to their allowed tools."""
    res_agent = ResearchAgent()
    scoped_res_tools = [t["function"]["name"] for t in res_agent.get_scoped_tools()]
    assert set(scoped_res_tools) == {
        "search_destination",
        "search_attractions",
        "retrieve_travel_knowledge",
    }

    bud_agent = BudgetAgent()
    scoped_bud_tools = [t["function"]["name"] for t in bud_agent.get_scoped_tools()]
    assert scoped_bud_tools == ["calculate_trip_budget"]

    booking_agent = BookingAssistantAgent()
    scoped_book_tools = [t["function"]["name"] for t in booking_agent.get_scoped_tools()]
    assert set(scoped_book_tools) == {"search_accommodation", "estimate_travel_time"}
