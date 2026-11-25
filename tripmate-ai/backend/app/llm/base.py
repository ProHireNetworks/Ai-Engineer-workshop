"""
TripMate AI - LLM Base Provider Interface
Abstract base class specifying required methods for all provider adapters.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypeVar
from pydantic import BaseModel

from app.llm.usage import LLMHealthStatus, LLMMessage, LLMResponse

T = TypeVar("T", bound=BaseModel)

from typing import Any, Dict, List, Optional
class BaseLLMProvider(ABC):
    """Abstract interface defining required methods for all LLM implementations."""

    @abstractmethod
    def get_provider_name(self) -> str:
        """Returns the canonical name of this provider (e.g. 'openai', 'ollama', 'mock')."""
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Returns the active model name being invoked."""
        pass

    @abstractmethod
    async def generate(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Executes a standard conversational or completion request asynchronously.

        Args:
            messages: Ordered sequence of conversation messages.
            temperature: Sampling temperature between 0.0 and 2.0.
            max_tokens: Maximum tokens allowed for generation.
            kwargs: Provider-specific auxiliary arguments.

        Returns:
            Standardized LLMResponse.
        """
        pass

    @abstractmethod
    async def generate_structured(
        self,
        messages: List[LLMMessage],
        response_model: Type[T],
        temperature: float = 0.2,
        **kwargs: Any,
    ) -> T:
        """
        Executes a structured completion enforcing Pydantic validation.

        Args:
            messages: Ordered sequence of conversation messages.
            response_model: Expected Pydantic model class for the output.
            temperature: Sampling temperature (typically low for structured accuracy).
            kwargs: Provider-specific auxiliary arguments.

        Returns:
            Validated instance of response_model.
        """
        pass

    @abstractmethod
    async def generate_with_tools(
        self,
        messages: List[LLMMessage],
        tools: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Executes a completion request providing tool definitions for function calling.

        Args:
            messages: Ordered sequence of conversation messages.
            tools: List of tool specifications conforming to provider formats.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens allowed.
            kwargs: Provider-specific auxiliary arguments.

        Returns:
            Standardized LLMResponse containing generated content and/or requested tool_calls.
        """
        pass

    @abstractmethod
    async def health_check(self) -> LLMHealthStatus:
        """
        Verifies connectivity and model availability.

        Returns:
            LLMHealthStatus containing availability flag, latency, and diagnostics.
        """
        pass

