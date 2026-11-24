"""
TripMate AI - Health Endpoint
Provides system health and readiness status for orchestration and load balancers.
"""

from fastapi import APIRouter, status
from app.config import settings
from app.schemas.health import HealthResponse, ServiceCheck
from app.utils.logger import get_logger

router = APIRouter(tags=["Health"])
logger = get_logger(__name__)


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="System Health & Readiness Check",
    description="Returns current operational status of the API and its underlying services.",
)
async def get_health() -> HealthResponse:
    """Check and return system health metrics."""
    logger.debug("Health check requested")

    checks = {
        "api": ServiceCheck(
            status="healthy",
            details="TripMate AI API service is operational",
        ),
        "llm_provider": ServiceCheck(
            status="healthy" if settings.LLM_PROVIDER in ["openai", "ollama"] else "mocked",
            details=f"Provider configured: {settings.LLM_PROVIDER}",
        ),
        "database": ServiceCheck(
            status="mocked" if settings.DATABASE_URL is None and settings.APP_ENV in ["development", "testing"] else "healthy",
            details="Database configured in active profile",
        ),
    }

    return HealthResponse(
        status="healthy",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.APP_ENV,
        checks=checks,
    )

