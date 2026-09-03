"""Prometheus instrumentation for the MCP tools.

Every registered tool is wrapped by `track_tool`, which records one call on a
Counter (labelled by tool and outcome) and its wall-clock duration on a
Histogram (labelled by tool). The App Performance dashboard reads these to show
how the model is using the warehouse.

`outcome` is `"error"` in the two ways a tool can fail under this server's
contract: it raises, or it returns a dict carrying an `"error"` key (the shape
`app.tools` uses for a handled failure). Everything else is `"ok"`. A raised
exception is still propagated after it is counted, so behaviour is unchanged.

The wrapper preserves the wrapped function with `functools.wraps`, so it can sit
between `@mcp.tool` and the definition without disturbing FastMCP's schema: the
model still sees the original parameters, and an injected `Context` stays hidden.
It keeps the sync or async nature of the tool it wraps, because FastMCP awaits a
tool only when its function is a coroutine.
"""

from __future__ import annotations

import asyncio
import functools
import time
from collections.abc import Callable
from typing import Any, TypeVar

from prometheus_client import Counter, Histogram

F = TypeVar("F", bound=Callable[..., Any])

OUTCOME_OK = "ok"
OUTCOME_ERROR = "error"

TOOL_CALLS = Counter(
    "mcp_tool_calls",
    "Number of MCP tool calls by tool and outcome.",
    ["tool", "outcome"],
)

TOOL_DURATION = Histogram(
    "mcp_tool_duration_seconds",
    "Wall-clock duration of MCP tool calls in seconds.",
    ["tool"],
)


def _is_error_result(result: Any) -> bool:
    """A handled failure is a dict carrying an `error` key, per `app.tools`."""
    return isinstance(result, dict) and "error" in result


def _record(tool: str, outcome: str, started: float) -> None:
    TOOL_DURATION.labels(tool=tool).observe(time.perf_counter() - started)
    TOOL_CALLS.labels(tool=tool, outcome=outcome).inc()


def track_tool(name: str) -> Callable[[F], F]:
    """Wrap a tool so each call is counted and timed.

    Args:
        name: The tool label the call is recorded under.

    The wrapper matches the coroutine-ness of the wrapped function so it can be
    awaited exactly when the original would be.
    """

    def decorate(func: F) -> F:
        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                started = time.perf_counter()
                try:
                    result = await func(*args, **kwargs)
                except Exception:
                    _record(name, OUTCOME_ERROR, started)
                    raise
                _record(name, OUTCOME_ERROR if _is_error_result(result) else OUTCOME_OK, started)
                return result

            return async_wrapper  # type: ignore[return-value]

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            started = time.perf_counter()
            try:
                result = func(*args, **kwargs)
            except Exception:
                _record(name, OUTCOME_ERROR, started)
                raise
            _record(name, OUTCOME_ERROR if _is_error_result(result) else OUTCOME_OK, started)
            return result

        return sync_wrapper  # type: ignore[return-value]

    return decorate
