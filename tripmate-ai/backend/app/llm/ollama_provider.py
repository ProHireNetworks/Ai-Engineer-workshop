"""
TripMate AI - Ollama Local LLM Provider
Async HTTP implementation integrating local Ollama instances (e.g. Llama 3, Mistral)
without requiring cloud API keys.
"""

import json
import time
import uuid
from typing import Any, Dict, List, Optional, Type, TypeVar
import httpx
from pydantic import BaseModel

from app.config import settings
from app.llm.base import BaseLLMProvider
from app.llm.exceptions import (
    LLMConnectionError,
    LLMProviderError,
    LLMStructuredOutputError,
    LLMTimeoutError,
)
from app.llm.usage import LLMHealthStatus, LLMMessage, LLMResponse, TokenUsage
from app.schemas.tool import ToolCall
from app.utils.logger import get_logger

logger = get_logger(__name__)
T = TypeVar("T", bound=BaseModel)


class OllamaProvider(BaseLLMProvider):
    """Local LLM provider interfacing with an Ollama daemon via REST APIs."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: Optional[int] = None,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model_name = model_name or settings.OLLAMA_MODEL
        self.timeout = float(timeout or settings.LLM_TIMEOUT)
        self.provider_name = "ollama"
        self._custom_client = http_client

    def get_provider_name(self) -> str:
        return self.provider_name

    def get_model_name(self) -> str:
        return self.model_name

    def _get_client(self) -> httpx.AsyncClient:
        if self._custom_client is not None:
            return self._custom_client
        return httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout)

    async def generate(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Invokes Ollama /api/chat with streaming disabled."""
        formatted_messages = [{"role": m.role, "content": m.content} for m in messages]

        payload: dict[str, Any] = {
            "model": self.model_name,
            "messages": formatted_messages,
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }
        if max_tokens is not None:
            payload["options"]["num_predict"] = max_tokens
        payload.update(kwargs)

        start_time = time.perf_counter()
        async with self._get_client() as client:
            try:
                response = await client.post("/api/chat", json=payload)
                latency_ms = (time.perf_counter() - start_time) * 1000.0

                if response.status_code == 404:
                    raise LLMProviderError(
                        f"Model '{self.model_name}' was not found in local Ollama instance. "
                        f"Run 'ollama pull {self.model_name}' to download it.",
                        provider=self.provider_name,
                    )
                response.raise_for_status()

                data = response.json()
                msg = data.get("message", {})
                content = msg.get("content", "")

                prompt_tokens = data.get("prompt_eval_count", 0)
                completion_tokens = data.get("eval_count", 0)
                usage = TokenUsage(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=prompt_tokens + completion_tokens,
                    estimated_cost_usd=0.0,  # Local compute has zero API expense
                )

                return LLMResponse(
                    content=content,
                    role=msg.get("role", "assistant"),
                    model=data.get("model", self.model_name),
                    provider=self.provider_name,
                    usage=usage,
                    finish_reason="stop" if data.get("done") else None,
                    latency_ms=round(latency_ms, 2),
                    is_mock=False,
                )
            except httpx.ConnectError as exc:
                logger.error("Failed to connect to Ollama at %s: %s", self.base_url, exc)
                raise LLMConnectionError(
                    f"Ollama server is not reachable at {self.base_url}. Ensure Ollama is installed and running.",
                    provider=self.provider_name,
                ) from exc
            except httpx.TimeoutException as exc:
                logger.error("Ollama request timed out after %ss: %s", self.timeout, exc)
                raise LLMTimeoutError(
                    f"Ollama inference timed out after {self.timeout} seconds.",
                    provider=self.provider_name,
                ) from exc
            except httpx.HTTPStatusError as exc:
                raise LLMProviderError(
                    f"Ollama returned HTTP error {exc.response.status_code}: {exc.response.text}",
                    provider=self.provider_name,
                ) from exc

    async def generate_structured(
        self,
        messages: List[LLMMessage],
        response_model: Type[T],
        temperature: float = 0.2,
        **kwargs: Any,
    ) -> T:
        """Invokes Ollama with JSON schema format constraint and parses Pydantic model."""
        formatted_messages = [{"role": m.role, "content": m.content} for m in messages]

        # Instruct model to respond with strictly valid JSON
        schema_json = json.dumps(response_model.model_json_schema())
        system_instruction = (
            f"You are a structured data extractor. You must respond ONLY with a valid JSON object matching "
            f"this schema: {schema_json}. Do not output any markdown formatting or commentary."
        )

        formatted_messages.insert(0, {"role": "system", "content": system_instruction})

        payload: dict[str, Any] = {
            "model": self.model_name,
            "messages": formatted_messages,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": temperature,
            },
        }
        payload.update(kwargs)

        async with self._get_client() as client:
            try:
                response = await client.post("/api/chat", json=payload)
                response.raise_for_status()
                data = response.json()
                raw_content = data.get("message", {}).get("content", "").strip()

                try:
                    return response_model.model_validate_json(raw_content)
                except Exception as parse_exc:
                    logger.error("Ollama JSON output validation failed: %s | Raw: %s", parse_exc, raw_content)
                    raise LLMStructuredOutputError(
                        f"Failed to validate model output against {response_model.__name__}: {parse_exc}",
                        provider=self.provider_name,
                    ) from parse_exc
            except httpx.ConnectError as exc:
                raise LLMConnectionError(
                    f"Ollama server is not reachable at {self.base_url}.",
                    provider=self.provider_name,
                ) from exc
            except httpx.TimeoutException as exc:
                raise LLMTimeoutError(
                    f"Ollama structured inference timed out after {self.timeout} seconds.",
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
        """Invokes Ollama with tool definitions when supported."""
        formatted_messages: list[dict[str, Any]] = []
        for m in messages:
            msg_dict: dict[str, Any] = {"role": m.role, "content": m.content}
            if m.tool_calls:
                msg_dict["tool_calls"] = m.tool_calls
            formatted_messages.append(msg_dict)

        payload: dict[str, Any] = {
            "model": self.model_name,
            "messages": formatted_messages,
            "stream": False,
            "tools": tools,
            "options": {
                "temperature": temperature,
            },
        }
        if max_tokens is not None:
            payload["options"]["num_predict"] = max_tokens
        payload.update(kwargs)

        start_time = time.perf_counter()
        async with self._get_client() as client:
            try:
                response = await client.post("/api/chat", json=payload)
                latency_ms = (time.perf_counter() - start_time) * 1000.0
                response.raise_for_status()

                data = response.json()
                msg = data.get("message", {})
                content = msg.get("content", "")

                prompt_tokens = data.get("prompt_eval_count", 0)
                completion_tokens = data.get("eval_count", 0)
                usage = TokenUsage(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=prompt_tokens + completion_tokens,
                    estimated_cost_usd=0.0,
                )

                extracted_tool_calls: List[ToolCall] = []
                raw_tool_calls = msg.get("tool_calls", [])
                for tc in raw_tool_calls:
                    fn = tc.get("function", {})
                    fn_name = fn.get("name", "unknown")
                    fn_args = fn.get("arguments", {})
                    if isinstance(fn_args, str):
                        try:
                            fn_args = json.loads(fn_args)
                        except Exception:
                            fn_args = {"raw": fn_args}
                    extracted_tool_calls.append(
                        ToolCall(
                            id=f"call_{uuid.uuid4().hex[:8]}",
                            name=fn_name,
                            arguments=fn_args,
                        )
                    )

                return LLMResponse(
                    content=content,
                    role=msg.get("role", "assistant"),
                    model=data.get("model", self.model_name),
                    provider=self.provider_name,
                    usage=usage,
                    finish_reason="tool_calls" if extracted_tool_calls else "stop",
                    latency_ms=round(latency_ms, 2),
                    is_mock=False,
                    tool_calls=extracted_tool_calls,
                )
            except httpx.ConnectError as exc:
                raise LLMConnectionError(
                    f"Ollama server is not reachable at {self.base_url}.",
                    provider=self.provider_name,
                ) from exc
            except httpx.TimeoutException as exc:
                raise LLMTimeoutError(
                    f"Ollama inference timed out after {self.timeout} seconds.",
                    provider=self.provider_name,
                ) from exc
            except Exception as exc:
                raise LLMProviderError(str(exc), provider=self.provider_name) from exc

    async def health_check(self) -> LLMHealthStatus:
        """Pings Ollama /api/version to verify server availability and listed models."""
        start_time = time.perf_counter()
        async with self._get_client() as client:
            try:
                response = await client.get("/api/version")
                latency_ms = (time.perf_counter() - start_time) * 1000.0

                if response.status_code == 200:
                    ver_data = response.json()
                    return LLMHealthStatus(
                        is_available=True,
                        provider=self.provider_name,
                        model=self.model_name,
                        is_mock=False,
                        latency_ms=round(latency_ms, 2),
                        details={"version": ver_data.get("version"), "status": "online"},
                    )
                return LLMHealthStatus(
                    is_available=False,
                    provider=self.provider_name,
                    model=self.model_name,
                    is_mock=False,
                    error=f"Unexpected status: {response.status_code}",
                )
            except Exception as exc:
                return LLMHealthStatus(
                    is_available=False,
                    provider=self.provider_name,
                    model=self.model_name,
                    is_mock=False,
                    error=str(exc),
                )

