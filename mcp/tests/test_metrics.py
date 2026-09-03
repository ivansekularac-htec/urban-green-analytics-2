"""Tests for MCP Prometheus instrumentation."""

import asyncio
import inspect
from unittest.mock import MagicMock

import httpx
import pytest
from prometheus_client import REGISTRY

from app.metrics import TOOL_CALLS, TOOL_DURATION, track_tool
from app.server import create_server


@pytest.fixture(autouse=True)
def reset_tool_metrics():
    """Reset tool metric state around every test."""
    TOOL_CALLS.clear()
    TOOL_DURATION.clear()

    yield

    TOOL_CALLS.clear()
    TOOL_DURATION.clear()


def test_track_tool_records_ok_outcome():
    """Record a normal tool return as successful."""

    @track_tool("test_tool")
    def tool() -> dict[str, bool]:
        return {"success": True}

    result = tool()

    assert result == {"success": True}
    assert (
        REGISTRY.get_sample_value(
            "mcp_tool_calls_total",
            {"tool": "test_tool", "outcome": "ok"},
        )
        == 1.0
    )
    assert (
        REGISTRY.get_sample_value(
            "mcp_tool_duration_seconds_count",
            {"tool": "test_tool"},
        )
        == 1.0
    )


def test_track_tool_records_error_dict():
    """Record structured tool errors as failed calls."""

    @track_tool("test_tool")
    def tool() -> dict[str, object]:
        return {"error": "Query failed"}

    result = tool()

    assert result == {"error": "Query failed"}
    assert (
        REGISTRY.get_sample_value(
            "mcp_tool_calls_total",
            {"tool": "test_tool", "outcome": "error"},
        )
        == 1.0
    )


def test_track_tool_records_exception_and_reraises():
    """Record raised exceptions as errors without swallowing them."""

    @track_tool("test_tool")
    def tool() -> None:
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        tool()

    assert (
        REGISTRY.get_sample_value(
            "mcp_tool_calls_total",
            {"tool": "test_tool", "outcome": "error"},
        )
        == 1.0
    )
    assert (
        REGISTRY.get_sample_value(
            "mcp_tool_duration_seconds_count",
            {"tool": "test_tool"},
        )
        == 1.0
    )


def test_track_tool_preserves_signature():
    """Preserve the wrapped signature for FastMCP introspection."""

    def tool(sql: str, limit: int | None = None) -> dict:
        return {"sql": sql, "limit": limit}

    wrapped = track_tool("test_tool")(tool)

    assert inspect.signature(wrapped) == inspect.signature(tool)
    assert wrapped.__name__ == tool.__name__


def test_track_tool_supports_async_tools():
    """Track async MCP tools without changing their behavior."""

    @track_tool("async_tool")
    async def tool(resource: str) -> str:
        return resource

    result = asyncio.run(tool("metrics"))

    assert result == "metrics"
    assert (
        REGISTRY.get_sample_value(
            "mcp_tool_calls_total",
            {"tool": "async_tool", "outcome": "ok"},
        )
        == 1.0
    )


def test_metrics_route_exposes_prometheus_metrics():
    """Expose tool metrics through the FastMCP HTTP application."""

    async def request() -> httpx.Response:
        server = create_server(client=MagicMock())
        transport = httpx.ASGITransport(app=server.http_app())

        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://mcp",
        ) as client:
            return await client.get("/metrics")

    response = asyncio.run(request())

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "mcp_tool_calls_total" in response.text
    assert "mcp_tool_duration_seconds" in response.text
