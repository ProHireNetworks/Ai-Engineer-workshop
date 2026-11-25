"""
TripMate AI - Tools API Endpoints
Allows listing registered tools and executing tools directly with schema validation.
"""

import uuid
from typing import List
from fastapi import APIRouter, HTTPException, status

from app.schemas.tool import (
    ToolCall,
    ToolDefinition,
    ToolExecuteRequest,
    ToolExecuteResponse,
)
from app.tools.executor import ToolExecutor
from app.tools.registry import tool_registry
from app.utils.logger import get_logger

router = APIRouter(prefix="/tools", tags=["Tools"])
logger = get_logger(__name__)
executor = ToolExecutor(registry=tool_registry)


@router.get(
    "",
    response_model=List[ToolDefinition],
    status_code=status.HTTP_200_OK,
    summary="List Registered Tools",
    description="Returns metadata, accepted parameters, and JSON schemas for all registered tools.",
)
async def list_tools() -> List[ToolDefinition]:
    """Returns the catalog of all tools currently available to agents."""
    return tool_registry.list_tools()


@router.post(
    "/execute",
    response_model=ToolExecuteResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute Tool Ad-Hoc",
    description="Executes a specified registered tool with argument validation and timeout enforcement.",
)
async def execute_tool(request: ToolExecuteRequest) -> ToolExecuteResponse:
    """Directly executes an authorized tool."""
    if not tool_registry.has_tool(request.tool_name):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool '{request.tool_name}' not found. Available tools: {tool_registry.list_tool_names()}",
        )

    tool_call = ToolCall(
        id=f"api_{uuid.uuid4().hex[:8]}",
        name=request.tool_name,
        arguments=request.arguments,
    )

    result = await executor.execute_call(tool_call, is_authorized=True)

    return ToolExecuteResponse(
        execution_id=tool_call.id,
        tool_name=result.tool_name,
        status=result.status,
        result=result.result,
        error=result.error,
        latency_ms=result.latency_ms,
    )

