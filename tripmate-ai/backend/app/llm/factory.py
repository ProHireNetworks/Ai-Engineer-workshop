"""
TripMate AI - LLM Provider Factory
Instantiates and configures the appropriate LLM provider dynamically
based on environment configuration or explicit injection.
"""

from typing import Optional
from app.config import settings
from app.llm.base import BaseLLMProvider
from app.llm.exceptions import LLMProviderError
from app.llm.mock_provider import MockLLMProvider
from app.llm.ollama_provider import OllamaProvider
from app.llm.openai_provider import OpenAIProvider
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Cached provider instance
_provider_instance: Optional[BaseLLMProvider] = None


def get_llm_provider(
    provider_type: Optional[str] = None, force_new: bool = False
) -> BaseLLMProvider:
    """
    Retrieves or instantiates an LLM provider adapter.

    Args:
        provider_type: Optional override ('openai', 'ollama', 'mock').
                       Defaults to settings.LLM_PROVIDER.
        force_new: If True, bypasses singleton cache and creates a fresh instance.

    Returns:
        Instance conforming to BaseLLMProvider.
    """
    global _provider_instance

    target_type = (provider_type or settings.LLM_PROVIDER).lower().strip()

    if not force_new and _provider_instance is not None:
        if _provider_instance.get_provider_name() == target_type:
            return _provider_instance

    logger.info("Initializing LLM provider: '%s'", target_type)

    if target_type == "openai":
        provider = OpenAIProvider(
            api_key=settings.OPENAI_API_KEY,
            model_name=settings.OPENAI_MODEL,
            timeout=settings.LLM_TIMEOUT,
            max_retries=settings.LLM_MAX_RETRIES,
        )
    elif target_type == "ollama":
        provider = OllamaProvider(
            base_url=settings.OLLAMA_BASE_URL,
            model_name=settings.OLLAMA_MODEL,
            timeout=settings.LLM_TIMEOUT,
        )
    elif target_type == "mock":
        provider = MockLLMProvider(model_name=settings.OPENAI_MODEL)
    else:
        raise LLMProviderError(
            f"Unsupported LLM provider '{target_type}'. Valid options are 'openai', 'ollama', 'mock'."
        )

    if not force_new:
        _provider_instance = provider

    return provider


def reset_llm_provider() -> None:
    """Clears the cached provider instance (useful for test fixtures)."""
    global _provider_instance
    _provider_instance = None

