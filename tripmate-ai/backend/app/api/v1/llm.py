"""
TripMate AI - LLM Diagnostics Endpoint
Provides live operational status and model availability metrics without leaking keys.
"""

from typing import List, Optional
from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from app.llm.factory import get_llm_provider
from app.llm.usage import TokenUsage
from app.schemas.llm import LLMStatusResponse
from app.schemas.tool import ToolCallResult
from app.services.tool_calling_service import ToolCallingService
from app.utils.logger import get_logger

router = APIRouter(prefix="/llm", tags=["LLM Provider"])
logger = get_logger(__name__)


class ChatRequest(BaseModel):
    """Payload for conversational interaction supporting tool calling."""

    message: str = Field(..., min_length=1, max_length=2000, description="User prompt or inquiry")
    enable_tools: bool = Field(default=True, description="Whether to allow the model to invoke registered tools")
    system_prompt: Optional[str] = Field(default=None, description="Optional custom system instructions")


class ChatResponse(BaseModel):
    """Response containing assistant text, executed tools audit, and token consumption."""

    response: str = Field(..., description="Final assistant conversational response")
    tool_calls_executed: List[ToolCallResult] = Field(
        default_factory=list, description="Audit log of all tools called during this turn"
    )
    token_usage: TokenUsage = Field(default_factory=TokenUsage)


@router.get(
    "/status",
    response_model=LLMStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="LLM Provider Operational Status",
    description="Returns current availability, active model, and latency for the configured LLM provider.",
)
async def get_llm_status() -> LLMStatusResponse:
    """Checks and returns the status of the configured LLM provider."""
    logger.debug("LLM status check requested")
    provider = get_llm_provider()

    try:
        health = await provider.health_check()
        return LLMStatusResponse(
            provider=health.provider,
            model=health.model,
            is_available=health.is_available,
            is_mock=health.is_mock,
            latency_ms=health.latency_ms,
            details=health.details,
            error=health.error,
        )
    except Exception as exc:
        logger.error("LLM status check failed unexpectedly: %s", exc, exc_info=True)
        return LLMStatusResponse(
            provider=provider.get_provider_name(),
            model=provider.get_model_name(),
            is_available=False,
            is_mock=(provider.get_provider_name() == "mock"),
            error=str(exc),
        )


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Conversational Chat with Tool Calling",
    description="Processes user inquiries, decides and executes necessary tools, and returns synthesized answers.",
)
async def chat_with_tools(request: ChatRequest) -> ChatResponse:
    """Conversational endpoint executing tool-calling loops."""
    service = ToolCallingService()
    content, tool_results, usage = await service.run_chat(
        user_prompt=request.message,
        system_prompt=request.system_prompt,
        enable_tools=request.enable_tools,
    )
    return ChatResponse(
        response=content,
        tool_calls_executed=tool_results,
        token_usage=usage,
    )

