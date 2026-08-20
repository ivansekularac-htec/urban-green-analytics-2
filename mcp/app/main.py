"""Application entry point for the UrbanGreen MCP server."""

import logging

from app.config import get_settings
from app.server import create_mcp_server

logger = logging.getLogger(__name__)


def main() -> None:
    """Build and run the UrbanGreen MCP server."""
    settings = get_settings()

    logging.basicConfig(level=settings.log_level)

    logger.info(f"Starting UrbanGreen MCP server on {settings.host}:{settings.port}")

    mcp = create_mcp_server()

    mcp.run(
        transport="http",
        host=settings.host,
        port=settings.port,
    )


if __name__ == "__main__":
    main()
