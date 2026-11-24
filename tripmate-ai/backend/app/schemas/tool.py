"""
TripMate AI - Tool Schemas
Pydantic schemas for tool registration, tool calls, and execution results.
"""

from typing import Any, Dict, Literal, Optional
from pydantic import BaseModel, Field


class ToolDefinition(BaseModel):
    """Metadata and JSON schema specification for a registered tool."""

    name: str = Field(..., description="Unique tool identifier")
    description: str = Field(..., description="Description of the tool purpose and capabilities")
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="JSON schema defining accepted arguments"
    )
    requires_auth: bool = Field(
        default=False, description="Whether execution requires elevated authorization"
    )
    timeout_seconds: float = Field(
        default=30.0, ge=1.0, le=300.0, description="Maximum execution timeout in seconds"
    )


class ToolCall(BaseModel):
    """Represents an invocation request emitted by an LLM."""

    id: str = Field(..., description="Unique tool call correlation ID")
    name: str = Field(..., description="Target tool name")
    arguments: Dict[str, Any] = Field(
        default_factory=dict, description="Parsed dictionary of arguments"
    )


class ToolCallResult(BaseModel):
    """Standardized result returned after executing a tool."""

    tool_call_id: str = Field(..., description="Original tool call correlation ID")
    tool_name: str = Field(..., description="Executed tool name")
    status: Literal["success", "error", "timeout", "unauthorized"] = Field(
        ..., description="Execution outcome status"
    )
    result: Any = Field(default=None, description="Serialized output payload on success")
    error: Optional[str] = Field(default=None, description="Error message if execution failed")
    latency_ms: float = Field(default=0.0, ge=0.0, description="Execution duration in milliseconds")
    is_mock: bool = Field(default=False, description="Flag indicating if output is simulated mock data")


class ToolExecuteRequest(BaseModel):
    """Public API payload for ad-hoc tool execution."""

    tool_name: str = Field(..., description="Registered tool name to execute")
    arguments: Dict[str, Any] = Field(
        default_factory=dict, description="Dictionary of tool arguments conforming to schema"
    )


class ToolExecuteResponse(BaseModel):
    """API response for tool execution."""

    execution_id: str = Field(..., description="Unique tracking identifier for this execution")
    tool_name: str = Field(..., description="Executed tool identifier")
    status: Literal["success", "error", "timeout", "unauthorized"] = Field(...)
    result: Any = Field(default=None, description="Returned tool data")
    error: Optional[str] = Field(default=None, description="Error diagnostic on failure")
    latency_ms: float = Field(default=0.0, ge=0.0)

