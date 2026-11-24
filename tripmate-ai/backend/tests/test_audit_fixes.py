"""
TripMate AI - Production Audit Fixes Test Suite
Verifies:
1. Handling of MODIFICATION_REQUESTED in Human-in-the-Loop workflows.
2. Prevention of duplicate approval submissions (idempotency/re-review rejection).
3. Relational database persistence across simulated process restarts.
4. REST API status codes and responses for approval and persistence flows.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.database.repository import TripRepository
from app.database.session import async_session_maker
from app.main import app
from app.schemas.approval import ApprovalDecisionRequest
from app.schemas.trip import TripRequest, TripResponse
from app.services.approval_service import approval_service


@pytest.mark.asyncio
async def test_hitl_modification_requested_service():
    """Verify that submitting MODIFICATION_REQUESTED updates status and returns a valid TripResponse."""
    req = TripRequest(
        destination="Udaipur",
        days=3,
        budget=30000.0,
        currency="INR",
        interests=["lakes", "palaces"],
    )

    start_result = await approval_service.start_trip_planning(
        trip_request=req,
        require_approval=True,
    )
    trip_id = start_result["trip_id"]
    assert start_result["is_paused"] is True

    # Submit MODIFICATION_REQUESTED decision
    resp = await approval_service.submit_approval_decision(
        trip_id=trip_id,
        decision="MODIFICATION_REQUESTED",
        comment="Please adjust accommodation to a heritage hotel with lake view.",
        reviewer_id="lead_traveler",
    )

    assert isinstance(resp, TripResponse)
    assert resp.trip_id == trip_id
    assert resp.status == "MODIFICATION_REQUESTED"
    assert resp.approval_status == "MODIFICATION_REQUESTED"


@pytest.mark.asyncio
async def test_hitl_duplicate_submission_blocked():
    """Verify that submitting an approval decision on an already finalized trip raises ValueError."""
    req = TripRequest(
        destination="Goa",
        days=2,
        budget=15000.0,
        currency="INR",
    )

    start_result = await approval_service.start_trip_planning(
        trip_request=req,
        require_approval=True,
    )
    trip_id = start_result["trip_id"]

    # First decision: APPROVED
    await approval_service.submit_approval_decision(
        trip_id=trip_id,
        decision="APPROVED",
        comment="Approved initial itinerary",
        reviewer_id="reviewer_1",
    )

    # Second decision should be rejected
    with pytest.raises(ValueError, match="Duplicate review submissions are not permitted"):
        await approval_service.submit_approval_decision(
            trip_id=trip_id,
            decision="APPROVED",
            comment="Duplicate approval attempt",
            reviewer_id="reviewer_2",
        )


@pytest.mark.asyncio
async def test_api_modification_requested_endpoint():
    """Verify that POST /api/v1/approvals/{trip_id}/decision handles MODIFICATION_REQUESTED with 200 OK."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        plan_resp = await client.post(
            "/api/v1/trips/plan?require_approval=true",
            json={
                "destination": "Shimla",
                "days": 3,
                "budget": 20000.0,
                "currency": "INR",
            },
        )
        assert plan_resp.status_code == 200
        trip_id = plan_resp.json()["trip_id"]

        decision_resp = await client.post(
            f"/api/v1/approvals/{trip_id}/decision",
            json={
                "decision": "MODIFICATION_REQUESTED",
                "comment": "Prefer mountain view homestay instead of hotel",
                "reviewer_id": "client_app",
            },
        )
        assert decision_resp.status_code == 200
        data = decision_resp.json()
        assert data["status"] == "MODIFICATION_REQUESTED"
        assert data["approval_status"] == "MODIFICATION_REQUESTED"
        assert data["trip_id"] == trip_id


@pytest.mark.asyncio
async def test_api_duplicate_approval_blocked():
    """Verify that approving an already approved trip via REST API returns 400 Bad Request."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        plan_resp = await client.post(
            "/api/v1/trips/plan?require_approval=true",
            json={
                "destination": "Mysore",
                "days": 2,
                "budget": 12000.0,
                "currency": "INR",
            },
        )
        assert plan_resp.status_code == 200
        trip_id = plan_resp.json()["trip_id"]

        # First approval
        first_resp = await client.post(
            f"/api/v1/approvals/{trip_id}/approve",
            json={"comment": "First approval", "reviewer_id": "operator_1"},
        )
        assert first_resp.status_code == 200
        assert first_resp.json()["status"] == "SUCCESS"

        # Duplicate approval attempt
        second_resp = await client.post(
            f"/api/v1/approvals/{trip_id}/approve",
            json={"comment": "Second approval attempt", "reviewer_id": "operator_2"},
        )
        assert second_resp.status_code == 400
        assert "Duplicate review submissions are not permitted" in second_resp.json()["detail"]


@pytest.mark.asyncio
async def test_trip_database_persistence_and_restart():
    """
    Verify that trips are persisted to the relational database and can be retrieved
    even when in-memory execution state is cleared (simulating process restart).
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Create a trip via API
        plan_resp = await client.post(
            "/api/v1/trips/plan?require_approval=true",
            json={
                "destination": "Ooty",
                "days": 4,
                "budget": 28000.0,
                "currency": "INR",
                "interests": ["botanical gardens", "tea estates"],
            },
        )
        assert plan_resp.status_code == 200
        trip_id = plan_resp.json()["trip_id"]

        # 2. Verify direct database persistence in relational repository
        async with async_session_maker() as session:
            db_trip = await TripRepository.get_trip(session, trip_id)
            assert db_trip is not None
            assert db_trip.destination == "Ooty"
            assert db_trip.trip_request is not None
            assert db_trip.trip_request.days == 4
            assert db_trip.trip_request.budget == 28000.0

        # 3. Simulate process restart by clearing checkpointer thread memory
        # In MemorySaver, storage holds the checkpoints
        if hasattr(approval_service.graph.checkpointer, "storage"):
            approval_service.graph.checkpointer.storage.clear()

        # 4. Fetch trip via GET endpoint - should successfully fall back to database
        get_resp = await client.get(f"/api/v1/trips/{trip_id}")
        assert get_resp.status_code == 200
        trip_data = get_resp.json()
        assert trip_data["trip_id"] == trip_id
        assert trip_data["data"]["destination"] == "Ooty"
        assert trip_data["data"]["days"] == 4
        assert trip_data["data"]["total_budget"] == 28000.0
        assert "persistent database" in trip_data["message"]

