from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_home_endpoint():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["status"] == "Running"


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_api_rejects_missing_fields():
    response = client.post(
        "/api/plan-trip",
        json={}
    )

    assert response.status_code == 422


def test_api_rejects_invalid_dates():
    response = client.post(
        "/api/plan-trip",
        json={
            "origin": "Hyderabad",
            "destination": "Goa",
            "start_date": "2026-12-15",
            "end_date": "2026-12-10",
            "travelers": 2,
            "budget": 15000
        }
    )

    assert response.status_code == 422


def test_openapi_documentation():
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "/api/plan-trip" in response.json()["paths"]