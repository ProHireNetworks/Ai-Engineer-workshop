"""
TripMate AI - Function Calling & Tool Loop Test Suite
Tests for OpenAI tool calling (mocked), Ollama tool calling (mocked),
Mock provider tool calling, ToolCallingService multi-turn reasoning, and max rounds limit.
"""

from unittest.mock import AsyncMock, MagicMock
import httpx
import pytest
from starlette.testclient import TestClient

from app.llm.mock_provider import MockLLMProvider
from app.llm.ollama_provider import OllamaProvider
from app.llm.openai_provider import OpenAIProvider
from app.llm.usage import LLMMessage, LLMResponse, TokenUsage
from app.schemas.tool import ToolCall, ToolCallResult
from app.services.tool_calling_service import ToolCallingService
from app.tools.registry import ToolRegistry, populate_default_tools, tool_registry


@pytest.mark.asyncio
async def test_mock_provider_tool_calling():
    """Verify MockLLMProvider simulates tool calls then finalizes after tool results."""
    provider = MockLLMProvider()
    tools = tool_registry.to_openai_tools()

    # Turn 1: User prompt -> Mock provider requests tools
    msg1 = [LLMMessage(role="user", content="Plan a 3-day trip to Jaipur with budget 15000")]
    res1 = await provider.generate_with_tools(msg1, tools=tools)

    assert len(res1.tool_calls) > 0
    assert any(tc.name == "search_destination" for tc in res1.tool_calls)

    # Turn 2: Providing tool results -> Mock provider emits final answer
    msg2 = list(msg1)
    msg2.append(LLMMessage(role="assistant", content="Calling tools...", tool_calls=[]))
    msg2.append(
        LLMMessage(
            role="tool",
            content='{"destination": "Jaipur", "overview": "Historic city"}',
            tool_call_id=res1.tool_calls[0].id,
            name="search_destination",
        )
    )
    res2 = await provider.generate_with_tools(msg2, tools=tools)
    assert len(res2.tool_calls) == 0
    assert "[MOCK DATA" in res2.content


@pytest.mark.asyncio
async def test_openai_tool_calling_mocked():
    """Verify OpenAIProvider parses returned tool calls into ToolCall objects."""
    mock_tc = MagicMock()
    mock_tc.id = "call_abc123"
    mock_tc.function.name = "get_weather"
    mock_tc.function.arguments = '{"destination": "Goa"}'

    mock_choice = MagicMock()
    mock_choice.message.content = None
    mock_choice.message.role = "assistant"
    mock_choice.message.tool_calls = [mock_tc]
    mock_choice.finish_reason = "tool_calls"

    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]
    mock_completion.model = "gpt-4o"
    mock_completion.usage.prompt_tokens = 50
    mock_completion.usage.completion_tokens = 20
    mock_completion.usage.total_tokens = 70

    mock_client = AsyncMock()
    mock_client.chat.completions.create.return_value = mock_completion

    provider = OpenAIProvider(api_key="sk-test-key", client=mock_client)
    messages = [LLMMessage(role="user", content="What's the weather in Goa?")]
    tools = [{"type": "function", "function": {"name": "get_weather"}}]

    response = await provider.generate_with_tools(messages, tools=tools)
    assert len(response.tool_calls) == 1
    assert response.tool_calls[0].id == "call_abc123"
    assert response.tool_calls[0].name == "get_weather"
    assert response.tool_calls[0].arguments == {"destination": "Goa"}


@pytest.mark.asyncio
async def test_ollama_tool_calling_mocked():
    """Verify OllamaProvider parses tool calls from /api/chat payload."""
    fake_response = {
        "model": "llama3.1",
        "message": {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "function": {
                        "name": "search_attractions",
                        "arguments": {"destination": "Jaipur", "limit": 3},
                    }
                }
            ],
        },
        "prompt_eval_count": 30,
        "eval_count": 15,
        "done": True,
    }

    mock_transport = httpx.MockTransport(
        lambda req: httpx.Response(200, json=fake_response)
    )
    custom_client = httpx.AsyncClient(transport=mock_transport, base_url="http://localhost:11434")

    provider = OllamaProvider(model_name="llama3.1", http_client=custom_client)
    messages = [LLMMessage(role="user", content="Attractions in Jaipur")]
    tools = [{"type": "function", "function": {"name": "search_attractions"}}]

    response = await provider.generate_with_tools(messages, tools=tools)
    assert len(response.tool_calls) == 1
    assert response.tool_calls[0].name == "search_attractions"
    assert response.tool_calls[0].arguments == {"destination": "Jaipur", "limit": 3}


@pytest.mark.asyncio
async def test_tool_calling_service_loop():
    """Verify ToolCallingService executes end-to-end multi-turn tool loops."""
    provider = MockLLMProvider()
    service = ToolCallingService(provider=provider, registry=tool_registry, max_rounds=3)

    content, tool_results, usage = await service.run_chat(
        user_prompt="Plan a trip to Goa with weather and budget",
        enable_tools=True,
    )

    assert len(content) > 0
    assert len(tool_results) > 0
    assert all(isinstance(tr, ToolCallResult) for tr in tool_results)
    assert usage.total_tokens > 0


@pytest.mark.asyncio
async def test_tool_calling_service_max_rounds():
    """Verify ToolCallingService halts and synthesizes after reaching max rounds limit."""
    class LoopingMockProvider(MockLLMProvider):
        async def generate_with_tools(self, messages, tools, **kwargs):
            # Always requests another tool call to simulate a loop
            return LLMResponse(
                content="Need more data",
                role="assistant",
                model=self.model_name,
                provider=self.provider_name,
                usage=TokenUsage(total_tokens=10),
                tool_calls=[ToolCall(id="call_loop", name="get_weather", arguments={"destination": "LoopCity"})],
            )

    service = ToolCallingService(
        provider=LoopingMockProvider(), registry=tool_registry, max_rounds=2
    )
    content, tool_results, usage = await service.run_chat("Infinite test", enable_tools=True)

    # Should execute exactly 2 rounds of tool calls then break out cleanly
    assert len(tool_results) == 2
    assert len(content) > 0


# ==============================================================================
# API Endpoints Tests
# ==============================================================================


def test_api_list_tools(client: TestClient):
    """Verify GET /api/v1/tools returns list of registered tools."""
    response = client.get("/api/v1/tools")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 6
    names = [t["name"] for t in data]
    assert "search_destination" in names
    assert "calculate_trip_budget" in names


def test_api_execute_tool(client: TestClient):
    """Verify POST /api/v1/tools/execute executes a tool ad-hoc."""
    payload = {
        "tool_name": "calculate_trip_budget",
        "arguments": {
            "transportation": 1000.0,
            "accommodation": 2000.0,
            "food": 1000.0,
            "activities": 500.0,
            "miscellaneous": 500.0,
            "currency": "INR",
            "target_budget": 6000.0,
        },
    }
    response = client.post("/api/v1/tools/execute", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["result"]["total_estimated_cost"] == 5000.0
    assert data["result"]["is_within_budget"] is True


def test_api_chat_endpoint(client: TestClient):
    """Verify POST /api/v1/llm/chat performs tool-calling chat."""
    payload = {
        "message": "Plan a budget trip to Jaipur",
        "enable_tools": True,
    }
    response = client.post("/api/v1/llm/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "tool_calls_executed" in data
    assert "token_usage" in data
    assert len(data["tool_calls_executed"]) > 0

