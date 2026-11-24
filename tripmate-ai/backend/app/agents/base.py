"""
TripMate AI - Base Agent Architecture
Defines common execution lifecycle, tool-scoping, token tracking,
and standardized AgentExecutionResult output.
"""

from abc import ABC, abstractmethod
import time
from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar
from pydantic import BaseModel

from app.llm.base import BaseLLMProvider
from app.llm.factory import get_llm_provider
from app.llm.usage import LLMMessage, TokenUsage
from app.prompts.system_prompts import PROMPT_GUARD_SYSTEM_PROMPT
from app.schemas.agent_output import AgentExecutionResult
from app.schemas.tool import ToolCallResult
from app.tools.executor import ToolExecutor
from app.tools.registry import ToolRegistry, tool_registry
from app.utils.logger import agent_id_ctx, get_logger

logger = get_logger(__name__)
T = TypeVar("T", bound=BaseModel)


class BaseAgent(ABC):
    """Abstract base class for all TripMate AI specialized agents."""

    name: str
    system_prompt: str
    allowed_tools: List[str] = []

    def __init__(
        self,
        provider: Optional[BaseLLMProvider] = None,
        registry: Optional[ToolRegistry] = None,
        executor: Optional[ToolExecutor] = None,
    ) -> None:
        self.provider = provider or get_llm_provider()
        self.registry = registry or tool_registry
        self.executor = executor or ToolExecutor(registry=self.registry)

    def get_scoped_tools(self) -> List[Dict[str, Any]]:
        """Returns OpenAI-compatible tool specifications restricted strictly to allowed_tools."""
        all_tools = self.registry.to_openai_tools()
        if not self.allowed_tools:
            return []
        return [
            t for t in all_tools
            if (t.get("function", {}).get("name") in self.allowed_tools)
        ]

    @abstractmethod
    async def run(self, **kwargs: Any) -> AgentExecutionResult:
        """Executes the agent's core task and returns an AgentExecutionResult."""
        pass

    async def execute_reasoning_cycle(
        self,
        user_prompt: str,
        response_model: Optional[Type[T]] = None,
        max_rounds: int = 3,
        extra_messages: Optional[List[LLMMessage]] = None,
    ) -> Tuple[Any, List[ToolCallResult], TokenUsage]:
        """
        Executes a bounded tool-reasoning loop scoped to this agent's allowed tools.
        Optionally extracts structured Pydantic output.
        """
        token = agent_id_ctx.set(self.name)
        start_time = time.perf_counter()
        cumulative_usage = TokenUsage()
        tool_results: List[ToolCallResult] = []

        try:
            messages: List[LLMMessage] = [
                LLMMessage(role="system", content=self.system_prompt)
            ]
            if extra_messages:
                messages.extend(extra_messages)
            messages.append(LLMMessage(role="user", content=user_prompt))

            scoped_tools = self.get_scoped_tools()

            for round_idx in range(1, max_rounds + 1):
                if scoped_tools:
                    response = await self.provider.generate_with_tools(
                        messages=messages,
                        tools=scoped_tools,
                        temperature=0.3 if response_model else 0.7,
                    )
                else:
                    response = await self.provider.generate(
                        messages=messages,
                        temperature=0.3 if response_model else 0.7,
                    )

                cumulative_usage = cumulative_usage.add(response.usage)

                if not response.tool_calls:
                    final_text = response.content
                    break

                # Execute requested tools
                executed = await self.executor.execute_many(response.tool_calls)
                tool_results.extend(executed)

                # Record assistant message with tool calls
                messages.append(
                    LLMMessage(
                        role="assistant",
                        content=response.content or "Processing tool results...",
                        tool_calls=[
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.name,
                                    "arguments": str(tc.arguments),
                                },
                            }
                            for tc in response.tool_calls
                        ],
                    )
                )

                # Append tool returns
                import json
                for r in executed:
                    serialized = json.dumps(r.result) if isinstance(r.result, (dict, list)) else str(r.result)
                    messages.append(
                        LLMMessage(
                            role="tool",
                            content=serialized,
                            tool_call_id=r.tool_call_id,
                            name=r.tool_name,
                        )
                    )
            else:
                final_text = "Completed tool-assisted analysis."

            # If response_model specified, parse into structured schema
            if response_model is not None:
                parsed_model = await self.provider.generate_structured(
                    messages=[
                        LLMMessage(role="system", content=self.system_prompt),
                        LLMMessage(role="user", content=f"Produce structured schema from:\n{final_text}\nTool Results: {[r.result for r in tool_results]}"),
                    ],
                    response_model=response_model,
                )
                return parsed_model, tool_results, cumulative_usage

            return final_text, tool_results, cumulative_usage

        finally:
            agent_id_ctx.reset(token)
