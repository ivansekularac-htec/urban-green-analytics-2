"""Prometheus metrics for MCP tool calls."""

import functools
import inspect
import time
from collections.abc import Callable
from typing import TypeVar

from prometheus_client import Counter, Histogram

F = TypeVar("F", bound=Callable)

TOOL_CALLS = Counter(
    "mcp_tool_calls_total",
    "MCP tool calls by tool and outcome.",
    ("tool", "outcome"),
)
TOOL_DURATION = Histogram(
    "mcp_tool_duration_seconds",
    "Wall-clock duration of MCP tool calls in seconds.",
    ("tool",),
)


def reset_metrics() -> None:
    """Drop recorded samples so tests cannot leak counts into siblings."""
    TOOL_CALLS.clear()
    TOOL_DURATION.clear()


def _outcome(result: object) -> str:
    if isinstance(result, dict) and "error" in result:
        return "error"
    return "ok"


def track_tool(name: str) -> Callable[[F], F]:
    """Record call count, outcome, and duration. Preserves the wrapped signature."""

    def decorator(fn: F) -> F:
        if inspect.iscoroutinefunction(fn):

            @functools.wraps(fn)
            async def async_wrapper(*args, **kwargs):
                started = time.perf_counter()
                outcome = "ok"
                try:
                    result = await fn(*args, **kwargs)
                    outcome = _outcome(result)
                    return result
                except Exception:
                    outcome = "error"
                    raise
                finally:
                    TOOL_DURATION.labels(tool=name).observe(time.perf_counter() - started)
                    TOOL_CALLS.labels(tool=name, outcome=outcome).inc()

            return async_wrapper  # type: ignore[return-value]

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            started = time.perf_counter()
            outcome = "ok"
            try:
                result = fn(*args, **kwargs)
                outcome = _outcome(result)
                return result
            except Exception:
                outcome = "error"
                raise
            finally:
                TOOL_DURATION.labels(tool=name).observe(time.perf_counter() - started)
                TOOL_CALLS.labels(tool=name, outcome=outcome).inc()

        return wrapper  # type: ignore[return-value]

    return decorator
