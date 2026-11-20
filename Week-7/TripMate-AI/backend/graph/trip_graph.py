
from typing import TypedDict

from langgraph.graph import StateGraph, START, END

from backend.models.schemas import (
    TravelPreferences,
    ResearchResult,
    TravelItinerary,
    BudgetAnalysis,
)

from backend.agents.research_agent import research_destination
from backend.agents.travel_planner import generate_itinerary
from backend.agents.budget_agent import analyze_budget


class TripState(TypedDict):
    preferences: TravelPreferences
    research: ResearchResult
    itinerary: TravelItinerary
    budget_analysis: BudgetAnalysis


def research_node(state: TripState):
    """Research the requested destination."""

    result = research_destination(state["preferences"])

    return {"research": result}


def planner_node(state: TripState):
    """Generate an itinerary using destination research."""

    result = generate_itinerary(
        state["preferences"],
        state["research"],
    )

    return {"itinerary": result}


def budget_node(state: TripState):
    """Analyze the generated itinerary against the budget."""

    result = analyze_budget(
        state["preferences"],
        state["itinerary"],
    )

    return {"budget_analysis": result}


def create_trip_graph():
    """Build and compile the TripMate multi-agent workflow."""

    workflow = StateGraph(TripState)

    workflow.add_node("research", research_node)
    workflow.add_node("planner", planner_node)
    workflow.add_node("budget", budget_node)

    workflow.add_edge(START, "research")
    workflow.add_edge("research", "planner")
    workflow.add_edge("planner", "budget")
    workflow.add_edge("budget", END)

    return workflow.compile()
