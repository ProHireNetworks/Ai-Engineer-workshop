"""
TripMate AI - Tool Registry Test Suite
Tests for tool registration, duplicate prevention, unknown tool handling, and schema exports.
"""

import pytest
from pydantic import BaseModel, Field

from app.schemas.tool import ToolDefinition
from app.tools.base import BaseTool
from app.tools.exceptions import ToolNotFoundError, ToolRegistrationError
from app.tools.registry import ToolRegistry, populate_default_tools


class DummyArgs(BaseModel):
    query: str = Field(..., min_length=1)


class DummyTool(BaseTool):
    name = "dummy_test_tool"
    description = "A dummy tool for unit testing."
    args_schema = DummyArgs

    async def _run(self, query: str):
        return {"echo": query}


def test_tool_registration_and_lookup():
    """Verify tool can be registered and retrieved by name."""
    registry = ToolRegistry()
    tool = DummyTool()
    registry.register(tool)

    assert registry.has_tool("dummy_test_tool") is True
    retrieved = registry.get("dummy_test_tool")
    assert retrieved.name == "dummy_test_tool"
    assert retrieved.description == "A dummy tool for unit testing."


def test_duplicate_registration_rejection():
    """Verify registering a duplicate tool name raises ToolRegistrationError."""
    registry = ToolRegistry()
    registry.register(DummyTool())

    with pytest.raises(ToolRegistrationError) as exc_info:
        registry.register(DummyTool(), override=False)
    assert "already registered" in str(exc_info.value)

    # Allowed with override=True
    registry.register(DummyTool(), override=True)
    assert registry.has_tool("dummy_test_tool") is True


def test_unknown_tool_rejection():
    """Verify requesting an unregistered tool raises ToolNotFoundError."""
    registry = ToolRegistry()
    with pytest.raises(ToolNotFoundError) as exc_info:
        registry.get("non_existent_tool_xyz")
    assert "not registered" in str(exc_info.value)


def test_tool_discovery_and_schema_export():
    """Verify tool discovery lists all registered tools and exports valid OpenAI schemas."""
    registry = ToolRegistry()
    populate_default_tools(registry)

    names = registry.list_tool_names()
    assert "search_destination" in names
    assert "search_attractions" in names
    assert "get_weather" in names
    assert "calculate_trip_budget"
    assert "estimate_travel_time" in names
    assert "search_accommodation" in names
    assert "retrieve_travel_knowledge" in names

    definitions = registry.list_tools()
    assert len(definitions) == 7
    assert all(isinstance(d, ToolDefinition) for d in definitions)

    openai_tools = registry.to_openai_tools()
    assert len(openai_tools) == 7
    first = openai_tools[0]
    assert first["type"] == "function"
    assert "name" in first["function"]
    assert "parameters" in first["function"]

