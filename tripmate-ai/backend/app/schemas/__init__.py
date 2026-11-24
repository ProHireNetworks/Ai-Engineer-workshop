"""TripMate AI Pydantic Validation Schemas."""
from app.schemas.agent_output import AgentExecutionResult
from app.schemas.health import HealthResponse, ServiceCheck
from app.schemas.llm import LLMStatusResponse
from app.schemas.tool import (
    ToolCall,
    ToolCallResult,
    ToolDefinition,
    ToolExecuteRequest,
    ToolExecuteResponse,
)
from app.schemas.trip import (
    AccommodationOption,
    Attraction,
    BudgetBreakdown,
    DailyItinerary,
    DestinationResearch,
    TripRequest,
    TripResponse,
    WeatherInformation,
)

__all__ = [
    "HealthResponse",
    "ServiceCheck",
    "LLMStatusResponse",
    "ToolDefinition",
    "ToolCall",
    "ToolCallResult",
    "ToolExecuteRequest",
    "ToolExecuteResponse",
    "TripRequest",
    "DestinationResearch",
    "Attraction",
    "WeatherInformation",
    "BudgetBreakdown",
    "DailyItinerary",
    "AccommodationOption",
    "TripResponse",
    "AgentExecutionResult",
]

