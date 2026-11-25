"""
TripMate AI - API Dependencies
Provides authentication, authorization, and security dependencies for REST endpoints.
"""

from typing import Optional
from fastapi import Header, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(
    api_key: Optional[str] = Security(api_key_header),
) -> Optional[str]:
    """
    Validates API key from request headers.
    When REQUIRE_API_KEY is enabled, rejects requests missing or with invalid API keys.
    """
    if not settings.REQUIRE_API_KEY:
        return api_key or "anonymous"

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed: Missing required 'X-API-Key' header.",
        )

    if settings.MASTER_API_KEY and api_key != settings.MASTER_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed: Invalid API Key.",
        )

    return api_key

