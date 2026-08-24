"""First node: read the day's KPIs from the warehouse."""

from __future__ import annotations

import logging
from collections.abc import Callable

from report.deps import ReportDeps
from report.metrics import fetch_kpis
from report.state import ReportState

logger = logging.getLogger(__name__)


def make_retrieve(deps: ReportDeps) -> Callable[[ReportState], dict]:
    """Build the retrieval node against a warehouse client."""

    def retrieve(state: ReportState) -> dict:
        report_date = state["report_date"]
        kpis = fetch_kpis(deps.warehouse, report_date)

        if not kpis["has_data"]:
            # An empty day is a real outcome, not an error: the report still
            # renders and says so, rather than reporting figures from nothing.
            logger.warning(
                f"no daily metrics loaded for {report_date}; report will note the gap"
            )
        else:
            logger.info(
                f"read KPIs for {report_date}: {kpis['active_farms']} active farms"
            )

        return {"kpis": kpis, "has_data": kpis["has_data"]}

    return retrieve
