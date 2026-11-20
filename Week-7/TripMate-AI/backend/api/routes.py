
from fastapi import APIRouter, HTTPException

from backend.models.schemas import (
    TravelPreferences,
    TripPlanResponse,
)
from backend.graph.trip_graph import create_trip_graph

router = APIRouter(
    prefix="/api",
    tags=["Travel Planning"]
)


@router.post("/plan-trip", response_model=TripPlanResponse)
def plan_trip(preferences: TravelPreferences):
    """Generate a complete travel plan using the multi-agent workflow."""

    try:
        graph = create_trip_graph()

        result = graph.invoke({
            "preferences": preferences
        })

        return {
            "research": result["research"],
            "itinerary": result["itinerary"],
            "budget_analysis": result["budget_analysis"],
        }

    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail=f"Travel planning failed: {str(error)}"
        )
