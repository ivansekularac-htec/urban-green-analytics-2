"""Shared pytest fixtures for the MCP test suite."""

import pytest

from app.metrics import TOOL_CALLS, TOOL_DURATION


@pytest.fixture(autouse=True)
def _reset_tool_metrics():
    """Clear tool-call metrics before and after every test.

    TOOL_CALLS and TOOL_DURATION are module-level, registered once on the
    default global registry at import time. Without this, a count recorded
    by one test would still be there when the next test asserts on it.
    """

    TOOL_CALLS.clear()
    TOOL_DURATION.clear()
    yield
    TOOL_CALLS.clear()
    TOOL_DURATION.clear()
