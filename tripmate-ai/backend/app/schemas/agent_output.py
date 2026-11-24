"""
TripMate AI - Agent Output Schemas
Standardized envelopes for individual agent execution results, tool invocations,
token accounting, and execution errors.
"""

from typing import Any, List, Literal, Optional
from pydantic import BaseModel, Field
from app.llm.usage import TokenUsage
from app.schemas.tool import ToolCallResult


class AgentExecutionResult(BaseModel):
    """Encapsulates the final or intermediate output from an individual agent node."""

    agent_name: str = Field(..., description="Identity of the agent that executed")
    status: Literal["success", "failure", "interrupted", "retrying"] = Field(
        ..., description="Execution status of this agent turn"
    )
    output: Any = Field(default=None, description="Domain output model or payload")
    tool_calls_made: List[ToolCallResult] = Field(
        default_factory=list, description="Audit record of all tool calls made during this execution"
    )
    token_usage: Optional[TokenUsage] = Field(
        default_factory=TokenUsage, description="Total tokens consumed by this agent"
    )
    latency_ms: float = Field(default=0.0, ge=0.0, description="Execution duration in milliseconds")
    errors: List[str] = Field(
        default_factory=list, description="Any warnings or error traces encountered"
    )

