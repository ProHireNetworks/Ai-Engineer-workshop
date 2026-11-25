"""
TripMate AI - Tool Execution Engine
Safe asynchronous tool executor with argument validation, timeout enforcement,
concurrency, error classification, and structured result wrapping.
"""

import asyncio
import time
import uuid
from typing import Any, Dict, List, Optional

from app.schemas.tool import ToolCall, ToolCallResult
from app.tools.exceptions import (
    ToolError,
    ToolExecutionError,
    ToolNotFoundError,
    ToolTimeoutError,
    ToolUnauthorizedError,
    ToolValidationError,
)
from app.tools.registry import ToolRegistry, tool_registry
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ToolExecutor:
    """Executes registered tools safely with timeout and error containment."""

    def __init__(
        self,
        registry: Optional[ToolRegistry] = None,
        max_retries: int = 1,
    ) -> None:
        self.registry = registry or tool_registry
        self.max_retries = max_retries

    async def execute_call(
        self,
        tool_call: ToolCall,
        is_authorized: bool = True,
    ) -> ToolCallResult:
        """
        Executes a single tool call request and returns a structured ToolCallResult.
        """
        start_time = time.perf_counter()
        tool_name = tool_call.name
        tool_call_id = tool_call.id or str(uuid.uuid4())

        logger.info("Executing tool call: '%s' [id=%s]", tool_name, tool_call_id)

        try:
            # 1. Lookup registered tool
            tool = self.registry.get(tool_name)

            # 2. Verify authorization
            if tool.requires_auth and not is_authorized:
                raise ToolUnauthorizedError(
                    f"Execution of tool '{tool_name}' requires explicit authorization.",
                    tool_name=tool_name,
                )

            # 3. Execute with controlled timeout and retries
            result_data = await self._execute_with_retry(
                tool=tool,
                args=tool_call.arguments,
                timeout=tool.timeout_seconds,
            )

            latency_ms = (time.perf_counter() - start_time) * 1000.0
            is_mock = isinstance(result_data, dict) and result_data.get("is_mock", False)

            return ToolCallResult(
                tool_call_id=tool_call_id,
                tool_name=tool_name,
                status="success",
                result=result_data,
                error=None,
                latency_ms=round(latency_ms, 2),
                is_mock=is_mock,
            )

        except ToolNotFoundError as exc:
            logger.warning("Tool not found: '%s'", tool_name)
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            return ToolCallResult(
                tool_call_id=tool_call_id,
                tool_name=tool_name,
                status="error",
                result=None,
                error=f"ToolNotFoundError: {exc.message}",
                latency_ms=round(latency_ms, 2),
            )
        except ToolUnauthorizedError as exc:
            logger.warning("Unauthorized execution attempt for tool: '%s'", tool_name)
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            return ToolCallResult(
                tool_call_id=tool_call_id,
                tool_name=tool_name,
                status="unauthorized",
                result=None,
                error=f"ToolUnauthorizedError: {exc.message}",
                latency_ms=round(latency_ms, 2),
            )
        except ToolValidationError as exc:
            logger.error("Argument validation failed for tool '%s': %s", tool_name, exc)
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            return ToolCallResult(
                tool_call_id=tool_call_id,
                tool_name=tool_name,
                status="error",
                result=None,
                error=f"ToolValidationError: {exc.message}",
                latency_ms=round(latency_ms, 2),
            )
        except ToolTimeoutError as exc:
            logger.error("Timeout executing tool '%s': %s", tool_name, exc)
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            return ToolCallResult(
                tool_call_id=tool_call_id,
                tool_name=tool_name,
                status="timeout",
                result=None,
                error=f"ToolTimeoutError: {exc.message}",
                latency_ms=round(latency_ms, 2),
            )
        except Exception as exc:
            logger.error("Unhandled error running tool '%s': %s", tool_name, exc, exc_info=True)
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            return ToolCallResult(
                tool_call_id=tool_call_id,
                tool_name=tool_name,
                status="error",
                result=None,
                error=f"ToolExecutionError: An unexpected failure occurred in {tool_name}: {str(exc)}",
                latency_ms=round(latency_ms, 2),
            )

    async def execute_many(
        self,
        tool_calls: List[ToolCall],
        is_authorized: bool = True,
    ) -> List[ToolCallResult]:
        """
        Executes a sequence of independent tool calls concurrently.
        """
        if not tool_calls:
            return []

        tasks = [
            self.execute_call(call, is_authorized=is_authorized)
            for call in tool_calls
        ]
        results = await asyncio.gather(*tasks)
        return list(results)

    async def _execute_with_retry(
        self, tool: Any, args: Dict[str, Any], timeout: float
    ) -> Any:
        """Executes a tool with timeout and controlled retry limit."""
        attempts = 0
        last_error: Optional[Exception] = None

        while attempts <= self.max_retries:
            try:
                attempts += 1
                return await asyncio.wait_for(tool.execute(**args), timeout=timeout)
            except asyncio.TimeoutError as timeout_exc:
                last_error = ToolTimeoutError(
                    f"Tool '{tool.name}' timed out after {timeout} seconds.",
                    tool_name=tool.name,
                )
                if attempts > self.max_retries:
                    raise last_error from timeout_exc
            except (ToolValidationError, ToolUnauthorizedError):
                # Never retry validation or authorization failures
                raise
            except Exception as exc:
                last_error = exc
                if attempts > self.max_retries:
                    raise ToolExecutionError(
                        f"Execution failed after {attempts} attempts: {str(exc)}",
                        tool_name=tool.name,
                    ) from exc

        if last_error:
            raise last_error

