"""
Prometheus instrumentation for MCP tool calls.

Every registered tool is wrapped with `track_tool`, which records a call
count (labelled by tool and outcome) and a wall-clock duration histogram.
`outcome` is "ok" on a normal return and "error" both when the tool raises
and when it returns a dict containing an "error" key - the same contract
`app.tools` already uses (see T5.1.4), so a tool doesn't need to know it's
being measured in order to report correctly.
"""

import inspect
import time
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from prometheus_client import Counter, Histogram

F = TypeVar("F", bound=Callable[..., Any])

TOOL_CALLS = Counter(
    "mcp_tool_calls_total",
    "Total number of MCP tool calls by tool and outcome.",
    ["tool", "outcome"],
)

TOOL_DURATION = Histogram(
    "mcp_tool_duration_seconds",
    "Wall-clock duration of MCP tool calls, by tool.",
    ["tool"],
)


def _outcome(result: object) -> str:
    """Return "ok" unless the tool's own error-dict contract says otherwise."""

    if isinstance(result, dict) and "error" in result:
        return "error"

    return "ok"


def track_tool(name: str) -> Callable[[F], F]:
    """
    Wrap a tool function to record its call count and duration.

    Sits between `@mcp.tool` and the function definition::

        @mcp.tool
        @track_tool("list_tables")
        def list_tables(...): ...

    Works on both sync and async tools. Preserves the wrapped function's
    signature via `functools.wraps` so FastMCP still builds the tool schema
    from the real parameters instead of `*args, **kwargs`.

    An exception is recorded as `outcome="error"` and re-raised unchanged -
    the decorator observes, it doesn't handle.

    Args:
        name: Label value identifying the tool being wrapped, e.g. the tool's
            registered name.
    """

    def decorator(func: F) -> F:
        if inspect.iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                start = time.perf_counter()
                outcome = "error"
                try:
                    result = await func(*args, **kwargs)
                    outcome = _outcome(result)
                    return result
                finally:
                    TOOL_DURATION.labels(tool=name).observe(time.perf_counter() - start)
                    TOOL_CALLS.labels(tool=name, outcome=outcome).inc()

            return async_wrapper  # type: ignore[return-value]

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            outcome = "error"
            try:
                result = func(*args, **kwargs)
                outcome = _outcome(result)
                return result
            finally:
                TOOL_DURATION.labels(tool=name).observe(time.perf_counter() - start)
                TOOL_CALLS.labels(tool=name, outcome=outcome).inc()

        return sync_wrapper  # type: ignore[return-value]

    return decorator
