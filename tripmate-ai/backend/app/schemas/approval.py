"""
TripMate AI - Approval Schemas
Pydantic models for Human-in-the-Loop trip plan review and authorization.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

from app.schemas.trip import DailyItinerary, TripResponse


class ApprovalDecisionRequest(BaseModel):
    """Payload submitted by user or reviewer to approve, reject, or modify a pending itinerary."""

    decision: Literal["APPROVED", "REJECTED", "MODIFICATION_REQUESTED"] = Field(
        ..., description="Review outcome decision"
    )
    comment: Optional[str] = Field(
        default=None, description="Human reviewer justification or requested modifications"
    )
    reviewer_id: Optional[str] = Field(
        default="human_operator", description="Identifier of the approving entity"
    )


class ApprovalStatusResponse(BaseModel):
    """Inspection response detailing the pending approval state of a trip."""

    trip_id: str
    status: Literal["PENDING", "APPROVED", "REJECTED", "NOT_REQUIRED", "MODIFICATION_REQUESTED"]
    is_paused: bool = Field(
        ..., description="Whether execution is paused awaiting human intervention"
    )
    next_action: Optional[str] = None
    destination: Optional[str] = None
    days: Optional[int] = None
    total_budget: Optional[float] = None
    estimated_cost: Optional[float] = None
    comment: Optional[str] = None
    current_stage: Optional[str] = None
    itinerary_preview: List[DailyItinerary] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

