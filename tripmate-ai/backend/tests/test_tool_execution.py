"""
TripMate AI - Tool Execution Engine Test Suite
Tests for tool invocation, timeout handling, error containment, concurrency, and authorization.
"""

import asyncio
import pytest
from pydantic import BaseModel, Field

from app.schemas.tool import ToolCall, ToolCallResult
from app.tools.base import BaseTool
from app.tools.cost_calculator import CalculateTripBudgetTool
from app.tools.executor import ToolExecutor
from app.tools.registry import ToolRegistry, populate_default_tools
from app.tools.travel_search import SearchDestinationTool


class SlowArgs(BaseModel):
    duration: float = Field(default=0.5)


class SlowTool(BaseTool):
    name = "slow_tool"
    description = "Sleeps for testing timeouts"
    args_schema = SlowArgs
    timeout_seconds = 0.1  # Fast timeout

    async def _run(self, duration: float = 0.5):
        await asyncio.sleep(duration)
        return {"done": True}


class SecuredArgs(BaseModel):
    action: str = "book"


class SecuredTool(BaseTool):
    name = "secured_booking_tool"
    description = "Requires explicit authorization"
    args_schema = SecuredArgs
    requires_auth = True

    async def _run(self, action: str):
        return {"authorized": True, "action": action}


@pytest.mark.asyncio
async def test_search_destination_execution():
    """Verify search_destination tool executes and returns expected structure."""
    tool = SearchDestinationTool()
    res = await tool.execute(destination="Jaipur", interests=["culture"])
    assert res["destination"] == "Jaipur"
    assert "Jaipur" in res["overview"]
    assert res["is_mock"] is True


@pytest.mark.asyncio
async def test_deterministic_budget_calculator_execution():
    """Verify calculate_trip_budget executes pure deterministic arithmetic."""
    tool = CalculateTripBudgetTool()
    res = await tool.execute(
        transportation=2500.50,
        accommodation=5000.25,
        food=3000.00,
        activities=1500.00,
        miscellaneous=500.00,
        currency="INR",
        target_budget=15000.00,
        days=3,
        travelers=2,
    )

    expected_total = 2500.50 + 5000.25 + 3000.00 + 1500.00 + 500.00  # 12500.75
    assert res["total_estimated_cost"] == 12500.75
    assert res["is_within_budget"] is True
    assert res["savings_or_deficit"] == round(15000.00 - 12500.75, 2)
    assert res["calculation_method"] == "deterministic_python"


@pytest.mark.asyncio
async def test_executor_timeout_handling():
    """Verify executor gracefully traps timeouts into status='timeout'."""
    registry = ToolRegistry()
    registry.register(SlowTool())
    executor = ToolExecutor(registry=registry)

    call = ToolCall(id="call_slow_1", name="slow_tool", arguments={"duration": 1.0})
    result = await executor.execute_call(call)

    assert isinstance(result, ToolCallResult)
    assert result.status == "timeout"
    assert "ToolTimeoutError" in (result.error or "")


@pytest.mark.asyncio
async def test_executor_authorization_check():
    """Verify secured tools reject unauthorized execution."""
    registry = ToolRegistry()
    registry.register(SecuredTool())
    executor = ToolExecutor(registry=registry)

    call = ToolCall(id="call_sec_1", name="secured_booking_tool", arguments={"action": "book"})

    # Unauthorized attempt
    unauth_res = await executor.execute_call(call, is_authorized=False)
    assert unauth_res.status == "unauthorized"
    assert "ToolUnauthorizedError" in (unauth_res.error or "")

    # Authorized attempt
    auth_res = await executor.execute_call(call, is_authorized=True)
    assert auth_res.status == "success"
    assert auth_res.result["authorized"] is True


@pytest.mark.asyncio
async def test_execute_many_concurrency():
    """Verify execute_many runs multiple calls concurrently."""
    registry = ToolRegistry()
    populate_default_tools(registry)
    executor = ToolExecutor(registry=registry)

    calls = [
        ToolCall(id="c1", name="search_destination", arguments={"destination": "Goa"}),
        ToolCall(id="c2", name="get_weather", arguments={"destination": "Goa"}),
        ToolCall(
            id="c3",
            name="calculate_trip_budget",
            arguments={
                "transportation": 2000,
                "accommodation": 4000,
                "food": 2000,
                "activities": 1000,
                "miscellaneous": 500,
            },
        ),
    ]

    results = await executor.execute_many(calls)
    assert len(results) == 3
    assert all(r.status == "success" for r in results)
    assert {r.tool_name for r in results} == {
        "search_destination",
        "get_weather",
        "calculate_trip_budget",
    }

