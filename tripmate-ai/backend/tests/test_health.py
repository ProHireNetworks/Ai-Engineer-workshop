"""
TripMate AI - Health & Core System Tests
Verifies FastAPI initialization, health check endpoint, request ID middleware,
and Pydantic response validation.
"""

import pytest
from starlette.testclient import TestClient
from httpx import AsyncClient

from app.schemas.health import HealthResponse


def test_root_endpoint(client: TestClient):
    """Verify root landing endpoint returns basic service metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "service" in data
    assert data["service"] == "TripMate AI"
    assert "version" in data
    assert "documentation" in data
    assert data["health"] == "/api/v1/health"


def test_health_endpoint_sync(client: TestClient):
    """Verify synchronous health check endpoint returns 200 and matches HealthResponse schema."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()

    # Validate against Pydantic schema
    health_model = HealthResponse.model_validate(data)
    assert health_model.status in ["healthy", "degraded"]
    assert health_model.app_name == "TripMate AI"
    assert "api" in health_model.checks
    assert health_model.checks["api"].status == "healthy"
    assert "llm_provider" in health_model.checks
    assert "database" in health_model.checks


@pytest.mark.asyncio
async def test_health_endpoint_async(async_client: AsyncClient):
    """Verify asynchronous health check endpoint."""
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["environment"] == "testing"


def test_request_id_generated(client: TestClient):
    """Verify middleware automatically generates an X-Request-ID header."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert "x-request-id" in response.headers
    assert len(response.headers["x-request-id"]) > 0


def test_request_id_preserved(client: TestClient):
    """Verify middleware propagates an existing incoming X-Request-ID header."""
    custom_id = "test-custom-trace-uuid-12345"
    response = client.get("/api/v1/health", headers={"X-Request-ID": custom_id})
    assert response.status_code == 200
    assert response.headers.get("x-request-id") == custom_id


def test_process_time_header(client: TestClient):
    """Verify middleware returns request execution latency in X-Process-Time."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert "x-process-time" in response.headers
    assert response.headers["x-process-time"].endswith("s")


def test_not_found_endpoint(client: TestClient):
    """Verify requesting an undefined route returns 404 with standard header."""
    response = client.get("/api/v1/nonexistent-route")
    assert response.status_code == 404
    assert "x-request-id" in response.headers

