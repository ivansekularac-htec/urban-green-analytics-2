"""Tests for the Urban Green MCP server."""

from app.server import mcp


def test_mcp_server_exists() -> None:
    """Verify that the MCP server is initialized successfully."""
    assert mcp is not None
