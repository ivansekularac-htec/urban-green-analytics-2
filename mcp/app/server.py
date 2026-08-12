from fastmcp import FastMCP
from fastmcp.server.lifespan import lifespan
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.clickhouse import close_clickhouse_client


@lifespan
async def app_lifespan(_server):
    try:
        yield
    finally:
        close_clickhouse_client()


mcp = FastMCP(
    "UrbanGreen MCP",
    lifespan=app_lifespan,
)


@mcp.custom_route("/health", methods=["GET"])
async def health_check(_request: Request) -> JSONResponse:
    return JSONResponse({"status": "healthy"})
