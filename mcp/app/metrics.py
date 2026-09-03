"""Prometheus metrics for MCP tool execution."""

from collections.abc import Callable
from functools import wraps
from inspect import iscoroutinefunction
from time import perf_counter
from typing import Any, TypeVar, cast

from prometheus_client import Counter, Histogram

F = TypeVar("F", bound=Callable[..., Any])

TOOL_CALLS = Counter(
    "mcp_tool_calls_total",
    "Total number of MCP tool calls.",
    ["tool", "outcome"],
)

TOOL_DURATION = Histogram(
    "mcp_tool_duration_seconds",
    "Wall-clock duration of MCP tool calls.",
    ["tool"],
)


def _outcome(result: Any) -> str:
    """Return the Prometheus outcome label for a tool result."""
    return "error" if isinstance(result, dict) and "error" in result else "ok"


def track_tool(name: str) -> Callable[[F], F]:
    """Track call outcome and wall-clock duration for an MCP tool.

    Structured error dictionaries and raised exceptions are recorded as
    errors. Raised exceptions are re-raised unchanged.
    """

    def decorator(func: F) -> F:
        # Preserve coroutine behavior so FastMCP can introspect async tools correctly.
        if iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                started_at = perf_counter()

                try:
                    result = await func(*args, **kwargs)
                except Exception:
                    TOOL_CALLS.labels(tool=name, outcome="error").inc()
                    raise
                else:
                    TOOL_CALLS.labels(tool=name, outcome=_outcome(result)).inc()
                    return result
                finally:
                    TOOL_DURATION.labels(tool=name).observe(perf_counter() - started_at)

            return cast(F, async_wrapper)

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            started_at = perf_counter()

            try:
                result = func(*args, **kwargs)
            except Exception:
                TOOL_CALLS.labels(tool=name, outcome="error").inc()
                raise
            else:
                TOOL_CALLS.labels(tool=name, outcome=_outcome(result)).inc()
                return result
            finally:
                TOOL_DURATION.labels(tool=name).observe(perf_counter() - started_at)

        return cast(F, wrapper)

    return decorator
