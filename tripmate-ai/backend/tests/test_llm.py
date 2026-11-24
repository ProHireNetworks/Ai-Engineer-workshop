"""
TripMate AI - LLM Layer Test Suite
Tests for provider abstraction, OpenAI adapter (mocked), Ollama adapter (mocked),
Mock provider, factory, usage tracking, error translation, and API status endpoint.
"""

from typing import List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import openai
import pytest
from pydantic import BaseModel
from starlette.testclient import TestClient

from app.llm.base import BaseLLMProvider
from app.llm.exceptions import (
    LLMAuthenticationError,
    LLMConnectionError,
    LLMError,
    LLMProviderError,
    LLMRateLimitError,
    LLMStructuredOutputError,
    LLMTimeoutError,
)
from app.llm.factory import get_llm_provider, reset_llm_provider
from app.llm.mock_provider import MockLLMProvider
from app.llm.ollama_provider import OllamaProvider
from app.llm.openai_provider import OpenAIProvider
from app.llm.usage import LLMHealthStatus, LLMMessage, LLMResponse, TokenUsage
from app.prompts.system_prompts import (
    BOOKING_ASSISTANT_SYSTEM_PROMPT,
    BUDGET_AGENT_SYSTEM_PROMPT,
    ITINERARY_AGENT_SYSTEM_PROMPT,
    RESEARCH_AGENT_SYSTEM_PROMPT,
)
from app.prompts.templates import (
    format_booking_prompt,
    format_budget_prompt,
    format_itinerary_prompt,
    format_research_prompt,
)
from app.schemas.llm import LLMStatusResponse


class SampleTravelPlan(BaseModel):
    destination: str
    days: int
    estimated_budget: float
    activities: List[str]
    notes: Optional[str] = None


# ==============================================================================
# 1. Token Usage Tests
# ==============================================================================


def test_token_usage_math():
    """Verify TokenUsage accumulation and pricing calculations."""
    u1 = TokenUsage(prompt_tokens=100, completion_tokens=50, total_tokens=150)
    u2 = TokenUsage(prompt_tokens=200, completion_tokens=100, total_tokens=300)
    combined = u1.add(u2)

    assert combined.prompt_tokens == 300
    assert combined.completion_tokens == 150
    assert combined.total_tokens == 450

    cost = TokenUsage.calculate_cost("gpt-4o", prompt_tokens=1000, completion_tokens=500)
    assert cost > 0.0


# ==============================================================================
# 2. Mock Provider Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_mock_provider_generate():
    """Verify MockLLMProvider produces deterministic mock responses."""
    provider = MockLLMProvider(model_name="mock-model")
    assert provider.get_provider_name() == "mock"
    assert provider.get_model_name() == "mock-model"

    messages = [
        LLMMessage(role="system", content="System instruction"),
        LLMMessage(role="user", content="Plan a trip to Tokyo"),
    ]
    response = await provider.generate(messages)

    assert isinstance(response, LLMResponse)
    assert response.is_mock is True
    assert "[MOCK DATA" in response.content
    assert response.usage.total_tokens > 0


@pytest.mark.asyncio
async def test_mock_provider_generate_structured():
    """Verify MockLLMProvider dynamically synthesizes valid Pydantic instances."""
    provider = MockLLMProvider()
    messages = [LLMMessage(role="user", content="Generate a sample travel plan")]

    plan = await provider.generate_structured(messages, response_model=SampleTravelPlan)
    assert isinstance(plan, SampleTravelPlan)
    assert len(plan.destination) > 0
    assert plan.days > 0
    assert plan.estimated_budget > 0
    assert isinstance(plan.activities, list)


@pytest.mark.asyncio
async def test_mock_provider_health_check():
    """Verify MockLLMProvider reports available status."""
    provider = MockLLMProvider()
    health = await provider.health_check()
    assert health.is_available is True
    assert health.is_mock is True
    assert health.provider == "mock"


# ==============================================================================
# 3. Provider Factory Tests
# ==============================================================================


def test_factory_provider_selection():
    """Verify factory returns appropriate provider classes."""
    reset_llm_provider()
    mock_prov = get_llm_provider("mock", force_new=True)
    assert isinstance(mock_prov, MockLLMProvider)

    openai_prov = get_llm_provider("openai", force_new=True)
    assert isinstance(openai_prov, OpenAIProvider)

    ollama_prov = get_llm_provider("ollama", force_new=True)
    assert isinstance(ollama_prov, OllamaProvider)


def test_factory_unsupported_provider():
    """Verify factory raises error for unrecognized provider names."""
    with pytest.raises(LLMProviderError) as exc_info:
        get_llm_provider("unsupported-provider-xyz", force_new=True)
    assert "Unsupported LLM provider" in str(exc_info.value)


# ==============================================================================
# 4. OpenAI Provider Tests (Mocked API)
# ==============================================================================


@pytest.mark.asyncio
async def test_openai_missing_key_error():
    """Verify OpenAIProvider raises LLMAuthenticationError when API key is missing."""
    provider = OpenAIProvider(api_key="")
    with pytest.raises(LLMAuthenticationError) as exc_info:
        await provider.generate([LLMMessage(role="user", content="Hello")])
    assert "API key is missing" in str(exc_info.value)


@pytest.mark.asyncio
async def test_openai_generate_mocked():
    """Verify OpenAIProvider correctly handles mock API completion responses."""
    mock_choice = MagicMock()
    mock_choice.message.content = "Visit the Taj Mahal and Agra Fort"
    mock_choice.message.role = "assistant"
    mock_choice.finish_reason = "stop"

    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]
    mock_completion.model = "gpt-4o"
    mock_completion.usage.prompt_tokens = 50
    mock_completion.usage.completion_tokens = 25
    mock_completion.usage.total_tokens = 75

    mock_client = AsyncMock()
    mock_client.chat.completions.create.return_value = mock_completion

    provider = OpenAIProvider(api_key="sk-mock-valid-key", client=mock_client)
    response = await provider.generate([LLMMessage(role="user", content="Attractions in Agra")])

    assert response.content == "Visit the Taj Mahal and Agra Fort"
    assert response.provider == "openai"
    assert response.usage.total_tokens == 75
    assert response.is_mock is False


@pytest.mark.asyncio
async def test_openai_generate_structured_mocked():
    """Verify OpenAIProvider parse endpoint with structured output."""
    sample_plan = SampleTravelPlan(
        destination="Kyoto", days=4, estimated_budget=60000.0, activities=["Kinkaku-ji", "Fushimi Inari"]
    )

    mock_parsed_choice = MagicMock()
    mock_parsed_choice.message.parsed = sample_plan

    mock_completion = MagicMock()
    mock_completion.choices = [mock_parsed_choice]

    mock_client = AsyncMock()
    mock_client.beta.chat.completions.parse.return_value = mock_completion

    provider = OpenAIProvider(api_key="sk-mock-key", client=mock_client)
    res = await provider.generate_structured(
        [LLMMessage(role="user", content="Plan trip to Kyoto")],
        response_model=SampleTravelPlan,
    )
    assert res.destination == "Kyoto"
    assert len(res.activities) == 2


@pytest.mark.asyncio
async def test_openai_rate_limit_error():
    """Verify OpenAI RateLimitError is translated to LLMRateLimitError."""
    mock_client = AsyncMock()
    fake_response = httpx.Response(429, request=httpx.Request("POST", "http://test"))
    mock_client.chat.completions.create.side_effect = openai.RateLimitError(
        "Rate limit exceeded", response=fake_response, body=None
    )

    provider = OpenAIProvider(api_key="sk-mock-key", client=mock_client)
    with pytest.raises(LLMRateLimitError):
        await provider.generate([LLMMessage(role="user", content="Hi")])


@pytest.mark.asyncio
async def test_openai_timeout_error():
    """Verify OpenAI APITimeoutError is translated to LLMTimeoutError."""
    mock_client = AsyncMock()
    mock_client.chat.completions.create.side_effect = openai.APITimeoutError(
        request=httpx.Request("POST", "http://test")
    )

    provider = OpenAIProvider(api_key="sk-mock-key", client=mock_client)
    with pytest.raises(LLMTimeoutError):
        await provider.generate([LLMMessage(role="user", content="Hi")])


@pytest.mark.asyncio
async def test_openai_health_check():
    """Verify OpenAI health check returns availability status based on client response."""
    mock_client = AsyncMock()
    mock_client.models.list.return_value = MagicMock()

    provider = OpenAIProvider(api_key="sk-mock-key", client=mock_client)
    health = await provider.health_check()
    assert health.is_available is True
    assert health.provider == "openai"


# ==============================================================================
# 5. Ollama Provider Tests (Mocked HTTP)
# ==============================================================================


@pytest.mark.asyncio
async def test_ollama_generate_mocked():
    """Verify OllamaProvider handles /api/chat payload properly."""
    fake_payload = {
        "model": "llama3.1",
        "message": {"role": "assistant", "content": "Explore Old Town and Castle"},
        "prompt_eval_count": 40,
        "eval_count": 20,
        "done": True,
    }

    mock_transport = httpx.MockTransport(
        lambda req: httpx.Response(200, json=fake_payload)
    )
    custom_client = httpx.AsyncClient(transport=mock_transport, base_url="http://localhost:11434")

    provider = OllamaProvider(model_name="llama3.1", http_client=custom_client)
    response = await provider.generate([LLMMessage(role="user", content="Prague highlights")])

    assert response.content == "Explore Old Town and Castle"
    assert response.provider == "ollama"
    assert response.usage.total_tokens == 60


@pytest.mark.asyncio
async def test_ollama_generate_structured_mocked():
    """Verify OllamaProvider structured response validation."""
    valid_json_body = {
        "destination": "Goa",
        "days": 3,
        "estimated_budget": 12000.0,
        "activities": ["Calangute Beach", "Fort Aguada"],
    }
    fake_response_data = {
        "model": "llama3.1",
        "message": {"role": "assistant", "content": str(valid_json_body).replace("'", '"')},
        "done": True,
    }

    mock_transport = httpx.MockTransport(
        lambda req: httpx.Response(200, json=fake_response_data)
    )
    custom_client = httpx.AsyncClient(transport=mock_transport, base_url="http://localhost:11434")

    provider = OllamaProvider(model_name="llama3.1", http_client=custom_client)
    plan = await provider.generate_structured(
        [LLMMessage(role="user", content="Plan Goa trip")],
        response_model=SampleTravelPlan,
    )
    assert plan.destination == "Goa"
    assert plan.days == 3


@pytest.mark.asyncio
async def test_ollama_connection_error():
    """Verify OllamaProvider handles connection failure properly."""
    def raise_connect(req):
        raise httpx.ConnectError("Connection refused", request=req)

    mock_transport = httpx.MockTransport(raise_connect)
    custom_client = httpx.AsyncClient(transport=mock_transport, base_url="http://localhost:11434")

    provider = OllamaProvider(http_client=custom_client)
    with pytest.raises(LLMConnectionError):
        await provider.generate([LLMMessage(role="user", content="Hello")])


@pytest.mark.asyncio
async def test_ollama_health_check_mocked():
    """Verify OllamaProvider health check returns online when version check succeeds."""
    mock_transport = httpx.MockTransport(
        lambda req: httpx.Response(200, json={"version": "0.3.14"})
    )
    custom_client = httpx.AsyncClient(transport=mock_transport, base_url="http://localhost:11434")

    provider = OllamaProvider(http_client=custom_client)
    health = await provider.health_check()
    assert health.is_available is True
    assert health.provider == "ollama"
    assert health.details.get("version") == "0.3.14"


# ==============================================================================
# 6. Prompts & Templates Tests
# ==============================================================================


def test_system_prompts_and_templates():
    """Verify system prompts are defined and template formatting functions."""
    assert len(RESEARCH_AGENT_SYSTEM_PROMPT) > 50
    assert len(BUDGET_AGENT_SYSTEM_PROMPT) > 50
    assert len(ITINERARY_AGENT_SYSTEM_PROMPT) > 50
    assert len(BOOKING_ASSISTANT_SYSTEM_PROMPT) > 50

    p_research = format_research_prompt("Rome", 5, ["history", "food"], 2)
    assert "Rome" in p_research
    assert "5 days" in p_research
    assert "history, food" in p_research

    p_budget = format_budget_prompt("Rome", 5, 2, 80000, "INR")
    assert "80,000.00 INR" in p_budget

    p_itinerary = format_itinerary_prompt("Rome", 5, 2, ["history"], "Great sights", "Realistic")
    assert "Great sights" in p_itinerary

    p_booking = format_booking_prompt("Rome", 5, 2, 40000, "INR")
    assert "40,000.00 INR" in p_booking


# ==============================================================================
# 7. LLM Status API Endpoint Tests
# ==============================================================================


def test_llm_status_endpoint(client: TestClient):
    """Verify GET /api/v1/llm/status returns 200 with valid LLMStatusResponse schema."""
    response = client.get("/api/v1/llm/status")
    assert response.status_code == 200
    data = response.json()

    status_model = LLMStatusResponse.model_validate(data)
    assert status_model.provider == "mock"
    assert status_model.is_mock is True
    assert status_model.is_available is True
    assert status_model.error is None

