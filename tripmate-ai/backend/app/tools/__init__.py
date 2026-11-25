"""TripMate AI Tools Package."""

from app.tools.accommodation import SearchAccommodationTool
from app.tools.base import BaseTool
from app.tools.cost_calculator import CalculateTripBudgetTool
from app.tools.exceptions import (
    ToolError,
    ToolExecutionError,
    ToolNotFoundError,
    ToolRegistrationError,
    ToolTimeoutError,
    ToolUnauthorizedError,
    ToolValidationError,
)
from app.tools.executor import ToolExecutor
from app.tools.registry import ToolRegistry, populate_default_tools, tool_registry
from app.tools.schemas import (
    AccommodationSearchArgs,
    AttractionsSearchArgs,
    BudgetCalculatorArgs,
    DestinationSearchArgs,
    TravelTimeArgs,
    WeatherArgs,
)
from app.tools.travel_search import (
    EstimateTravelTimeTool,
    SearchAttractionsTool,
    SearchDestinationTool,
)
from app.tools.weather import GetWeatherTool

__all__ = [
    "BaseTool",
    "ToolRegistry",
    "tool_registry",
    "populate_default_tools",
    "ToolExecutor",
    "SearchDestinationTool",
    "SearchAttractionsTool",
    "GetWeatherTool",
    "CalculateTripBudgetTool",
    "EstimateTravelTimeTool",
    "SearchAccommodationTool",
    "DestinationSearchArgs",
    "AttractionsSearchArgs",
    "WeatherArgs",
    "BudgetCalculatorArgs",
    "TravelTimeArgs",
    "AccommodationSearchArgs",
    "ToolError",
    "ToolNotFoundError",
    "ToolRegistrationError",
    "ToolValidationError",
    "ToolExecutionError",
    "ToolTimeoutError",
    "ToolUnauthorizedError",
]
