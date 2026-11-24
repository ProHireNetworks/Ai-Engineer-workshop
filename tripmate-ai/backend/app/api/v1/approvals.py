"""
TripMate AI - Human-in-the-Loop Approval Endpoints
Endpoints for reviewing, approving, rejecting, or requesting modifications for pending trips.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.api.deps import verify_api_key
from app.database.repository import TripRepository
from app.database.session import async_session_maker
from app.schemas.approval import ApprovalDecisionRequest, ApprovalStatusResponse
from app.schemas.trip import TripResponse
from app.services.approval_service import approval_service
from app.services.prompt_guard import PromptGuardService
from app.utils.logger import get_logger

router = APIRouter(prefix="/approvals", tags=["Human-in-the-Loop Approvals"])
logger = get_logger(__name__)


class QuickApprovalComment(BaseModel):
    comment: Optional[str] = Field(default=None, description="Optional reviewer notes")
    reviewer_id: Optional[str] = Field(default="reviewer", description="Reviewer identifier")


@router.get(
    "/{trip_id}",
    response_model=ApprovalStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Trip Approval Status",
    description="Inspects the checkpointed graph state to see if execution is paused for review.",
)
async def get_approval_status(trip_id: str) -> ApprovalStatusResponse:
    """Retrieve current human-in-the-loop approval status for a trip."""
    try:
        return approval_service.get_approval_status(trip_id)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        logger.error("Failed getting approval status for %s: %s", trip_id, exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error retrieving approval status: {exc}",
        )


@router.post(
    "/{trip_id}/decision",
    response_model=TripResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit Human Approval Decision",
    description="Resumes the paused LangGraph workflow with an explicit review decision.",
)
async def submit_approval_decision(
    trip_id: str,
    payload: ApprovalDecisionRequest,
    caller_id: Optional[str] = Depends(verify_api_key),
) -> TripResponse:
    """Submits review decision and resumes agent workflow."""
    if payload.comment:
        try:
            PromptGuardService.validate_request_content([payload.comment])
        except ValueError as sec_err:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(sec_err))

    try:
        final_resp = await approval_service.submit_approval_decision(
            trip_id=trip_id,
            decision=payload.decision,
            comment=payload.comment,
            reviewer_id=payload.reviewer_id,
        )

        # Persist approval decision and updated trip state into relational database
        try:
            async with async_session_maker() as session:
                await TripRepository.record_approval(
                    db=session,
                    trip_id=trip_id,
                    decision=payload.decision,
                    comment=payload.comment,
                    reviewer_id=payload.reviewer_id,
                )
                await TripRepository.save_trip_response(session, trip_id, final_resp)
                await session.commit()
        except Exception as db_err:
            logger.warning("Could not persist approval record for %s: %s", trip_id, db_err)

        return final_resp
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        logger.error("Failed submitting decision for %s: %s", trip_id, exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Resumption error: {exc}",
        )


@router.post(
    "/{trip_id}/approve",
    response_model=TripResponse,
    status_code=status.HTTP_200_OK,
    summary="Quick Approve Trip",
    description="Convenience shortcut to approve itinerary and finalize workflow.",
)
async def quick_approve(
    trip_id: str,
    body: Optional[QuickApprovalComment] = None,
) -> TripResponse:
    """Approves itinerary and triggers finalization."""
    notes = body.comment if body else "Approved via quick approve"
    reviewer = body.reviewer_id if body else "reviewer"
    return await submit_approval_decision(
        trip_id=trip_id,
        payload=ApprovalDecisionRequest(decision="APPROVED", comment=notes, reviewer_id=reviewer),
    )


@router.post(
    "/{trip_id}/reject",
    response_model=TripResponse,
    status_code=status.HTTP_200_OK,
    summary="Quick Reject Trip",
    description="Convenience shortcut to reject itinerary and record rejection in final state.",
)
async def quick_reject(
    trip_id: str,
    body: Optional[QuickApprovalComment] = None,
) -> TripResponse:
    """Rejects itinerary and terminates workflow with REJECTED status."""
    notes = body.comment if body else "Rejected via quick reject"
    reviewer = body.reviewer_id if body else "reviewer"
    return await submit_approval_decision(
        trip_id=trip_id,
        payload=ApprovalDecisionRequest(decision="REJECTED", comment=notes, reviewer_id=reviewer),
    )

