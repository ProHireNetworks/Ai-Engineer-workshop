"""
TripMate AI - Comprehensive Live API Smoke Test
Verifies all FastAPI REST endpoints across Phases 1-10.
"""

import asyncio
import os
from pathlib import Path
import sys

# Ensure backend directory is in python sys.path
backend_path = str(Path(__file__).resolve().parent.parent / "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from httpx import ASGITransport, AsyncClient

from app.main import app


async def run_smoke_test():
    print("=== TRIPMATE AI LIVE API SMOKE TEST ===")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Health check
        r = await client.get("/api/v1/health")
        assert r.status_code == 200, f"Health check failed: {r.text}"
        print(f"[OK] GET /api/v1/health -> {r.json()['status']}")

        # 2. LLM status
        r = await client.get("/api/v1/llm/status")
        assert r.status_code == 200, f"LLM status failed: {r.text}"
        print(f"[OK] GET /api/v1/llm/status -> Provider: {r.json()['provider']}")

        # 3. Tool discovery
        r = await client.get("/api/v1/tools")
        assert r.status_code == 200, f"Tools listing failed: {r.text}"
        tools_list = r.json()
        print(f"[OK] GET /api/v1/tools -> {len(tools_list)} registered tools")

        # 4. Trip request validation
        r = await client.post(
            "/api/v1/trips/validate",
            json={"destination": "Jaipur", "days": 3, "budget": 30000, "travelers": 2},
        )
        assert r.status_code == 200, f"Validation failed: {r.text}"
        print(f"[OK] POST /api/v1/trips/validate -> Valid: {r.json()['valid']}")

        # 5. RAG knowledge search
        r = await client.post(
            "/api/v1/knowledge/ingest",
            json={
                "content": "Jaipur boasts majestic Rajput architecture including Amer Fort.",
                "destination": "Jaipur",
                "source_file": "jaipur_brief.md",
            },
        )
        assert r.status_code == 201
        r = await client.post(
            "/api/v1/knowledge/search",
            json={"query": "Amer Fort architecture", "destination": "Jaipur", "top_k": 2},
        )
        assert r.status_code == 200
        print(f"[OK] POST /api/v1/knowledge/search -> Found {r.json()['results_count']} chunks")

        # 6. Full Trip Planning with Human-in-the-Loop Interrupt
        r = await client.post(
            "/api/v1/trips/plan?require_approval=true",
            json={
                "destination": "Kerala",
                "days": 3,
                "budget": 35000,
                "travelers": 2,
                "currency": "INR",
                "interests": ["backwaters", "wellness"],
            },
        )
        assert r.status_code == 200
        plan_data = r.json()
        trip_id = plan_data["trip_id"]
        assert plan_data["status"] == "PENDING_APPROVAL"
        print(f"[OK] POST /api/v1/trips/plan -> Trip ID: {trip_id} (Status: {plan_data['status']})")

        # 7. Inspect approval state
        r = await client.get(f"/api/v1/approvals/{trip_id}")
        assert r.status_code == 200
        appr_data = r.json()
        assert appr_data["is_paused"] is True
        print(f"[OK] GET /api/v1/approvals/{trip_id} -> Paused: {appr_data['is_paused']}")

        # 8. Approve trip
        r = await client.post(
            f"/api/v1/approvals/{trip_id}/approve",
            json={"comment": "Approved by client via test harness", "reviewer_id": "test_operator"},
        )
        assert r.status_code == 200
        approved_trip = r.json()
        assert approved_trip["status"] == "SUCCESS"
        assert approved_trip["approval_status"] == "APPROVED"
        print(f"[OK] POST /api/v1/approvals/{trip_id}/approve -> Final Status: {approved_trip['status']}")

    print("\nALL API SMOKE TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    asyncio.run(run_smoke_test())
