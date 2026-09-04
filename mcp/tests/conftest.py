"""Shared fixtures for isolated MCP tests."""

import pytest

from app.metrics import TOOL_CALLS, TOOL_DURATION


@pytest.fixture(autouse=True)
def reset_prometheus_metrics():
    """Prevent one test's labelled metric values leaking into another."""

    TOOL_CALLS.clear()
    TOOL_DURATION.clear()

    yield

    TOOL_CALLS.clear()
    TOOL_DURATION.clear()
