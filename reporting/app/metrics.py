"""Reads the executive KPIs for one day from the warehouse.

The queries are fixed: the model narrates these numbers, it does not choose
them. Tables are unqualified because the client is connected to the warehouse
database.
"""

from datetime import date
from decimal import Decimal
from functools import lru_cache

import clickhouse_connect
from clickhouse_connect.driver.client import Client

from app.config import get_settings

TOP_FARMS = 3

_LATEST_DATE = """
SELECT max(metric_date) AS latest
FROM fact_daily_farm_metrics
"""

# The alias goes before FINAL; ClickHouse rejects `table FINAL AS alias`.
_TOTALS = """
SELECT
    sum(d.total_yield_kg) AS yield_kg,
    sum(d.harvest_count) AS harvests,
    sum(d.energy_kwh) AS energy_kwh,
    sum(d.reading_count) AS readings,
    sum(d.anomaly_count) AS anomalies
FROM fact_daily_farm_metrics AS d FINAL
WHERE d.metric_date = {day:Date}
"""

# Counted from the dimension, not from the fact rollup: a farm that recorded
# neither a harvest nor a reading is still an active farm, and counting fact
# rows would quietly drop it from the headline.
#
# dim_farm is SCD-2 over the half-open interval [valid_from, valid_to), so this
# reads the state at the close of the report day rather than the state today.
# Using is_current would report today's farms on a report about a past date.
_ACTIVE_FARMS = """
SELECT count() AS farms
FROM dim_farm FINAL
WHERE status = 'ACTIVE'
    AND valid_from <= toDateTime64({day:Date}, 3) + toIntervalDay(1)
    AND valid_to > toDateTime64({day:Date}, 3) + toIntervalDay(1)
"""

_SENSORS = """
SELECT
    t.name AS sensor_type,
    t.unit AS unit,
    sum(s.reading_count) AS readings,
    sum(s.anomaly_count) AS anomalies
FROM fact_daily_sensor_metrics AS s FINAL
INNER JOIN (
    SELECT sensor_type_id, name, unit
    FROM dim_sensor_type FINAL
    WHERE is_current = 1
) AS t ON s.sensor_type_id = t.sensor_type_id
WHERE s.metric_date = {day:Date}
GROUP BY sensor_type, unit
ORDER BY sensor_type
"""

# The ranks are read, not recomputed: rebuilding them here would disagree with
# the dashboard for the same day.
_LEADERBOARD = f"""
SELECT
    f.name AS farm,
    b.total_yield_kg AS yield_kg,
    b.premium_yield_share AS premium_share,
    b.composite_rank AS rank
FROM fact_farm_leaderboard AS b FINAL
INNER JOIN (
    SELECT farm_id, name
    FROM dim_farm FINAL
    WHERE is_current = 1
) AS f ON b.farm_id = f.farm_id
WHERE b.metric_date = {{day:Date}}
ORDER BY b.composite_rank
LIMIT {TOP_FARMS}
"""


@lru_cache
def get_client() -> Client:
    """Return the shared read-only warehouse client."""

    settings = get_settings()

    return clickhouse_connect.get_client(
        host=settings.clickhouse_host,
        port=settings.clickhouse_port,
        username=settings.clickhouse_user,
        password=settings.clickhouse_password,
        database=settings.clickhouse_db,
        autogenerate_session_id=False,
        settings={"readonly": 1},
    )


def latest_date(client: Client) -> date | None:
    """Return the newest day loaded, or None when nothing is loaded."""

    rows = _rows(client.query(_LATEST_DATE))
    latest = rows[0]["latest"] if rows else None

    # max() over an empty table answers with the epoch, not with no row.
    return None if not latest or latest == date(1970, 1, 1) else latest


def collect(client: Client, day: date) -> dict:
    """Read every figure the report needs for one day."""

    totals = _rows(client.query(_TOTALS, parameters={"day": day}))[0]
    totals["farms"] = _rows(client.query(_ACTIVE_FARMS, parameters={"day": day}))[0]["farms"]

    # Ratios are derived here rather than in SQL: ClickHouse will not divide a
    # Decimal by a Float64, and a zero denominator means nothing was measured.
    totals["energy_per_kg"] = _ratio(totals["energy_kwh"], totals["yield_kg"])
    totals["anomaly_rate"] = _ratio(totals["anomalies"], totals["readings"])

    return {
        "day": day,
        "totals": totals,
        "sensors": _rows(client.query(_SENSORS, parameters={"day": day})),
        "leaderboard": _rows(client.query(_LEADERBOARD, parameters={"day": day})),
    }


def _ratio(numerator, denominator) -> float | None:
    """Divide, or return None when there is nothing to divide by."""

    return numerator / denominator if denominator else None


def _rows(result) -> list[dict]:
    """Return the result as dictionaries, with Decimals narrowed to floats."""

    return [
        {key: float(value) if isinstance(value, Decimal) else value for key, value in row.items()}
        for row in result.named_results()
    ]
