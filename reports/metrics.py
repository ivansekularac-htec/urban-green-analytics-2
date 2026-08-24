"""Retrieve the fixed executive KPI set from ClickHouse."""

import logging
from decimal import Decimal

import clickhouse_connect
from clickhouse_connect.driver.client import Client

from reports.config import get_clickhouse_settings
from reports.models import ExecutiveMetrics, ReportState, TopFarm

logger = logging.getLogger(__name__)


EXECUTIVE_KPI_SQL = """
SELECT
    count() AS source_row_count,
    uniqExact(farm_id) AS farms_reporting,
    sum(total_yield_kg) AS total_yield_kg,
    sum(harvest_count) AS harvest_count,
    sum(premium_yield_kg) AS premium_yield_kg,
    sum(energy_kwh) AS energy_kwh,
    sum(reading_count) AS reading_count,
    sum(anomaly_count) AS anomaly_count
FROM fact_daily_farm_metrics FINAL
WHERE metric_date = {report_date:Date}
""".strip()


TOP_FARMS_SQL = """
SELECT
    leaderboard.composite_rank AS rank,
    farm.name AS farm_name,
    leaderboard.total_yield_kg,
    leaderboard.premium_yield_share,
    leaderboard.energy_efficiency_kwh_per_kg,
    leaderboard.composite_score
FROM fact_farm_leaderboard AS leaderboard FINAL
INNER JOIN dim_farm AS farm FINAL
    ON farm.farm_key = leaderboard.farm_key
WHERE leaderboard.metric_date = {report_date:Date}
ORDER BY
    leaderboard.composite_rank,
    leaderboard.composite_score DESC,
    leaderboard.farm_id
LIMIT 3
""".strip()


def get_client() -> Client:
    """Create a read-only ClickHouse client for one retrieval stage."""

    settings = get_clickhouse_settings()
    return clickhouse_connect.get_client(
        host=settings.host,
        port=settings.port,
        database=settings.database,
        username=settings.user,
        password=settings.password,
        autogenerate_session_id=False,
        settings={"readonly": 1},
    )


def _number(value: object) -> float:
    """Normalize ClickHouse numeric values for graph serialization."""

    if isinstance(value, (int, float, Decimal)):
        return float(value)
    raise TypeError(f"Expected a numeric warehouse value, got {type(value).__name__}")


def _optional_number(value: object | None) -> float | None:
    """Normalize a nullable ClickHouse numeric value."""

    return None if value is None else _number(value)


def _ratio(numerator: float | int, denominator: float | int) -> float | None:
    """Return a ratio, or None when its denominator is zero."""

    return float(numerator) / float(denominator) if denominator else None


def _rows(result: object) -> list[dict[str, object]]:
    """Return a ClickHouse query result as dictionaries."""

    return list(result.named_results())  # type: ignore[attr-defined]


def retrieve_metrics(state: ReportState) -> dict[str, object]:
    """Read aggregate KPIs and the precomputed top-three leaderboard."""

    report_date = state["report_date"]
    logger.info("Retrieving executive KPIs for %s", report_date)

    client = get_client()
    try:
        kpi_rows = _rows(
            client.query(
                EXECUTIVE_KPI_SQL,
                parameters={"report_date": report_date},
            )
        )
        top_farm_rows = _rows(
            client.query(
                TOP_FARMS_SQL,
                parameters={"report_date": report_date},
            )
        )
    finally:
        client.close()

    if not kpi_rows or int(kpi_rows[0]["source_row_count"]) == 0:
        raise ValueError(f"No executive metrics found for {report_date}")

    row = kpi_rows[0]
    total_yield_kg = _number(row["total_yield_kg"])
    premium_yield_kg = _number(row["premium_yield_kg"])
    energy_kwh = _number(row["energy_kwh"])
    reading_count = int(row["reading_count"])
    anomaly_count = int(row["anomaly_count"])

    metrics: ExecutiveMetrics = {
        "farms_reporting": int(row["farms_reporting"]),
        "total_yield_kg": total_yield_kg,
        "harvest_count": int(row["harvest_count"]),
        "premium_yield_kg": premium_yield_kg,
        "premium_yield_share": _ratio(premium_yield_kg, total_yield_kg),
        "energy_kwh": energy_kwh,
        "energy_efficiency_kwh_per_kg": _ratio(energy_kwh, total_yield_kg),
        "reading_count": reading_count,
        "anomaly_count": anomaly_count,
        "anomaly_rate": _ratio(anomaly_count, reading_count),
    }

    top_farms: list[TopFarm] = [
        {
            "rank": int(farm["rank"]),
            "farm_name": str(farm["farm_name"]),
            "total_yield_kg": _number(farm["total_yield_kg"]),
            "premium_yield_share": _optional_number(farm["premium_yield_share"]),
            "energy_efficiency_kwh_per_kg": _optional_number(farm["energy_efficiency_kwh_per_kg"]),
            "composite_score": _number(farm["composite_score"]),
        }
        for farm in top_farm_rows
    ]

    logger.info(
        "Retrieved KPIs for %s: %d reporting farms and %d leaderboard entries",
        report_date,
        metrics["farms_reporting"],
        len(top_farms),
    )
    return {"metrics": metrics, "top_farms": top_farms}
