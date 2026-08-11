"""FastMCP server entry point for the Urban Green MCP service."""

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import get_settings

mcp = FastMCP("Urban Green MCP")


@mcp.custom_route("/health", methods=["GET"])
async def health_check(_request: Request) -> JSONResponse:
    """Return the health status of the MCP service."""
    return JSONResponse({"status": "healthy"})


def main() -> None:
    """Start the MCP server using the configured HTTP host and port."""
    settings = get_settings()

    mcp.run(
        transport="http",
        host=settings.mcp_host,
        port=settings.mcp_port,
    )


if __name__ == "__main__":
    main()
