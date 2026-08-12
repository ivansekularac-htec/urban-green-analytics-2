from app.config import get_settings
from app.server import mcp


def main() -> None:
    settings = get_settings()

    mcp.run(
        transport="http",
        host=settings.mcp_host,
        port=settings.mcp_port,
    )


if __name__ == "__main__":
    main()
