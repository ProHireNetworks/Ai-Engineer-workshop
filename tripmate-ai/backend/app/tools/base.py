"""
TripMate AI - Tool Base Class
Abstract base interface for all tools with Pydantic argument validation,
OpenAI function schema export, and execution handlers.
"""

from abc import ABC, abstractmethod
import inspect
from typing import Any, Dict, Type
from pydantic import BaseModel, ValidationError

from app.schemas.tool import ToolDefinition
from app.tools.exceptions import ToolValidationError


class BaseTool(ABC):
    """Abstract base class for all tools available to agents and API callers."""

    name: str
    description: str
    args_schema: Type[BaseModel]
    requires_auth: bool = False
    timeout_seconds: float = 30.0

    def to_definition(self) -> ToolDefinition:
        """Converts tool metadata and argument schema into a standardized ToolDefinition."""
        schema = self.args_schema.model_json_schema()
        # Clean internal metadata keys if present
        schema.pop("title", None)
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters=schema,
            requires_auth=self.requires_auth,
            timeout_seconds=self.timeout_seconds,
        )

    def to_openai_tool(self) -> Dict[str, Any]:
        """Converts tool into OpenAI tool calling JSON specification."""
        schema = self.args_schema.model_json_schema()
        schema.pop("title", None)
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": schema,
            },
        }

    async def execute(self, **kwargs: Any) -> Any:
        """
        Validates arguments against args_schema and delegates to _run / _arun.

        Raises:
            ToolValidationError: If argument validation fails.
            ToolExecutionError: If execution raises an unhandled error.
        """
        try:
            validated = self.args_schema.model_validate(kwargs)
        except ValidationError as val_err:
            raise ToolValidationError(
                message=f"Invalid arguments for tool '{self.name}': {val_err}",
                tool_name=self.name,
                details={"errors": val_err.errors()},
            ) from val_err

        args_dict = validated.model_dump()
        return await self._run(**args_dict)

    @abstractmethod
    async def _run(self, **kwargs: Any) -> Any:
        """Core implementation of tool logic to be provided by subclasses."""
        pass

