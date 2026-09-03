"""Tests for the tool-call metrics.

These pin the contract the dashboard depends on: a call is counted once under
its tool with the right `outcome`, its duration is observed, a raised exception
is still propagated, and the rendered exposition names the metrics. The Counter
and Histogram are process-wide singletons, so an autouse fixture clears their
label children around each test to keep the counts isolated.
"""

import asyncio

import pytest
from prometheus_client import REGISTRY, generate_latest

from app.metrics import TOOL_CALLS, TOOL_DURATION, track_tool


@pytest.fixture(autouse=True)
def _reset_metrics():
    TOOL_CALLS.clear()
    TOOL_DURATION.clear()
    yield
    TOOL_CALLS.clear()
    TOOL_DURATION.clear()


def _calls(tool: str, outcome: str) -> float | None:
    return REGISTRY.get_sample_value("mcp_tool_calls_total", {"tool": tool, "outcome": outcome})


def _duration_count(tool: str) -> float | None:
    return REGISTRY.get_sample_value("mcp_tool_duration_seconds_count", {"tool": tool})


def test_a_normal_return_is_counted_ok_and_timed():
    @track_tool("list_tables")
    def tool() -> dict:
        return {"tables": []}

    assert tool() == {"tables": []}

    assert _calls("list_tables", "ok") == 1.0
    assert _calls("list_tables", "error") is None
    assert _duration_count("list_tables") == 1.0


def test_an_error_dict_is_counted_error():
    """A handled failure comes back as a dict with an `error` key, not a raise."""

    @track_tool("execute_query")
    def tool() -> dict:
        return {"error": "SQL rejected"}

    result = tool()

    assert result == {"error": "SQL rejected"}
    assert _calls("execute_query", "error") == 1.0
    assert _calls("execute_query", "ok") is None


def test_a_raise_is_counted_error_and_still_propagates():
    @track_tool("describe_table")
    def tool() -> dict:
        raise ValueError("boom")

    with pytest.raises(ValueError, match="boom"):
        tool()

    assert _calls("describe_table", "error") == 1.0
    assert _duration_count("describe_table") == 1.0


def test_an_async_tool_is_tracked_and_stays_awaitable():
    @track_tool("read_warehouse_resource")
    async def tool() -> str:
        return "conventions text"

    assert asyncio.iscoroutinefunction(tool)
    assert asyncio.run(tool()) == "conventions text"
    assert _calls("read_warehouse_resource", "ok") == 1.0


def test_an_async_error_dict_is_counted_error():
    @track_tool("read_warehouse_resource")
    async def tool() -> dict:
        return {"error": "missing"}

    asyncio.run(tool())

    assert _calls("read_warehouse_resource", "error") == 1.0


def test_the_exposition_names_both_metrics():
    @track_tool("list_tables")
    def tool() -> dict:
        return {"ok": True}

    tool()
    body = generate_latest().decode("utf-8")

    assert "mcp_tool_calls_total" in body
    assert "mcp_tool_duration_seconds" in body
    assert 'tool="list_tables"' in body
