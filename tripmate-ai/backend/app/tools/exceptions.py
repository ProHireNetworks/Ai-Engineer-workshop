"""
TripMate AI - Tool Exceptions
Structured exceptions for tool validation, registration, execution, and authorization.
"""

from typing import Any, Dict, Optional


class ToolError(Exception):
    """Base exception for all tool operations."""

    def __init__(
        self,
        message: str,
        tool_name: str = "unknown",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.tool_name = tool_name
        self.details = details or {}


class ToolNotFoundError(ToolError):
    """Raised when an execution is attempted for an unregistered tool name."""


class ToolRegistrationError(ToolError):
    """Raised when a tool fails to register (e.g. duplicate name, invalid schema)."""


class ToolValidationError(ToolError):
    """Raised when provided arguments fail Pydantic schema validation."""


class ToolExecutionError(ToolError):
    """Raised when an unexpected exception occurs inside the tool implementation."""


class ToolTimeoutError(ToolError):
    """Raised when tool execution exceeds the configured timeout limit."""


class ToolUnauthorizedError(ToolError):
    """Raised when a caller lacks permissions to run an authorized tool."""

