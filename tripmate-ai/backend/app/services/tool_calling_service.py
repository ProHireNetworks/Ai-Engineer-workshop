"""
TripMate AI - Tool Calling Service
Orchestrates autonomous multi-turn reasoning loops: tool selection, argument validation,
parallel execution, tool result ingestion, and final synthesis.
"""

import json
from typing import Any, List, Optional, Tuple, Type, TypeVar
from pydantic import BaseModel

from app.llm.base import BaseLLMProvider
from app.llm.factory import get_llm_provider
from app.llm.usage import LLMMessage, TokenUsage
from app.schemas.tool import ToolCallResult
from app.tools.executor import ToolExecutor
from app.tools.registry import ToolRegistry, tool_registry
from app.utils.logger import get_logger

logger = get_logger(__name__)
T = TypeVar("T", bound=BaseModel)


class ToolCallingService:
    """Service orchestrating iterative tool-calling reasoning loops."""

    def __init__(
        self,
        provider: Optional[BaseLLMProvider] = None,
        executor: Optional[ToolExecutor] = None,
        registry: Optional[ToolRegistry] = None,
        max_rounds: int = 5,
    ) -> None:
        self.provider = provider or get_llm_provider()
        self.registry = registry or tool_registry
        self.executor = executor or ToolExecutor(registry=self.registry)
        self.max_rounds = max_rounds

    async def run_chat(
        self,
        user_prompt: str,
        system_prompt: Optional[str] = None,
        enable_tools: bool = True,
        conversation_history: Optional[List[LLMMessage]] = None,
    ) -> Tuple[str, List[ToolCallResult], TokenUsage]:
        """
        Runs an autonomous tool-calling loop until the model emits a final answer
        or the maximum rounds safety threshold is reached.

        Returns:
            Tuple of (final_content, all_tool_results, total_token_usage)
        """
        messages: List[LLMMessage] = []
        if system_prompt:
            messages.append(LLMMessage(role="system", content=system_prompt))
        if conversation_history:
            messages.extend(conversation_history)
        messages.append(LLMMessage(role="user", content=user_prompt))

        cumulative_usage = TokenUsage()
        all_executed_tool_results: List[ToolCallResult] = []

        tools_def = self.registry.to_openai_tools() if enable_tools else []

        for round_num in range(1, self.max_rounds + 1):
            logger.debug("Tool-calling round %d/%d", round_num, self.max_rounds)

            # Call provider with tools
            if enable_tools and tools_def:
                response = await self.provider.generate_with_tools(
                    messages=messages,
                    tools=tools_def,
                    temperature=0.7,
                )
            else:
                response = await self.provider.generate(
                    messages=messages,
                    temperature=0.7,
                )

            cumulative_usage = cumulative_usage.add(response.usage)

            # If no tool calls requested, model has reached a final natural language answer
            if not response.tool_calls:
                return response.content, all_executed_tool_results, cumulative_usage

            logger.info(
                "Round %d: LLM requested %d tool calls: %s",
                round_num,
                len(response.tool_calls),
                [tc.name for tc in response.tool_calls],
            )

            # Record assistant turn with tool_calls in message history
            assistant_tool_msg = LLMMessage(
                role="assistant",
                content=response.content or "Calling requested tools...",
                tool_calls=[
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": json.dumps(tc.arguments) if isinstance(tc.arguments, dict) else str(tc.arguments),
                        },
                    }
                    for tc in response.tool_calls
                ],
            )
            messages.append(assistant_tool_msg)

            # Execute requested tool calls (concurrently when safe)
            round_results = await self.executor.execute_many(response.tool_calls)
            all_executed_tool_results.extend(round_results)

            # Append each tool result as a role="tool" message
            for tr in round_results:
                serialized_content = (
                    json.dumps(tr.result)
                    if isinstance(tr.result, (dict, list))
                    else str(tr.result)
                )
                if tr.status != "success":
                    serialized_content = json.dumps({"error": tr.error, "status": tr.status})

                messages.append(
                    LLMMessage(
                        role="tool",
                        content=serialized_content,
                        tool_call_id=tr.tool_call_id,
                        name=tr.tool_name,
                    )
                )

        # Reached max rounds without explicit completion; ask for final summary
        logger.warning("Reached maximum tool rounds (%d). Requesting final synthesis.", self.max_rounds)
        messages.append(
            LLMMessage(
                role="user",
                content="Please formulate your final response based on the tool results gathered so far.",
            )
        )
        final_response = await self.provider.generate(messages=messages, temperature=0.7)
        cumulative_usage = cumulative_usage.add(final_response.usage)
        return final_response.content, all_executed_tool_results, cumulative_usage

    async def run_structured(
        self,
        user_prompt: str,
        response_model: Type[T],
        system_prompt: Optional[str] = None,
        enable_tools: bool = True,
    ) -> Tuple[T, List[ToolCallResult], TokenUsage]:
        """
        Executes tool calls to gather ground truth, then enforces Pydantic structured output.
        """
        chat_content, tool_results, usage = await self.run_chat(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            enable_tools=enable_tools,
        )

        parse_messages = [
            LLMMessage(
                role="system",
                content=(
                    "Extract and synthesize the verified travel information into the requested structured JSON model."
                ),
            ),
            LLMMessage(role="user", content=f"Synthesize this planning context into schema:\n{chat_content}"),
        ]

        structured_model = await self.provider.generate_structured(
            messages=parse_messages, response_model=response_model
        )
        return structured_model, tool_results, usage

