"""Executive KPI retrieval from ClickHouse."""

import logging
from datetime import date
from decimal import Decimal
from typing import Any

import clickhouse_connect
from airflow.sdk import get_current_context

from report.config import (
    clickhouse_database,
    clickhouse_host,
    clickhouse_password,
    clickhouse_port,
    clickhouse_user,
)
from report.state import ReportState

logger = logging.getLogger(__name__)

CLICKHOUSE_CONN_ID = "urbangreen_clickhouse"
TOP_FARMS_LIMIT = 5


_DAILY_METRICS_SQL = """
WITH
    farm_metrics AS
    (
        SELECT
            count() AS source_rows,
            uniqExact(farm_id) AS reporting_farms,
            sum(total_yield_kg) AS total_harvest_yield_kg,
            sum(energy_kwh) AS total_energy_kwh,
            sum(energy_kwh) / nullIf(sum(total_yield_kg), 0)
                AS energy_efficiency_kwh_per_kg,
            sum(non_premium_yield_kg) / nullIf(sum(total_yield_kg), 0)
                AS waste_reduction_progress,
            sum(in_range_count) / nullIf(sum(reading_count), 0)
                AS environmental_compliance_rate
        FROM urbangreen_dw.fact_daily_farm_metrics FINAL
        WHERE metric_date = {report_date:Date}
    ),
    sensor_metrics AS
    (
        SELECT
            sum(reading_count) AS total_sensor_readings,
            sum(anomaly_count) / nullIf(sum(reading_count), 0)
                AS sensor_anomaly_rate
        FROM urbangreen_dw.fact_daily_sensor_metrics FINAL
        WHERE metric_date = {report_date:Date}
    )
SELECT
    farm_metrics.source_rows,
    farm_metrics.reporting_farms,
    farm_metrics.total_harvest_yield_kg,
    farm_metrics.total_energy_kwh,
    farm_metrics.energy_efficiency_kwh_per_kg,
    farm_metrics.waste_reduction_progress,
    farm_metrics.environmental_compliance_rate,
    sensor_metrics.sensor_anomaly_rate,
    sensor_metrics.total_sensor_readings
FROM farm_metrics
CROSS JOIN sensor_metrics
"""


_TOP_FARMS_SQL = """
SELECT
    l.composite_rank AS rank,
    f.name AS farm,
    f.city AS city,
    l.total_yield_kg AS total_yield_kg,
    l.premium_yield_share AS premium_yield_share,
    l.energy_efficiency_kwh_per_kg
        AS energy_efficiency_kwh_per_kg
FROM
(
    SELECT
        farm_id,
        composite_rank,
        total_yield_kg,
        premium_yield_share,
        energy_efficiency_kwh_per_kg
    FROM urbangreen_dw.fact_farm_leaderboard FINAL
    WHERE metric_date = {report_date:Date}
) AS l
INNER JOIN
(
    SELECT
        farm_id,
        name,
        city
    FROM urbangreen_dw.dim_farm FINAL
    WHERE is_current = 1
) AS f
    ON f.farm_id = l.farm_id
ORDER BY
    l.composite_rank ASC,
    l.farm_id ASC
LIMIT {top_n:UInt32}
"""


_SENSORS_SQL = """
SELECT
    t.name AS sensor_type,
    t.unit AS unit,
    s.readings AS readings,
    s.anomalies AS anomalies,
    s.anomalies / nullIf(s.readings, 0)
        AS anomaly_rate,
    s.in_range_readings / nullIf(s.readings, 0)
        AS compliance_rate
FROM
(
    SELECT
        sensor_type_id,
        sum(reading_count) AS readings,
        sum(anomaly_count) AS anomalies,
        sum(in_range_count) AS in_range_readings
    FROM urbangreen_dw.fact_daily_sensor_metrics FINAL
    WHERE metric_date = {report_date:Date}
    GROUP BY sensor_type_id
) AS s
LEFT JOIN
(
    SELECT
        sensor_type_id,
        name,
        unit
    FROM urbangreen_dw.dim_sensor_type FINAL
) AS t
    ON t.sensor_type_id = s.sensor_type_id
ORDER BY t.name
"""


def _get_clickhouse_client():
    """Create a ClickHouse client for Airflow or standalone execution."""
    try:
        context = get_current_context()
    except RuntimeError:
        context = None

    if context:
        connection = context["conn"].get(CLICKHOUSE_CONN_ID)

        return clickhouse_connect.get_client(
            host=connection.host,
            port=connection.port or 8123,
            username=connection.login,
            password=connection.password,
            database=connection.schema or "urbangreen_dw",
        )

    return clickhouse_connect.get_client(
        host=clickhouse_host(),
        port=clickhouse_port(),
        username=clickhouse_user(),
        password=clickhouse_password(),
        database=clickhouse_database(),
    )


def _json_value(value: Any) -> Any:
    """Convert ClickHouse values to JSON-friendly Python values."""
    if isinstance(value, Decimal):
        return float(value)

    return value


def _rows_as_dicts(result) -> list[dict[str, Any]]:
    """Convert ClickHouse result rows to JSON-friendly dictionaries."""
    return [
        {
            column: _json_value(value)
            for column, value in zip(
                result.column_names,
                row,
                strict=True,
            )
        }
        for row in result.result_rows
    ]


def retrieve_metrics(
    state: ReportState,
) -> dict[str, Any]:
    """Load executive report data for the requested report date."""
    report_date = date.fromisoformat(state["report_date"])

    client = _get_clickhouse_client()

    try:
        metrics_result = client.query(
            _DAILY_METRICS_SQL,
            parameters={
                "report_date": report_date,
            },
        )

        if not metrics_result.result_rows or metrics_result.result_rows[0][0] == 0:
            raise ValueError(f"No daily farm metrics found for {report_date}.")

        top_farms_result = client.query(
            _TOP_FARMS_SQL,
            parameters={
                "report_date": report_date,
                "top_n": TOP_FARMS_LIMIT,
            },
        )

        sensors_result = client.query(
            _SENSORS_SQL,
            parameters={
                "report_date": report_date,
            },
        )

    finally:
        client.close()

    metrics_row = metrics_result.result_rows[0]

    metrics = {
        column: _json_value(value)
        for column, value in zip(
            metrics_result.column_names[1:],
            metrics_row[1:],
            strict=True,
        )
    }

    top_farms = _rows_as_dicts(top_farms_result)
    sensors = _rows_as_dicts(sensors_result)

    logger.info(
        f"Loaded executive report data for {report_date}: "
        f"{len(top_farms)} top farms and "
        f"{len(sensors)} sensor types."
    )

    return {
        "metrics": metrics,
        "top_farms": top_farms,
        "sensors": sensors,
    }
