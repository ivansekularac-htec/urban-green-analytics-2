"""Start the Urban Green MCP server over HTTP for Docker clients."""

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import PlainTextResponse

from app.config import get_settings

mcp = FastMCP("urbangreen-mcp")


@mcp.custom_route("/health", methods=["GET"])
async def health(_request: Request) -> PlainTextResponse:
    return PlainTextResponse("ok")


def main() -> None:
    settings = get_settings()
    mcp.run(
        transport="streamable-http",
        host=settings.mcp_host,
        port=settings.mcp_port,
    )


if __name__ == "__main__":
    main()
