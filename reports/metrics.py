"""Retrieve executive report data from the UrbanGreen warehouse."""

import logging
from datetime import date

import clickhouse_connect
from clickhouse_connect.driver.client import Client

from reports.config import get_clickhouse_settings
from reports.models import ExecutiveMetrics, ReportState, SensorMetric, TopFarm

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
LIMIT 5
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


SENSOR_METRICS_SQL = """
SELECT
    m.sensor_type_id,
    st.name AS sensor_name,
    st.unit,

    uniqExactIf(
        m.farm_id,
        m.reading_count > 0
    ) AS farms_reporting,

    uniqExactIf(
        m.farm_id,
        m.anomaly_count > 0
    ) AS farms_with_anomalies,

    toUInt64(sum(m.reading_count)) AS reading_count,

    toFloat64(sum(m.sum_value))
        / nullIf(toFloat64(sum(m.reading_count)), 0.0)
        AS average_value,

    minIf(
        m.min_value,
        m.reading_count > 0
    ) AS min_value,

    maxIf(
        m.max_value,
        m.reading_count > 0
    ) AS max_value,

    toUInt64(sum(m.anomaly_count)) AS anomaly_count,

    toFloat64(sum(m.anomaly_count))
        / nullIf(toFloat64(sum(m.reading_count)), 0.0)
        AS anomaly_rate,

    toUInt64(sum(m.in_range_count)) AS in_range_count,

    toFloat64(sum(m.in_range_count))
        / nullIf(toFloat64(sum(m.reading_count)), 0.0)
        AS in_range_rate

FROM fact_daily_sensor_metrics AS m FINAL

INNER JOIN
(
    SELECT
        sensor_type_id,
        name,
        unit
    FROM dim_sensor_type FINAL
    WHERE is_current = 1
) AS st
    ON st.sensor_type_id = m.sensor_type_id

WHERE m.metric_date = {report_date:Date}

GROUP BY
    m.sensor_type_id,
    st.name,
    st.unit

HAVING reading_count > 0

ORDER BY
    anomaly_rate DESC,
    sensor_name
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


def _optional_float(value: object) -> float | None:
    """Convert a nullable warehouse value to float."""
    return float(value) if value is not None else None


def retrieve_metrics(state: ReportState) -> dict[str, object]:
    """Retrieve executive, leaderboard, and sensor metrics for one date."""
    report_date = date.fromisoformat(state["report_date"])

    logger.info(f"Retrieving executive report data for {report_date}")

    client = _get_clickhouse_client()

    try:
        parameters = {"report_date": report_date}

        kpi_result = client.query(
            EXECUTIVE_KPI_SQL,
            parameters=parameters,
        )

        top_farms_result = client.query(
            TOP_FARMS_SQL,
            parameters=parameters,
        )

        top_rank_result = client.query(
            TOP_RANK_SQL,
            parameters=parameters,
        )

        sensor_result = client.query(
            SENSOR_METRICS_SQL,
            parameters=parameters,
        )

        top_farm_rows = list(top_farms_result.named_results())
        top_rank_rows = list(top_rank_result.named_results())
        sensor_rows = list(sensor_result.named_results())

    finally:
        client.close()

    if not kpi_result.result_rows:
        raise RuntimeError(f"ClickHouse returned no KPI result for {report_date}")

    values = dict(
        zip(
            kpi_result.column_names,
            kpi_result.result_rows[0],
            strict=True,
        )
    )

    if int(values["source_row_count"]) == 0:
        raise ValueError(f"No daily farm metrics found for {report_date}")

    metrics: ExecutiveMetrics = {
        "farms_reporting": int(values["farms_reporting"]),
        "total_yield_kg": float(values["total_yield_kg"]),
        "harvest_count": int(values["harvest_count"]),
        "premium_yield_kg": float(values["premium_yield_kg"]),
        "premium_yield_share": _optional_float(values["premium_yield_share"]),
        "energy_kwh": float(values["energy_kwh"]),
        "energy_efficiency_kwh_per_kg": _optional_float(
            values["energy_efficiency_kwh_per_kg"]
        ),
        "reading_count": int(values["reading_count"]),
        "anomaly_count": int(values["anomaly_count"]),
        "sensor_anomaly_rate": _optional_float(values["sensor_anomaly_rate"]),
    }

    top_farms: list[TopFarm] = [
        {
            "rank": int(row["rank"]),
            "farm_name": str(row["farm_name"]),
            "total_yield_kg": float(row["total_yield_kg"]),
            "premium_yield_share": _optional_float(row["premium_yield_share"]),
            "energy_efficiency_kwh_per_kg": _optional_float(
                row["energy_efficiency_kwh_per_kg"]
            ),
            "composite_score": float(row["composite_score"]),
        }
        for row in top_farm_rows
    ]

    sensor_metrics: list[SensorMetric] = [
        {
            "sensor_type_id": int(row["sensor_type_id"]),
            "sensor_name": str(row["sensor_name"]),
            "unit": str(row["unit"] or ""),
            "farms_reporting": int(row["farms_reporting"]),
            "farms_with_anomalies": int(row["farms_with_anomalies"]),
            "reading_count": int(row["reading_count"]),
            "average_value": _optional_float(row["average_value"]),
            "min_value": _optional_float(row["min_value"]),
            "max_value": _optional_float(row["max_value"]),
            "anomaly_count": int(row["anomaly_count"]),
            "anomaly_rate": _optional_float(row["anomaly_rate"]),
            "in_range_count": int(row["in_range_count"]),
            "in_range_rate": _optional_float(row["in_range_rate"]),
        }
        for row in sensor_rows
    ]

    if top_rank_rows:
        top_rank = int(top_rank_rows[0]["top_rank"])
        top_rank_count = int(top_rank_rows[0]["top_rank_count"])
    else:
        top_rank = None
        top_rank_count = 0

    logger.info(
        f"Retrieved executive report data for {report_date}: "
        f"{len(top_farms)} displayed farms, "
        f"{top_rank_count} farms at top rank, "
        f"{len(sensor_metrics)} sensor types"
    )

    return {
        "metrics": metrics,
        "top_farms": top_farms,
        "top_rank": top_rank,
        "top_rank_count": top_rank_count,
        "sensor_metrics": sensor_metrics,
    }
