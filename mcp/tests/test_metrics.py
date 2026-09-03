"""Unit tests for MCP tool-call Prometheus instrumentation."""

import asyncio
import inspect

import pytest
from prometheus_client import REGISTRY

from app.metrics import track_tool


def metric_value(name: str, labels: dict[str, str]) -> float | None:
    """Read one labelled sample from the default Prometheus registry."""

    return REGISTRY.get_sample_value(name, labels)


def test_track_tool_records_a_normal_return_as_ok():
    @track_tool("successful_tool")
    def successful_tool() -> dict[str, bool]:
        return {"success": True}

    result = successful_tool()

    assert result == {"success": True}
    assert (
        metric_value(
            "mcp_tool_calls_total",
            {"tool": "successful_tool", "outcome": "ok"},
        )
        == 1
    )
    assert (
        metric_value(
            "mcp_tool_duration_seconds_count",
            {"tool": "successful_tool"},
        )
        == 1
    )


def test_track_tool_records_an_error_dict_as_error():
    @track_tool("structured_error_tool")
    def structured_error_tool() -> dict[str, str]:
        return {"error": "warehouse unavailable"}

    result = structured_error_tool()

    assert result == {"error": "warehouse unavailable"}
    assert (
        metric_value(
            "mcp_tool_calls_total",
            {"tool": "structured_error_tool", "outcome": "error"},
        )
        == 1
    )
    assert (
        metric_value(
            "mcp_tool_calls_total",
            {"tool": "structured_error_tool", "outcome": "ok"},
        )
        is None
    )


def test_track_tool_records_and_propagates_a_raised_exception():
    @track_tool("failing_tool")
    def failing_tool() -> None:
        raise RuntimeError("warehouse connection failed")

    with pytest.raises(RuntimeError, match="warehouse connection failed"):
        failing_tool()

    assert (
        metric_value(
            "mcp_tool_calls_total",
            {"tool": "failing_tool", "outcome": "error"},
        )
        == 1
    )
    assert (
        metric_value(
            "mcp_tool_duration_seconds_count",
            {"tool": "failing_tool"},
        )
        == 1
    )


def test_track_tool_awaits_and_records_async_tools():
    @track_tool("async_tool")
    async def async_tool() -> str:
        await asyncio.sleep(0)
        return "done"

    result = asyncio.run(async_tool())

    assert result == "done"
    assert (
        metric_value(
            "mcp_tool_calls_total",
            {"tool": "async_tool", "outcome": "ok"},
        )
        == 1
    )
    assert (
        metric_value(
            "mcp_tool_duration_seconds_count",
            {"tool": "async_tool"},
        )
        == 1
    )


def test_track_tool_preserves_the_wrapped_signature():
    def original(value: str, limit: int | None = None) -> dict[str, object]:
        return {"value": value, "limit": limit}

    wrapped = track_tool("signature_tool")(original)

    assert wrapped.__name__ == original.__name__
    assert wrapped.__doc__ == original.__doc__
    assert inspect.signature(wrapped) == inspect.signature(original)
