"""
Unit tests for MCP tool-call instrumentation.

Covers the outcome track_tool derives from a tool's return value (a dict
with an "error" key vs anything else) and from a raised exception, that a
raised exception still propagates to the caller, and the Prometheus
exposition body /metrics ultimately serves.
"""

import asyncio
import inspect

import pytest
from prometheus_client import REGISTRY, generate_latest

from app.metrics import track_tool


def test_normal_return_is_recorded_as_ok():
    @track_tool("sample_tool")
    def sample_tool() -> dict:
        return {"rows": []}

    sample_tool()

    assert (
        REGISTRY.get_sample_value("mcp_tool_calls_total", {"tool": "sample_tool", "outcome": "ok"})
        == 1.0
    )
    assert (
        REGISTRY.get_sample_value("mcp_tool_duration_seconds_count", {"tool": "sample_tool"}) == 1.0
    )


# ---------------------------------------------------------------------------
# outcome="error" via the tools.py error-dict contract
# ---------------------------------------------------------------------------


def test_error_dict_return_is_recorded_as_error():
    @track_tool("sample_tool")
    def sample_tool() -> dict:
        return {"error": "bad input"}

    sample_tool()

    assert (
        REGISTRY.get_sample_value(
            "mcp_tool_calls_total", {"tool": "sample_tool", "outcome": "error"}
        )
        == 1.0
    )
    assert (
        REGISTRY.get_sample_value("mcp_tool_calls_total", {"tool": "sample_tool", "outcome": "ok"})
        is None
    )


def test_async_tool_error_dict_return_is_recorded_as_error():
    @track_tool("async_sample_tool")
    async def async_sample_tool() -> dict:
        return {"error": "bad input"}

    asyncio.run(async_sample_tool())

    assert (
        REGISTRY.get_sample_value(
            "mcp_tool_calls_total",
            {"tool": "async_sample_tool", "outcome": "error"},
        )
        == 1.0
    )


# ---------------------------------------------------------------------------
# outcome="error" via a raised exception
# ---------------------------------------------------------------------------


def test_raised_exception_is_recorded_as_error_and_still_propagates():
    @track_tool("sample_tool")
    def sample_tool() -> dict:
        raise ValueError("boom")

    with pytest.raises(ValueError, match="boom"):
        sample_tool()

    assert (
        REGISTRY.get_sample_value(
            "mcp_tool_calls_total", {"tool": "sample_tool", "outcome": "error"}
        )
        == 1.0
    )


def test_raised_exception_from_an_async_tool_still_propagates():
    @track_tool("async_sample_tool")
    async def async_sample_tool() -> dict:
        raise ValueError("boom")

    with pytest.raises(ValueError, match="boom"):
        asyncio.run(async_sample_tool())

    assert (
        REGISTRY.get_sample_value(
            "mcp_tool_calls_total",
            {"tool": "async_sample_tool", "outcome": "error"},
        )
        == 1.0
    )


# ---------------------------------------------------------------------------
# FastMCP introspection
# ---------------------------------------------------------------------------


def test_decorator_preserves_the_wrapped_functions_signature():
    """FastMCP builds each tool's schema from the function signature, so a
    wrapper that hid the real parameters behind *args, **kwargs would break
    every tool it was applied to."""

    def sample_tool(table: str, database: str = "urbangreen_dw") -> dict:
        return {}

    wrapped = track_tool("sample_tool")(sample_tool)

    assert inspect.signature(wrapped) == inspect.signature(sample_tool)
    assert wrapped.__name__ == "sample_tool"


# ---------------------------------------------------------------------------
# Rendered exposition body
# ---------------------------------------------------------------------------


def test_rendered_body_contains_the_tool_metric_names():
    @track_tool("sample_tool")
    def sample_tool() -> dict:
        return {"rows": []}

    sample_tool()

    body = generate_latest(REGISTRY).decode()

    assert "mcp_tool_calls_total" in body
    assert "mcp_tool_duration_seconds" in body
    assert 'mcp_tool_calls_total{outcome="ok",tool="sample_tool"} 1.0' in body
