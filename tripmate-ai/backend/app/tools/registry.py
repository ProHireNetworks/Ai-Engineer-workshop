"""
TripMate AI - Central Tool Registry
Maintains unique registration, discovery, schema exports, and validation for all tools.
"""

from typing import Any, Dict, List, Optional
from app.schemas.tool import ToolDefinition
from app.tools.accommodation import SearchAccommodationTool
from app.tools.base import BaseTool
from app.tools.cost_calculator import CalculateTripBudgetTool
from app.tools.exceptions import ToolNotFoundError, ToolRegistrationError
from app.tools.rag_search import RetrieveTravelKnowledgeTool
from app.tools.travel_search import (
    EstimateTravelTimeTool,
    SearchAttractionsTool,
    SearchDestinationTool,
)
from app.tools.weather import GetWeatherTool
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ToolRegistry:
    """Centralized catalog managing tool registrations, schemas, and lookups."""

    def __init__(self) -> None:
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool, override: bool = False) -> None:
        """
        Registers a tool instance in the registry.

        Args:
            tool: The tool instance inheriting from BaseTool.
            override: If False, raises ToolRegistrationError on duplicate names.
        """
        if not tool.name or not isinstance(tool.name, str):
            raise ToolRegistrationError("Tool must have a valid non-empty string name.")

        if tool.name in self._tools and not override:
            raise ToolRegistrationError(
                f"Tool '{tool.name}' is already registered. Use override=True to replace.",
                tool_name=tool.name,
            )

        self._tools[tool.name] = tool
        logger.debug("Registered tool: '%s'", tool.name)

    def get(self, name: str) -> BaseTool:
        """
        Retrieves a registered tool by its name.

        Raises:
            ToolNotFoundError: If name is not present in registry.
        """
        if name not in self._tools:
            raise ToolNotFoundError(
                f"Tool '{name}' is not registered in the system.",
                tool_name=name,
                details={"available_tools": list(self._tools.keys())},
            )
        return self._tools[name]

    def has_tool(self, name: str) -> bool:
        """Checks if a tool name is registered."""
        return name in self._tools

    def list_tools(self) -> List[ToolDefinition]:
        """Returns standard definition schemas for all registered tools."""
        return [tool.to_definition() for tool in self._tools.values()]

    def list_tool_names(self) -> List[str]:
        """Returns a list of all registered tool names."""
        return list(self._tools.keys())

    def to_openai_tools(self) -> List[Dict[str, Any]]:
        """Exports all registered tools formatted for OpenAI tool calling."""
        return [tool.to_openai_tool() for tool in self._tools.values()]

    def clear(self) -> None:
        """Clears all registered tools (used in isolated unit testing)."""
        self._tools.clear()


# Global registry singleton populated with standard TripMate AI tools
tool_registry = ToolRegistry()


def populate_default_tools(registry: ToolRegistry = tool_registry) -> None:
    """Initializes the default suite of trip planning tools."""
    default_tools: List[BaseTool] = [
        SearchDestinationTool(),
        SearchAttractionsTool(),
        GetWeatherTool(),
        CalculateTripBudgetTool(),
        EstimateTravelTimeTool(),
        SearchAccommodationTool(),
        RetrieveTravelKnowledgeTool(),
    ]
    for tool in default_tools:
        if not registry.has_tool(tool.name):
            registry.register(tool)


# Initialize standard tools at module import
populate_default_tools()

