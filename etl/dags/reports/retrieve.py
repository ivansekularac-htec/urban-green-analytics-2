"""Pull the day's executive KPIs from pre-aggregated warehouse tables."""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

import clickhouse_connect
from airflow.sdk.bases.hook import BaseHook

from reports.state import CLICKHOUSE_CONN_ID, ReportState

logger = logging.getLogger(__name__)

_EMPTY_DAY_METRICS = (
    "total_yield_kg",
    "energy_kwh",
    "energy_efficiency_kwh_per_kg",
    "yield_efficiency_kg_per_m2",
    "waste_reduction_progress",
    "compliance_rate",
    "anomaly_rate",
)


def _jsonable(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def _row_dict(result) -> dict[str, Any]:
    if not result.result_rows:
        return {}
    return dict(zip(result.column_names, result.result_rows[0]))


def _clickhouse():
    conn = BaseHook.get_connection(CLICKHOUSE_CONN_ID)
    return clickhouse_connect.get_client(
        host=conn.host,
        port=conn.port or 8123,
        username=conn.login,
        password=conn.password,
        database=conn.schema or "urbangreen_dw",
    )


def retrieve_metrics(state: ReportState) -> dict:
    """Read the executive KPI snapshot for one day from pre-aggregated tables."""
    report_date = state["report_date"]
    client = _clickhouse()
    params = {"report_date": report_date}

    try:
        snapshot = client.query(
            """
            SELECT
                uniqExact(m.farm_id) AS farms_with_activity,
                sum(m.total_yield_kg) AS total_yield_kg,
                sum(m.energy_kwh) AS energy_kwh,
                sum(m.energy_kwh) / nullIf(sum(m.total_yield_kg), 0)
                    AS energy_efficiency_kwh_per_kg,
                sum(m.total_yield_kg) / nullIf(sum(f.size_m2), 0)
                    AS yield_efficiency_kg_per_m2,
                sum(m.non_premium_yield_kg) / nullIf(sum(m.total_yield_kg), 0)
                    AS waste_reduction_progress,
                sum(m.in_range_count) / nullIf(sum(m.reading_count), 0)
                    AS compliance_rate,
                sum(m.anomaly_count) / nullIf(sum(m.reading_count), 0)
                    AS anomaly_rate
            FROM urbangreen_dw.fact_daily_farm_metrics AS m FINAL
            INNER JOIN urbangreen_dw.dim_farm AS f FINAL
                ON m.farm_id = f.farm_id AND f.is_current = 1
            WHERE m.metric_date = {report_date:Date}
            """,
            parameters=params,
        )
        expansion = client.query(
            """
            SELECT
                count() AS registered_farms,
                count() / 100.0 AS expansion_progress
            FROM urbangreen_dw.dim_farm FINAL
            WHERE is_current = 1
            """
        )
        leaders = client.query(
            """
            SELECT
                l.composite_rank,
                f.name AS farm_name,
                l.total_yield_kg
            FROM urbangreen_dw.fact_farm_leaderboard AS l FINAL
            INNER JOIN urbangreen_dw.dim_farm AS f FINAL
                ON l.farm_id = f.farm_id AND f.is_current = 1
            WHERE l.metric_date = {report_date:Date}
            ORDER BY l.composite_rank
            LIMIT 3
            """,
            parameters=params,
        )
    finally:
        client.close()

    row = {k: _jsonable(v) for k, v in _row_dict(snapshot).items()}
    exp = {k: _jsonable(v) for k, v in _row_dict(expansion).items()}
    kpis = {
        "report_date": report_date,
        **exp,
        **row,
        "top_farms": [
            {k: _jsonable(v) for k, v in zip(leaders.column_names, rec)}
            for rec in leaders.result_rows
        ],
    }

    if not kpis.get("farms_with_activity"):
        for name in _EMPTY_DAY_METRICS:
            kpis[name] = None

    logger.info(f"retrieved KPIs for {report_date}")
    return {"kpis": kpis}
