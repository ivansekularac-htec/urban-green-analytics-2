"""
main.py
Entry point for the Urban Green MCP server.

Starts FastMCP over the streamable-HTTP transport. stdio is not an option
here: LM Studio runs on the host while this server runs inside a container,
and stdio cannot cross that boundary.
"""

import logging

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import PlainTextResponse

from app.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("urbangreen-mcp")


@mcp.custom_route("/health", methods=["GET"])
async def health(_request: Request) -> PlainTextResponse:
    """Plain endpoint for the compose healthcheck to poll."""

    return PlainTextResponse("ok")


def main() -> None:
    """Start the MCP server using host and port from settings."""

    settings = get_settings()

    logger.info("Starting MCP server on %s:%s", settings.mcp_host, settings.mcp_port)

    # "http" is what the standalone FastMCP package calls the streamable-HTTP
    # transport; "streamable-http" is the older name from the in-SDK module.
    mcp.run(
        transport="http",
        host=settings.mcp_host,
        port=settings.mcp_port,
    )


if __name__ == "__main__":
    main()
