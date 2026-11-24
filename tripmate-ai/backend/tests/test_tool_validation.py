"""
TripMate AI - Tool Validation Test Suite
Tests for Pydantic input validation, boundary constraints, and error messages.
"""

import pytest
from app.schemas.tool import ToolCall
from app.tools.cost_calculator import CalculateTripBudgetTool
from app.tools.exceptions import ToolValidationError
from app.tools.executor import ToolExecutor
from app.tools.registry import ToolRegistry
from app.tools.schemas import (
    AttractionsSearchArgs,
    BudgetCalculatorArgs,
    DestinationSearchArgs,
    TravelTimeArgs,
    WeatherArgs,
)
from app.tools.travel_search import SearchDestinationTool


def test_destination_search_args_validation():
    """Verify DestinationSearchArgs validation rules."""
    # Valid
    args = DestinationSearchArgs(destination="Jaipur", interests=["forts"])
    assert args.destination == "Jaipur"

    # Too short
    with pytest.raises(Exception):
        DestinationSearchArgs(destination="A")


def test_budget_calculator_args_validation():
    """Verify BudgetCalculatorArgs non-negative validation."""
    # Valid
    args = BudgetCalculatorArgs(
        transportation=100.0,
        accommodation=200.0,
        food=50.0,
        activities=30.0,
        miscellaneous=20.0,
        currency="usd",
    )
    assert args.currency == "USD"

    # Negative value rejected
    with pytest.raises(Exception):
        BudgetCalculatorArgs(
            transportation=-50.0,
            accommodation=200.0,
            food=50.0,
            activities=30.0,
            miscellaneous=20.0,
        )


@pytest.mark.asyncio
async def test_tool_execute_validation_failure():
    """Verify Tool.execute() raises ToolValidationError on bad arguments."""
    tool = SearchDestinationTool()
    with pytest.raises(ToolValidationError) as exc_info:
        await tool.execute(destination="")  # Empty destination
    assert "Invalid arguments" in str(exc_info.value)


@pytest.mark.asyncio
async def test_executor_catches_validation_error():
    """Verify ToolExecutor handles validation failure and returns status='error'."""
    registry = ToolRegistry()
    registry.register(CalculateTripBudgetTool())
    executor = ToolExecutor(registry=registry)

    # Missing required arguments
    bad_call = ToolCall(
        id="bad_call_1",
        name="calculate_trip_budget",
        arguments={"transportation": 100},  # Missing accommodation, food, etc.
    )
    result = await executor.execute_call(bad_call)

    assert result.status == "error"
    assert "ToolValidationError" in (result.error or "")

