"""
TripMate AI - LLM Exceptions
Structured exception hierarchy for LLM providers, network timeouts,
rate limits, authentication, and structured validation errors.
"""

from typing import Any, Dict, Optional


class LLMError(Exception):
    """Base exception for all LLM-related operations."""

    def __init__(
        self,
        message: str,
        provider: str = "unknown",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.provider = provider
        self.details = details or {}


class LLMProviderError(LLMError):
    """Raised when an underlying provider fails to process a request."""


class LLMAuthenticationError(LLMError):
    """Raised when provider credentials (e.g. OpenAI API Key) are invalid or missing."""


class LLMRateLimitError(LLMError):
    """Raised when provider rate limits or quotas are exceeded."""


class LLMTimeoutError(LLMError):
    """Raised when a request exceeds the configured provider timeout."""


class LLMStructuredOutputError(LLMError):
    """Raised when LLM output fails Pydantic validation or JSON schema decoding."""


class LLMConnectionError(LLMError):
    """Raised when a provider host (e.g. local Ollama server) is unreachable."""

