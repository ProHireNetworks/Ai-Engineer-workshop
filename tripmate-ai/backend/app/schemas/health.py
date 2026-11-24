"""
TripMate AI - Health Schema
Pydantic schemas for system health and readiness verification.
"""

from datetime import datetime, timezone
from typing import Dict, Literal
from pydantic import BaseModel, Field


class ServiceCheck(BaseModel):
    status: Literal["healthy", "degraded", "unhealthy", "mocked"] = Field(
        ..., description="Status of the individual subsystem"
    )
    details: str = Field(..., description="Descriptive status or diagnostic message")


class HealthResponse(BaseModel):
    status: Literal["healthy", "degraded", "unhealthy"] = Field(
        ..., description="Overall health status of the application"
    )
    app_name: str = Field(..., description="Application name")
    version: str = Field(..., description="Application semantic version")
    environment: str = Field(..., description="Active runtime environment")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of the health check",
    )
    checks: Dict[str, ServiceCheck] = Field(
        default_factory=dict, description="Detailed status breakdown per component"
    )

