"""The reporting pipeline entry point.

run_report() builds and publishes the report for one day. The day is a date, or
"latest" for the newest day loaded in the warehouse. The Airflow DAG imports
this function and calls it in process; --date runs the same pipeline from the
command line, so the pipeline can be run without a scheduler.
"""

import argparse
import logging
from datetime import date

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


def main() -> None:
    settings = get_settings()

    logging.basicConfig(level=settings.log_level)

    parser = argparse.ArgumentParser(description="UrbanGreen reporting pipeline")
    parser.add_argument(
        "--date",
        default="latest",
        help="the day to report on (YYYY-MM-DD, or 'latest' for the newest loaded day)",
    )
    arguments = parser.parse_args()

    print(run_report(arguments.date)["key"])


if __name__ == "__main__":
    main()
