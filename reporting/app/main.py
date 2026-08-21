"""The reporting service entry point.

POST /reports/{day} runs the pipeline for one day. The day is a date, or
"latest" for the newest day loaded in the warehouse. The same run is available
from the command line with --date, so the pipeline does not need a scheduler.
"""

import argparse
import logging
from datetime import date

import uvicorn
from fastapi import FastAPI, HTTPException

from app import graph, metrics
from app.config import get_settings

logger = logging.getLogger(__name__)


def resolve_day(value: str) -> date:
    """Turn a requested day into a date."""

    if value == "latest":
        day = metrics.latest_date(metrics.get_client())

        if day is None:
            raise ValueError("the warehouse has no loaded days")

        return day

    return date.fromisoformat(value)


def run_report(value: str) -> dict:
    """Run the pipeline for a requested day and describe what was published."""

    day = resolve_day(value)
    state = graph.run(day)
    published = state["published"]

    return {
        "day": day.isoformat(),
        "key": published["key"],
        "stored": published["stored"],
        "emailed": published["emailed"],
        "summary_source": state["summary"]["source"],
        "warnings": published["warnings"],
    }


def create_app() -> FastAPI:
    """Build the FastAPI application."""

    app = FastAPI(title="UrbanGreen Reporting", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "healthy"}

    @app.post("/reports/{day}")
    def create_report(day: str) -> dict:
        try:
            return run_report(day)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return app


app = create_app()


def main() -> None:
    settings = get_settings()

    logging.basicConfig(level=settings.log_level)

    parser = argparse.ArgumentParser(description="UrbanGreen reporting service")
    parser.add_argument(
        "--date",
        help="run the pipeline once for this day (YYYY-MM-DD or 'latest') and exit",
    )
    arguments = parser.parse_args()

    if arguments.date:
        print(run_report(arguments.date)["key"])
        return

    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
