import logging

from app.config import get_settings
from app.server import mcp


def main() -> None:
    settings = get_settings()

    logging.basicConfig(level=settings.log_level)

    mcp.run(
        transport="http",
        host=settings.host,
        port=settings.port,
    )


if __name__ == "__main__":
    main()
