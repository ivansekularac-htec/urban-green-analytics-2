"""Prometheus metrics for model-facing MCP tool calls."""

from collections.abc import Callable
from functools import wraps
from inspect import iscoroutinefunction
from time import perf_counter
from typing import Any

from prometheus_client import Counter, Histogram

TOOL_CALLS = Counter(
    "mcp_tool_calls_total",
    "Number of MCP tool calls by tool and outcome.",
    labelnames=("tool", "outcome"),
)

TOOL_DURATION = Histogram(
    "mcp_tool_duration_seconds",
    "Wall-clock duration of MCP tool calls in seconds.",
    labelnames=("tool",),
)


def _result_outcome(result: Any) -> str:
    """Classify the structured error payload used by the tool layer."""

    if isinstance(result, dict) and "error" in result:
        return "error"

    return "ok"


def _record_call(tool: str, outcome: str, started_at: float) -> None:
    """Record one completed call, including calls that raised."""

    TOOL_CALLS.labels(tool=tool, outcome=outcome).inc()
    TOOL_DURATION.labels(tool=tool).observe(perf_counter() - started_at)


def track_tool(name: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Track calls, outcomes and duration for a sync or async MCP tool."""

    def decorator(function: Callable[..., Any]) -> Callable[..., Any]:
        if iscoroutinefunction(function):

            @wraps(function)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                started_at = perf_counter()
                outcome = "error"

                try:
                    result = await function(*args, **kwargs)
                    outcome = _result_outcome(result)
                    return result
                finally:
                    _record_call(name, outcome, started_at)

            return async_wrapper

        @wraps(function)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            started_at = perf_counter()
            outcome = "error"

            try:
                result = function(*args, **kwargs)
                outcome = _result_outcome(result)
                return result
            finally:
                _record_call(name, outcome, started_at)

        return sync_wrapper

    return decorator
