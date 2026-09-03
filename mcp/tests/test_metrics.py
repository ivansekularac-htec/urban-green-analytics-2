import asyncio
import inspect
from unittest.mock import MagicMock

import httpx
import pytest
from prometheus_client import generate_latest

from app.metrics import reset_metrics, track_tool
from app.server import create_server


@pytest.fixture(autouse=True)
def _reset_registries():
    reset_metrics()
    yield
    reset_metrics()


def _body() -> str:
    return generate_latest().decode()


def test_ok_outcome_on_normal_return():
    @track_tool("demo")
    def demo() -> dict:
        return {"tables": []}

    assert demo() == {"tables": []}
    body = _body()
    assert 'mcp_tool_calls_total{outcome="ok",tool="demo"} 1.0' in body
    assert "mcp_tool_duration_seconds" in body


def test_ok_outcome_on_async_return():
    @track_tool("async_demo")
    async def async_demo() -> dict:
        return {"tables": []}

    result = asyncio.run(async_demo())

    assert result == {"tables": []}
    assert 'mcp_tool_calls_total{outcome="ok",tool="async_demo"} 1.0' in _body()


def test_error_outcome_on_error_dict():
    @track_tool("demo")
    def demo() -> dict:
        return {"error": "Database 'system' is not allowed."}

    assert "error" in demo()
    body = _body()
    assert 'mcp_tool_calls_total{outcome="error",tool="demo"} 1.0' in body
    assert 'outcome="ok"' not in body


def test_error_outcome_on_raise_and_exception_propagates():
    @track_tool("demo")
    def demo() -> dict:
        raise ValueError("boom")

    with pytest.raises(ValueError, match="boom"):
        demo()

    body = _body()
    assert 'mcp_tool_calls_total{outcome="error",tool="demo"} 1.0' in body


def test_decorator_preserves_tool_signature():
    def sample_tool(table: str, database: str = "urbangreen_dw") -> dict:
        return {}

    wrapped = track_tool("sample_tool")(sample_tool)

    assert inspect.signature(wrapped) == inspect.signature(sample_tool)
    assert wrapped.__name__ == sample_tool.__name__


def test_metrics_route_renders_metric_names():
    async def request():
        transport = httpx.ASGITransport(app=create_server(client=MagicMock()).http_app())
        async with httpx.AsyncClient(transport=transport, base_url="http://mcp") as http:
            return await http.get("/metrics")

    response = asyncio.run(request())

    assert response.status_code == 200
    assert "mcp_tool_calls_total" in response.text
    assert "mcp_tool_duration_seconds" in response.text
