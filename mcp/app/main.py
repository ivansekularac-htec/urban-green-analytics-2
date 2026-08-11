from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.config import get_settings

mcp = FastMCP("Urban Green Analytics")


@mcp.custom_route("/health", methods=["GET"], include_in_schema=False)
async def health_check(_request: Request) -> Response:
    """Return the MCP service health status."""
    return JSONResponse({"status": "ok"})


def main() -> None:
    """Start the MCP server using environment-based settings."""
    settings = get_settings()
    mcp.run(
        transport="streamable-http",
        host=settings.host,
        port=settings.port,
    )


if __name__ == "__main__":
    main()
