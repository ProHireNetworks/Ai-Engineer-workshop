"""
TripMate AI - LLM Status Schemas
Pydantic schemas for LLM provider status and diagnostics.
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class LLMStatusResponse(BaseModel):
    """Safe public status response for active LLM provider."""

    provider: str = Field(..., description="Active configured provider identifier")
    model: str = Field(..., description="Active model identity")
    is_available: bool = Field(..., description="Whether the provider is currently reachable")
    is_mock: bool = Field(..., description="True if using simulated offline mock provider")
    latency_ms: Optional[float] = Field(default=None, description="Health check latency in milliseconds")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Diagnostic details (no secrets)")
    error: Optional[str] = Field(default=None, description="Error message if provider is unavailable")

