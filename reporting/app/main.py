"""The reporting service entry point.

The application is built by a factory rather than at import time, so importing
this module - which the tests do - neither opens a warehouse connection nor
needs one. Later steps register the report routes on the app the factory
returns; for now it carries the liveness route compose polls.
"""

import logging

import uvicorn
from fastapi import FastAPI

from app.config import get_settings


def create_app() -> FastAPI:
    """Build the FastAPI application with every route registered."""

    app = FastAPI(
        title="UrbanGreen Reporting",
        description="Automated executive reporting for the UrbanGreen Analytics platform.",
        version="0.1.0",
    )

    # Liveness only, and deliberately not a warehouse or model ping: compose
    # already holds this service back until its dependencies are healthy, and a
    # restart would not fix one that went away afterwards.
    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "healthy"}

    return app


app = create_app()


def main() -> None:
    settings = get_settings()

    logging.basicConfig(level=settings.log_level)

    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
