"""Run the report pipeline for one date, outside Airflow.

This is the standalone entry point the ticket asks for: it builds the
dependencies from the environment and runs the same graph the DAG runs. A date
may be passed as the single argument; without one it defaults to yesterday
(UTC).

    python -m report.run 2026-08-15
"""

from __future__ import annotations

import argparse
import logging
from datetime import datetime, timedelta, timezone

from report.deps import from_env
from report.graph import run_report

logger = logging.getLogger(__name__)


def _yesterday_utc() -> str:
    return (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build the daily executive report for a date."
    )
    parser.add_argument(
        "report_date",
        nargs="?",
        default=_yesterday_utc(),
        help="Report date as YYYY-MM-DD (default: yesterday, UTC).",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s"
    )

    result = run_report(from_env(), args.report_date)

    logger.info(
        f"report for {args.report_date}: key={result.get('object_key')} "
        f"summary={result.get('summary_source')} email_sent={result.get('email_sent')}"
    )


if __name__ == "__main__":
    main()
