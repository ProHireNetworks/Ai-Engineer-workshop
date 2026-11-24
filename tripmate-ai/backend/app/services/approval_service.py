"""
TripMate AI - Approval and Checkpoint Service
Coordinates execution, human review interrupts, state inspection, and resumption.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Any, Dict, Optional
import uuid

if TYPE_CHECKING:
    from app.graph.state import TripState

from app.graph.workflow import trip_graph_with_approval
from app.schemas.approval import ApprovalStatusResponse
from app.schemas.trip import TripRequest, TripResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ApprovalService:
    """Manages LangGraph thread checkpointing, human-in-the-loop review, and workflow resumption."""

    def __init__(self) -> None:
        self.graph = trip_graph_with_approval

    async def start_trip_planning(
        self,
        trip_request: TripRequest,
        require_approval: bool = True,
        custom_trip_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Initiates the multi-agent travel planning workflow.
        If require_approval is True, the graph halts before final approval.
        """
        trip_id = custom_trip_id or f"trip_{uuid.uuid4().hex[:12]}"
        config = {"configurable": {"thread_id": trip_id}}

        initial_state: TripState = {
            "trip_id": trip_id,
            "user_request": trip_request,
            "approval_status": "PENDING" if require_approval else "NOT_REQUIRED",
            "revision_count": 0,
        }

        logger.info(
            "Starting trip planning workflow: %s (require_approval=%s)",
            trip_id,
            require_approval,
        )

        # Run until completion or interrupt
        await self.graph.ainvoke(initial_state, config=config)

        # Inspect post-run snapshot
        snapshot = self.graph.get_state(config)
        is_paused = bool(snapshot.next)

        if is_paused:
            logger.info("Workflow paused at interrupt node: %s for trip %s", snapshot.next, trip_id)
            values = snapshot.values
            return {
                "trip_id": trip_id,
                "status": "PENDING_APPROVAL",
                "is_paused": True,
                "paused_at": snapshot.next[0] if snapshot.next else "approval",
                "destination": trip_request.destination,
                "budget_analysis": values.get("budget_analysis"),
                "itinerary": values.get("itinerary") or [],
                "accommodation_options": values.get("accommodation_options") or [],
            }
        else:
            final_resp = snapshot.values.get("final_response")
            return {
                "trip_id": trip_id,
                "status": "COMPLETED",
                "is_paused": False,
                "response": final_resp,
            }

    def get_approval_status(self, trip_id: str) -> ApprovalStatusResponse:
        """Inspects the thread state and returns current approval/pause details."""
        config = {"configurable": {"thread_id": trip_id}}
        snapshot = self.graph.get_state(config)

        if not snapshot or not snapshot.values:
            raise KeyError(f"No execution state found for trip ID '{trip_id}'")

        values = snapshot.values
        req: Optional[TripRequest] = values.get("user_request")
        budget = values.get("budget_analysis")
        is_paused = bool(snapshot.next)
        next_action = snapshot.next[0] if snapshot.next else None

        return ApprovalStatusResponse(
            trip_id=trip_id,
            status=values.get("approval_status", "NOT_REQUIRED"),
            is_paused=is_paused,
            next_action=next_action,
            destination=req.destination if req else None,
            days=req.days if req else None,
            total_budget=req.budget if req else None,
            estimated_cost=budget.total_estimated_cost if budget else None,
            comment=values.get("approval_comment"),
            current_stage=values.get("current_stage"),
            itinerary_preview=values.get("itinerary") or [],
        )

    async def submit_approval_decision(
        self,
        trip_id: str,
        decision: str,
        comment: Optional[str] = None,
        reviewer_id: Optional[str] = None,
    ) -> TripResponse:
        """
        Resumes execution of an interrupted workflow by submitting an approval decision.
        """
        config = {"configurable": {"thread_id": trip_id}}
        snapshot = self.graph.get_state(config)

        if not snapshot or not snapshot.values:
            raise KeyError(f"No execution state found for trip ID '{trip_id}'")

        current_status = snapshot.values.get("approval_status")
        if current_status in ("APPROVED", "REJECTED"):
            raise ValueError(
                f"Trip '{trip_id}' has already been finalized with decision '{current_status}'. "
                f"Duplicate review submissions are not permitted."
            )

        logger.info(
            "Submitting decision '%s' for trip %s (Reviewer: %s)",
            decision,
            trip_id,
            reviewer_id,
        )

        if decision == "APPROVED":
            self.graph.update_state(
                config,
                {
                    "approval_status": "APPROVED",
                    "approval_comment": comment or f"Approved by {reviewer_id or 'operator'}",
                },
            )
        elif decision == "REJECTED":
            self.graph.update_state(
                config,
                {
                    "approval_status": "REJECTED",
                    "approval_comment": comment or f"Rejected by {reviewer_id or 'operator'}",
                },
            )
        elif decision == "MODIFICATION_REQUESTED":
            self.graph.update_state(
                config,
                {
                    "approval_status": "MODIFICATION_REQUESTED",
                    "approval_comment": comment or f"Modifications requested by {reviewer_id or 'reviewer'}",
                },
            )
        else:
            raise ValueError(f"Unsupported decision '{decision}'")

        # Resume graph execution with None input
        res = await self.graph.ainvoke(None, config=config)
        final_resp: Optional[TripResponse] = res.get("final_response")

        if not final_resp:
            # Fallback if state completed
            snapshot_after = self.graph.get_state(config)
            final_resp = snapshot_after.values.get("final_response")

        if not final_resp:
            raise RuntimeError(f"Workflow resumption did not produce a final TripResponse for '{trip_id}'")

        return final_resp


approval_service = ApprovalService()

