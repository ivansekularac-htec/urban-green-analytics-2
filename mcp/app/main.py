from fastmcp import FastMCP
from starlette.responses import JSONResponse

from app.config import get_settings

mcp = FastMCP("Urbangreen Analytics MCP Server")


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):
    return JSONResponse({"status": "healthy", "service": "urbangreen-mcp-server"})


def main():
    settings = get_settings()

    mcp.run(
        transport="http",
        host=settings.mcp_host,
        port=settings.mcp_port,
    )


if __name__ == "__main__":
    main()
