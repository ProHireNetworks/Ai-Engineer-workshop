"""
TripMate AI - Human-in-the-Loop & Approval Tests
Tests LangGraph interrupt before approval, state checkpointing, inspection, and resumption.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.schemas.approval import ApprovalDecisionRequest
from app.schemas.trip import TripRequest
from app.services.approval_service import approval_service


@pytest.mark.asyncio
async def test_hitl_workflow_interrupt_and_inspection():
    """Verify that trip planning halts at interrupt and can be inspected."""
    req = TripRequest(
        destination="Kerala",
        days=4,
        budget=45000.0,
        currency="INR",
        interests=["nature", "backwaters"],
    )

    result = await approval_service.start_trip_planning(
        trip_request=req,
        require_approval=True,
    )

    trip_id = result["trip_id"]
    assert result["is_paused"] is True
    assert result["status"] == "PENDING_APPROVAL"
    assert result["paused_at"] == "approval"
    assert len(result["itinerary"]) == 4

    # Inspect status
    status_resp = approval_service.get_approval_status(trip_id)
    assert status_resp.trip_id == trip_id
    assert status_resp.is_paused is True
    assert status_resp.status == "PENDING"
    assert status_resp.destination == "Kerala"
    assert len(status_resp.itinerary_preview) == 4


@pytest.mark.asyncio
async def test_hitl_workflow_resumption_approved():
    """Verify that approving an interrupted workflow resumes and finalizes with SUCCESS."""
    req = TripRequest(
        destination="Goa",
        days=3,
        budget=25000.0,
        currency="INR",
        interests=["beaches"],
    )

    start_result = await approval_service.start_trip_planning(
        trip_request=req,
        require_approval=True,
    )
    trip_id = start_result["trip_id"]
    assert start_result["is_paused"] is True

    # Resume with approval
    final_resp = await approval_service.submit_approval_decision(
        trip_id=trip_id,
        decision="APPROVED",
        comment="Looks great! Approved by client.",
        reviewer_id="lead_agent",
    )

    assert final_resp is not None
    assert final_resp.trip_id == trip_id
    assert final_resp.status == "SUCCESS"
    assert final_resp.approval_status == "APPROVED"

    # Status inspection after completion
    post_status = approval_service.get_approval_status(trip_id)
    assert post_status.is_paused is False
    assert post_status.status == "APPROVED"


@pytest.mark.asyncio
async def test_hitl_workflow_resumption_rejected():
    """Verify that rejecting an interrupted workflow resumes and finalizes with REJECTED."""
    req = TripRequest(
        destination="Manali",
        days=3,
        budget=20000.0,
        currency="INR",
    )

    start_result = await approval_service.start_trip_planning(
        trip_request=req,
        require_approval=True,
    )
    trip_id = start_result["trip_id"]

    # Resume with rejection
    final_resp = await approval_service.submit_approval_decision(
        trip_id=trip_id,
        decision="REJECTED",
        comment="Budget too tight for the season.",
        reviewer_id="human_supervisor",
    )

    assert final_resp is not None
    assert final_resp.status == "REJECTED"
    assert final_resp.approval_status == "REJECTED"


@pytest.mark.asyncio
async def test_api_trip_planning_and_approval_flow():
    """Test full HTTP API lifecycle for trip planning, status check, and quick approval."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Initiate plan with require_approval=True
        plan_resp = await client.post(
            "/api/v1/trips/plan?require_approval=true",
            json={
                "destination": "Jaipur",
                "days": 3,
                "budget": 30000.0,
                "travelers": 2,
                "currency": "INR",
                "interests": ["heritage"],
            },
        )
        assert plan_resp.status_code == 200
        plan_data = plan_resp.json()
        assert plan_data["status"] == "PENDING_APPROVAL"
        assert plan_data["is_paused"] is True
        trip_id = plan_data["trip_id"]

        # 2. Check approval status endpoint
        status_resp = await client.get(f"/api/v1/approvals/{trip_id}")
        assert status_resp.status_code == 200
        status_data = status_resp.json()
        assert status_data["is_paused"] is True
        assert status_data["status"] == "PENDING"
        assert status_data["destination"] == "Jaipur"

        # 3. Check trips details endpoint
        trip_detail_resp = await client.get(f"/api/v1/trips/{trip_id}")
        assert trip_detail_resp.status_code == 200
        trip_detail_data = trip_detail_resp.json()
        assert trip_detail_data["is_paused"] is True

        # 4. Approve via quick approve endpoint
        approve_resp = await client.post(
            f"/api/v1/approvals/{trip_id}/approve",
            json={"comment": "Approved by testing suite", "reviewer_id": "test_operator"},
        )
        assert approve_resp.status_code == 200
        approved_data = approve_resp.json()
        assert approved_data["status"] == "SUCCESS"
        assert approved_data["approval_status"] == "APPROVED"
        assert approved_data["trip_id"] == trip_id

