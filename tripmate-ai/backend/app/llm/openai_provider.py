"""
TripMate AI - OpenAI LLM Provider
Async implementation for OpenAI GPT models supporting standard completions,
native structured JSON parsing, token accounting, and explicit error translation.
"""

import json
import time
from typing import Any, Dict, List, Optional, Type, TypeVar
from pydantic import BaseModel
import openai
from openai import AsyncOpenAI

from app.config import settings
from app.llm.base import BaseLLMProvider
from app.llm.exceptions import (
    LLMAuthenticationError,
    LLMConnectionError,
    LLMProviderError,
    LLMRateLimitError,
    LLMStructuredOutputError,
    LLMTimeoutError,
)
from app.llm.usage import LLMHealthStatus, LLMMessage, LLMResponse, TokenUsage
from app.schemas.tool import ToolCall
from app.utils.logger import get_logger

logger = get_logger(__name__)
T = TypeVar("T", bound=BaseModel)


class OpenAIProvider(BaseLLMProvider):
    """Production provider integrating OpenAI API via AsyncOpenAI."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
        client: Optional[AsyncOpenAI] = None,
    ) -> None:
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model_name = model_name or settings.OPENAI_MODEL
        self.timeout = timeout or settings.LLM_TIMEOUT
        self.max_retries = max_retries or settings.LLM_MAX_RETRIES
        self.provider_name = "openai"

        # Client can be injected (e.g. in tests) or created with provided settings
        if client is not None:
            self.client = client
        else:
            self.client = AsyncOpenAI(
                api_key=self.api_key or "missing-key",
                timeout=float(self.timeout),
                max_retries=self.max_retries,
            )

    def get_provider_name(self) -> str:
        return self.provider_name

    def get_model_name(self) -> str:
        return self.model_name

    def _validate_credentials(self) -> None:
        if not self.api_key or self.api_key.strip() in ("", "missing-key", "your-openai-api-key"):
            raise LLMAuthenticationError(
                message="OpenAI API key is missing or not configured. Set OPENAI_API_KEY in .env.",
                provider=self.provider_name,
            )

    async def generate(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Executes async completion call against OpenAI."""
        self._validate_credentials()
        formatted = [{"role": m.role, "content": m.content} for m in messages]

        start_time = time.perf_counter()
        try:
            params: dict[str, Any] = {
                "model": self.model_name,
                "messages": formatted,
                "temperature": temperature,
            }
            if max_tokens is not None:
                params["max_tokens"] = max_tokens
            params.update(kwargs)

            completion = await self.client.chat.completions.create(**params)
            latency_ms = (time.perf_counter() - start_time) * 1000.0

            choice = completion.choices[0]
            content = choice.message.content or ""

            prompt_tokens = completion.usage.prompt_tokens if completion.usage else 0
            completion_tokens = completion.usage.completion_tokens if completion.usage else 0
            total_tokens = completion.usage.total_tokens if completion.usage else 0

            usage = TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                estimated_cost_usd=TokenUsage.calculate_cost(
                    self.model_name, prompt_tokens, completion_tokens
                ),
            )

            return LLMResponse(
                content=content,
                role=choice.message.role or "assistant",
                model=completion.model,
                provider=self.provider_name,
                usage=usage,
                finish_reason=choice.finish_reason,
                latency_ms=round(latency_ms, 2),
                is_mock=False,
            )
        except openai.AuthenticationError as exc:
            logger.error("OpenAI authentication error: %s", exc)
            raise LLMAuthenticationError(str(exc), provider=self.provider_name) from exc
        except openai.RateLimitError as exc:
            logger.warning("OpenAI rate limit reached: %s", exc)
            raise LLMRateLimitError(str(exc), provider=self.provider_name) from exc
        except openai.APITimeoutError as exc:
            logger.error("OpenAI request timed out: %s", exc)
            raise LLMTimeoutError(str(exc), provider=self.provider_name) from exc
        except openai.APIConnectionError as exc:
            logger.error("OpenAI connection failed: %s", exc)
            raise LLMConnectionError(str(exc), provider=self.provider_name) from exc
        except openai.APIError as exc:
            logger.error("OpenAI provider error: %s", exc)
            raise LLMProviderError(str(exc), provider=self.provider_name) from exc

    async def generate_structured(
        self,
        messages: List[LLMMessage],
        response_model: Type[T],
        temperature: float = 0.2,
        **kwargs: Any,
    ) -> T:
        """Executes structured completion via OpenAI parse endpoint."""
        self._validate_credentials()
        formatted = [{"role": m.role, "content": m.content} for m in messages]

        try:
            params: dict[str, Any] = {
                "model": self.model_name,
                "messages": formatted,
                "response_format": response_model,
                "temperature": temperature,
            }
            params.update(kwargs)

            completion = await self.client.beta.chat.completions.parse(**params)
            parsed = completion.choices[0].message.parsed
            if parsed is None:
                raise LLMStructuredOutputError(
                    "Model failed to produce a structured JSON output satisfying schema.",
                    provider=self.provider_name,
                )
            return parsed
        except openai.AuthenticationError as exc:
            raise LLMAuthenticationError(str(exc), provider=self.provider_name) from exc
        except openai.RateLimitError as exc:
            raise LLMRateLimitError(str(exc), provider=self.provider_name) from exc
        except openai.APITimeoutError as exc:
            raise LLMTimeoutError(str(exc), provider=self.provider_name) from exc
        except (openai.APIError, Exception) as exc:
            if isinstance(exc, (LLMAuthenticationError, LLMRateLimitError, LLMTimeoutError)):
                raise
            logger.error("OpenAI structured output failed: %s", exc)
            raise LLMStructuredOutputError(
                f"Failed to generate structured output: {str(exc)}",
                provider=self.provider_name,
            ) from exc

    async def generate_with_tools(
        self,
        messages: List[LLMMessage],
        tools: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Executes tool-calling completion against OpenAI."""
        self._validate_credentials()

        formatted: list[dict[str, Any]] = []
        for m in messages:
            msg_dict: dict[str, Any] = {"role": m.role, "content": m.content}
            if m.name:
                msg_dict["name"] = m.name
            if m.tool_call_id:
                msg_dict["tool_call_id"] = m.tool_call_id
            if m.tool_calls:
                msg_dict["tool_calls"] = m.tool_calls
            formatted.append(msg_dict)

        start_time = time.perf_counter()
        try:
            params: dict[str, Any] = {
                "model": self.model_name,
                "messages": formatted,
                "tools": tools,
                "tool_choice": "auto",
                "temperature": temperature,
            }
            if max_tokens is not None:
                params["max_tokens"] = max_tokens
            params.update(kwargs)

            completion = await self.client.chat.completions.create(**params)
            latency_ms = (time.perf_counter() - start_time) * 1000.0

            choice = completion.choices[0]
            content = choice.message.content or ""

            prompt_tokens = completion.usage.prompt_tokens if completion.usage else 0
            completion_tokens = completion.usage.completion_tokens if completion.usage else 0
            total_tokens = completion.usage.total_tokens if completion.usage else 0

            usage = TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                estimated_cost_usd=TokenUsage.calculate_cost(
                    self.model_name, prompt_tokens, completion_tokens
                ),
            )

            extracted_tool_calls: List[ToolCall] = []
            if choice.message.tool_calls:
                for tc in choice.message.tool_calls:
                    try:
                        args = (
                            json.loads(tc.function.arguments)
                            if isinstance(tc.function.arguments, str)
                            else tc.function.arguments
                        )
                    except Exception:
                        args = {"raw": tc.function.arguments}
                    extracted_tool_calls.append(
                        ToolCall(
                            id=tc.id,
                            name=tc.function.name,
                            arguments=args,
                        )
                    )

            return LLMResponse(
                content=content,
                role=choice.message.role or "assistant",
                model=completion.model,
                provider=self.provider_name,
                usage=usage,
                finish_reason=choice.finish_reason,
                latency_ms=round(latency_ms, 2),
                is_mock=False,
                tool_calls=extracted_tool_calls,
            )
        except openai.AuthenticationError as exc:
            raise LLMAuthenticationError(str(exc), provider=self.provider_name) from exc
        except openai.RateLimitError as exc:
            raise LLMRateLimitError(str(exc), provider=self.provider_name) from exc
        except openai.APITimeoutError as exc:
            raise LLMTimeoutError(str(exc), provider=self.provider_name) from exc
        except openai.APIConnectionError as exc:
            raise LLMConnectionError(str(exc), provider=self.provider_name) from exc
        except openai.APIError as exc:
            raise LLMProviderError(str(exc), provider=self.provider_name) from exc

    async def health_check(self) -> LLMHealthStatus:
        """Verifies API key validity and reachability by listing available models."""
        if not self.api_key or self.api_key.strip() in ("", "missing-key"):
            return LLMHealthStatus(
                is_available=False,
                provider=self.provider_name,
                model=self.model_name,
                is_mock=False,
                error="OpenAI API key not configured.",
            )

        start_time = time.perf_counter()
        try:
            # Query models endpoint with short timeout to test connectivity
            await self.client.models.list(timeout=5.0)
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            return LLMHealthStatus(
                is_available=True,
                provider=self.provider_name,
                model=self.model_name,
                is_mock=False,
                latency_ms=round(latency_ms, 2),
                details={"status": "online"},
            )
        except Exception as exc:
            logger.warning("OpenAI health check failed: %s", exc)
            return LLMHealthStatus(
                is_available=False,
                provider=self.provider_name,
                model=self.model_name,
                is_mock=False,
                error=str(exc),
            )

