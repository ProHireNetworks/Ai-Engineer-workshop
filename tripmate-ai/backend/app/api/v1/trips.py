"""
TripMate AI - Trip Planning & Validation Endpoints
Provides validation services and multi-agent trip orchestration endpoints.
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.api.deps import verify_api_key
from app.database.repository import TripRepository
from app.database.session import async_session_maker
from app.schemas.trip import TripRequest, TripResponse
from app.services.approval_service import approval_service
from app.services.prompt_guard import PromptGuardService
from app.utils.logger import get_logger

router = APIRouter(prefix="/trips", tags=["Trips"])
logger = get_logger(__name__)


class TripValidateResponse(BaseModel):
    valid: bool = Field(default=True, description="Whether the request is strictly valid")
    message: str = Field(default="Trip request parameters validated successfully.")
    validated_request: TripRequest = Field(..., description="Parsed and validated trip request")


class TripPlanningResult(BaseModel):
    """Wrapper response for initiating a trip planning workflow."""

    trip_id: str
    status: str = Field(..., description="PENDING_APPROVAL or COMPLETED")
    is_paused: bool = Field(..., description="Whether workflow is paused awaiting review")
    message: str
    data: Optional[Dict[str, Any]] = None
    response: Optional[TripResponse] = None


@router.post(
    "/validate",
    response_model=TripValidateResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate Trip Parameters",
    description="Validates trip duration, budget feasibility, traveler count, and currency against Pydantic rules.",
)
async def validate_trip(trip_req: TripRequest) -> TripValidateResponse:
    """Validates submitted trip requirements."""
    logger.debug("Validating trip request for destination '%s'", trip_req.destination)
    try:
        PromptGuardService.validate_request_content([trip_req.destination, *(trip_req.interests or [])])
    except ValueError as sec_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(sec_err))

    return TripValidateResponse(
        valid=True,
        message=f"Trip to {trip_req.destination} for {trip_req.days} days is valid.",
        validated_request=trip_req,
    )


@router.post(
    "/plan",
    response_model=TripPlanningResult,
    status_code=status.HTTP_200_OK,
    summary="Plan Complete Trip with Multi-Agent Swarm",
    description="Coordinates Research, Budget, Itinerary, and Booking agents with LangGraph checkpointing.",
)
async def plan_trip(
    trip_req: TripRequest,
    require_approval: bool = Query(
        default=True, description="Whether human approval is required before final confirmation"
    ),
    caller_id: Optional[str] = Depends(verify_api_key),
) -> TripPlanningResult:
    """Initiates multi-agent travel planning graph."""
    logger.info("Received trip planning request for '%s' (Caller: %s)", trip_req.destination, caller_id)
    try:
        PromptGuardService.validate_request_content([trip_req.destination, *(trip_req.interests or [])])
    except ValueError as sec_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(sec_err))

    try:
        raw_result = await approval_service.start_trip_planning(
            trip_request=trip_req,
            require_approval=require_approval,
        )
        trip_id = raw_result["trip_id"]

        # Persist trip and requirements to the relational database
        try:
            async with async_session_maker() as session:
                await TripRepository.create_trip(session, trip_req, custom_trip_id=trip_id)
                if not raw_result.get("is_paused") and raw_result.get("response"):
                    await TripRepository.save_trip_response(session, trip_id, raw_result["response"])
                await session.commit()
        except Exception as db_err:
            logger.warning("Could not persist trip %s to relational database: %s", trip_id, db_err)

        if raw_result.get("is_paused"):
            return TripPlanningResult(
                trip_id=trip_id,
                status="PENDING_APPROVAL",
                is_paused=True,
                message="Trip plan created. Paused awaiting human authorization.",
                data={
                    "paused_at": raw_result.get("paused_at"),
                    "destination": raw_result.get("destination"),
                    "itinerary_days": len(raw_result.get("itinerary", [])),
                    "accommodation_options": len(raw_result.get("accommodation_options", [])),
                },
            )
        else:
            final_resp: Optional[TripResponse] = raw_result.get("response")
            return TripPlanningResult(
                trip_id=trip_id,
                status="COMPLETED",
                is_paused=False,
                message="Trip plan generated and finalized successfully.",
                response=final_resp,
            )
    except Exception as exc:
        logger.error("Trip planning failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Multi-agent trip planning failed: {exc}",
        )


@router.get(
    "/{trip_id}",
    response_model=TripPlanningResult,
    status_code=status.HTTP_200_OK,
    summary="Get Trip Details by ID",
    description="Fetches current execution state or finalized response from checkpointer or database.",
)
async def get_trip(trip_id: str) -> TripPlanningResult:
    """Retrieves current trip status and results."""
    try:
        status_info = approval_service.get_approval_status(trip_id)
        return TripPlanningResult(
            trip_id=trip_id,
            status=status_info.status,
            is_paused=status_info.is_paused,
            message=f"Current stage: {status_info.current_stage or 'unknown'}",
            data={
                "destination": status_info.destination,
                "days": status_info.days,
                "total_budget": status_info.total_budget,
                "estimated_cost": status_info.estimated_cost,
                "itinerary_count": len(status_info.itinerary_preview),
            },
        )
    except KeyError:
        # Fall back to persistent database record
        try:
            async with async_session_maker() as session:
                db_trip = await TripRepository.get_trip(session, trip_id)
                if db_trip:
                    req_days = db_trip.trip_request.days if db_trip.trip_request else None
                    req_b = db_trip.trip_request.budget if db_trip.trip_request else None
                    est_c = db_trip.budget.total_estimated_cost if db_trip.budget else None
                    itin_len = len(db_trip.itinerary.days) if (db_trip.itinerary and db_trip.itinerary.days) else 0

                    return TripPlanningResult(
                        trip_id=trip_id,
                        status=db_trip.status,
                        is_paused=(db_trip.status == "PENDING_APPROVAL"),
                        message=f"Retrieved from persistent database: {db_trip.title}",
                        data={
                            "destination": db_trip.destination,
                            "days": req_days,
                            "total_budget": req_b,
                            "estimated_cost": est_c,
                            "itinerary_count": itin_len,
                        },
                    )
        except Exception as db_exc:
            logger.warning("Database fallback check failed for %s: %s", trip_id, db_exc)

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No execution state or database record found for trip ID '{trip_id}'",
        )
    except Exception as exc:
        logger.error("Error retrieving trip %s: %s", trip_id, exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving trip: {exc}",
        )
