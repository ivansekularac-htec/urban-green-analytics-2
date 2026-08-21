"""Retrieve executive report data from the UrbanGreen warehouse."""

import logging
from datetime import date

import clickhouse_connect
from clickhouse_connect.driver.client import Client

from reports.config import get_clickhouse_settings
from reports.models import ExecutiveMetrics, ReportState, TopFarm

logger = logging.getLogger(__name__)


EXECUTIVE_KPI_SQL = """
SELECT
    source_row_count,
    farms_reporting,
    total_yield_kg,
    harvest_count,
    premium_yield_kg,
    premium_yield_kg / nullIf(total_yield_kg, 0.0) AS premium_yield_share,
    energy_kwh,
    energy_kwh / nullIf(total_yield_kg, 0.0) AS energy_efficiency_kwh_per_kg,
    reading_count,
    anomaly_count,
    anomaly_count / nullIf(reading_count, 0) AS sensor_anomaly_rate
FROM
(
    SELECT
        count() AS source_row_count,
        uniqExact(farm_id) AS farms_reporting,
        toFloat64(sum(total_yield_kg)) AS total_yield_kg,
        toUInt64(sum(harvest_count)) AS harvest_count,
        toFloat64(sum(premium_yield_kg)) AS premium_yield_kg,
        toFloat64(sum(energy_kwh)) AS energy_kwh,
        toUInt64(sum(reading_count)) AS reading_count,
        toUInt64(sum(anomaly_count)) AS anomaly_count
    FROM fact_daily_farm_metrics FINAL
    WHERE metric_date = {report_date:Date}
)
""".strip()


TOP_FARMS_SQL = """
SELECT
    l.composite_rank AS rank,
    f.name AS farm_name,
    l.total_yield_kg,
    l.premium_yield_share,
    l.energy_efficiency_kwh_per_kg,
    l.composite_score
FROM fact_farm_leaderboard AS l FINAL
INNER JOIN
(
    SELECT farm_id, name
    FROM dim_farm FINAL
    WHERE is_current = 1
) AS f ON f.farm_id = l.farm_id
WHERE l.metric_date = {report_date:Date}
ORDER BY
    l.composite_rank,
    l.composite_score DESC,
    l.total_yield_kg DESC,
    l.farm_id
LIMIT 3
""".strip()


TOP_RANK_SQL = """
SELECT
    composite_rank AS top_rank,
    count() AS top_rank_count
FROM fact_farm_leaderboard FINAL
WHERE metric_date = {report_date:Date}
GROUP BY composite_rank
ORDER BY composite_rank
LIMIT 1
""".strip()


def _get_clickhouse_client() -> Client:
    """Create the ClickHouse client used for report data retrieval."""
    settings = get_clickhouse_settings()
    return clickhouse_connect.get_client(
        host=settings.host,
        port=settings.port,
        database=settings.database,
        username=settings.user,
        password=settings.password,
    )


def retrieve_metrics(state: ReportState) -> dict[str, object]:
    """Retrieve executive KPIs and leaderboard data for the report date."""
    report_date = date.fromisoformat(state["report_date"])
    logger.info(f"Retrieving executive report data for {report_date}")

    client = _get_clickhouse_client()
    try:
        kpi_result = client.query(
            EXECUTIVE_KPI_SQL,
            parameters={"report_date": report_date},
        )
        top_farms_result = client.query(
            TOP_FARMS_SQL,
            parameters={"report_date": report_date},
        )
        top_rank_result = client.query(
            TOP_RANK_SQL,
            parameters={"report_date": report_date},
        )
        top_farm_rows = list(top_farms_result.named_results())
        top_rank_rows = list(top_rank_result.named_results())
    finally:
        client.close()

    if not kpi_result.result_rows:
        raise RuntimeError(f"ClickHouse returned no KPI result for {report_date}")

    values = dict(zip(kpi_result.column_names, kpi_result.result_rows[0], strict=True))

    # Aggregate SELECT returns one row even when the source set is empty.
    if int(values["source_row_count"]) == 0:
        raise ValueError(f"No daily farm metrics found for {report_date}")

    metrics: ExecutiveMetrics = {
        "farms_reporting": int(values["farms_reporting"]),
        "total_yield_kg": float(values["total_yield_kg"]),
        "harvest_count": int(values["harvest_count"]),
        "premium_yield_kg": float(values["premium_yield_kg"]),
        "premium_yield_share": (
            float(values["premium_yield_share"])
            if values["premium_yield_share"] is not None
            else None
        ),
        "energy_kwh": float(values["energy_kwh"]),
        "energy_efficiency_kwh_per_kg": (
            float(values["energy_efficiency_kwh_per_kg"])
            if values["energy_efficiency_kwh_per_kg"] is not None
            else None
        ),
        "reading_count": int(values["reading_count"]),
        "anomaly_count": int(values["anomaly_count"]),
        "sensor_anomaly_rate": (
            float(values["sensor_anomaly_rate"])
            if values["sensor_anomaly_rate"] is not None
            else None
        ),
    }

    top_farms: list[TopFarm] = [
        {
            "rank": int(row["rank"]),
            "farm_name": str(row["farm_name"]),
            "total_yield_kg": float(row["total_yield_kg"]),
            "premium_yield_share": (
                float(row["premium_yield_share"])
                if row["premium_yield_share"] is not None
                else None
            ),
            "energy_efficiency_kwh_per_kg": (
                float(row["energy_efficiency_kwh_per_kg"])
                if row["energy_efficiency_kwh_per_kg"] is not None
                else None
            ),
            "composite_score": float(row["composite_score"]),
        }
        for row in top_farm_rows
    ]

    if top_rank_rows:
        top_rank = int(top_rank_rows[0]["top_rank"])
        top_rank_count = int(top_rank_rows[0]["top_rank_count"])
    else:
        top_rank = None
        top_rank_count = 0

    logger.info(
        f"Retrieved executive report data for {report_date}: "
        f"{len(top_farms)} displayed farms, {top_rank_count} farms at top rank"
    )

    return {
        "metrics": metrics,
        "top_farms": top_farms,
        "top_rank": top_rank,
        "top_rank_count": top_rank_count,
    }
