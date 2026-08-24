"""The fixed executive KPIs, read from the pre-aggregated warehouse tables.

The model never picks a number. These queries produce every figure the report
shows; the model only writes prose around them. The formulas are the canonical
ones from the metric catalog - ratios divide with `nullIf`, the leaderboard is
read rather than rebuilt - so the report agrees with the dashboard.

Two rules the catalog makes that are easy to get wrong:

- **Active farms comes from `dim_farm`, not from counting fact rows.** A farm
  with no harvest and no readings on the date has no row in the daily fact
  table, but it is still an active farm. Counting fact rows would silently drop
  it from a headline labelled "active".
- **The leaderboard ranks and values are precomputed.** They are read straight
  from `fact_farm_leaderboard`, never re-derived.

Every table is a `ReplacingMergeTree`, so each read carries `FINAL` to collapse
any replayed load before it is aggregated.
"""

from __future__ import annotations

from typing import Any

from clickhouse_connect.driver.client import Client

# One row of headline totals for the date. The sums are aliased to names that do
# not match any base column, then the ratios are formed in the outer query where
# no aggregate remains - aliasing a SUM to the column name it sums makes
# ClickHouse resolve a later reference to that alias, producing SUM(SUM(...)) and
# an ILLEGAL_AGGREGATION error. The ratios follow the catalog; `nullIf` makes a
# zero denominator a NULL rather than a divide error.
_TOTALS_SQL = """
SELECT
    yield_kg                          AS total_yield_kg,
    energy_total                      AS total_energy_kwh,
    energy_total / nullIf(yield_kg, 0)    AS energy_efficiency_kwh_per_kg,
    non_premium_kg / nullIf(yield_kg, 0)  AS non_premium_share,
    in_range / nullIf(readings, 0)        AS compliance_rate,
    anomalies / nullIf(readings, 0)       AS anomaly_rate,
    harvest_ct                        AS harvests,
    readings                          AS sensor_readings,
    anomalies                         AS anomaly_count,
    farms                             AS farms_reporting
FROM (
    SELECT
        SUM(total_yield_kg)       AS yield_kg,
        SUM(energy_kwh)           AS energy_total,
        SUM(non_premium_yield_kg) AS non_premium_kg,
        SUM(harvest_count)        AS harvest_ct,
        SUM(in_range_count)       AS in_range,
        SUM(anomaly_count)        AS anomalies,
        SUM(reading_count)        AS readings,
        countDistinct(farm_id)    AS farms
    FROM urbangreen_dw.fact_daily_farm_metrics FINAL
    WHERE metric_date = {report_date:Date}
)
"""

# Per-sensor-type readings and anomalies for the day, joined to the current
# sensor-type dimension for the display name and unit. Aggregated in a subquery
# then joined, so the dimension is not re-aggregated.
_SENSORS_SQL = """
SELECT
    t.name  AS sensor_type,
    t.unit  AS unit,
    s.readings  AS readings,
    s.anomalies AS anomalies
FROM (
    SELECT
        sensor_type_id,
        SUM(reading_count) AS readings,
        SUM(anomaly_count) AS anomalies
    FROM urbangreen_dw.fact_daily_sensor_metrics FINAL
    WHERE metric_date = {report_date:Date}
    GROUP BY sensor_type_id
) AS s
INNER JOIN (
    SELECT sensor_type_id, name, unit
    FROM urbangreen_dw.dim_sensor_type AS d FINAL
    WHERE is_current = 1
) AS t ON t.sensor_type_id = s.sensor_type_id
ORDER BY t.name
"""

# "Active farms" is a property of the farm dimension, not of the day's activity.
# Read the current-version farm count so the headline says what it means.
_ACTIVE_FARMS_SQL = """
SELECT countDistinct(farm_id) AS active_farms
FROM urbangreen_dw.dim_farm FINAL
WHERE is_current = 1
"""

# The top farms for the day, read from the precomputed leaderboard and joined to
# the current farm dimension for display names. The ranks are read, never
# rebuilt. The alias goes before FINAL, which is the order ClickHouse parses.
_TOP_FARMS_SQL = """
SELECT
    l.composite_rank                    AS rank,
    f.name                              AS farm,
    f.city                              AS city,
    l.total_yield_kg                    AS total_yield_kg,
    l.premium_yield_share               AS premium_yield_share,
    l.energy_efficiency_kwh_per_kg      AS energy_efficiency_kwh_per_kg
FROM urbangreen_dw.fact_farm_leaderboard AS l FINAL
INNER JOIN (
    SELECT farm_id, name, city
    FROM urbangreen_dw.dim_farm AS d FINAL
    WHERE is_current = 1
) AS f ON f.farm_id = l.farm_id
WHERE l.metric_date = {report_date:Date}
ORDER BY l.composite_rank
LIMIT {top_n:UInt32}
"""

TOP_FARMS_DEFAULT = 5


def _one_row(client: Client, sql: str, parameters: dict) -> dict[str, Any]:
    """Run a query expected to return a single row and return it as a dict."""
    result = client.query(sql, parameters=parameters)

    if not result.result_rows:
        return {}

    return dict(zip(result.column_names, result.result_rows[0]))


def _rows(client: Client, sql: str, parameters: dict) -> list[dict[str, Any]]:
    """Run a query and return every row as a dict."""
    result = client.query(sql, parameters=parameters)

    return [dict(zip(result.column_names, row)) for row in result.result_rows]


def fetch_kpis(
    client: Client, report_date: str, top_n: int = TOP_FARMS_DEFAULT
) -> dict[str, Any]:
    """Read the executive KPIs for one date.

    Returns a dict with the headline totals, the active-farm count, and the top
    farms. `has_data` is False when the date has no rows in the daily fact
    table, which lets the caller report an empty day rather than a wrong one.
    """
    totals = _one_row(client, _TOTALS_SQL, {"report_date": report_date})
    active = _one_row(client, _ACTIVE_FARMS_SQL, {})
    top_farms = _rows(
        client, _TOP_FARMS_SQL, {"report_date": report_date, "top_n": top_n}
    )
    sensors = _rows(client, _SENSORS_SQL, {"report_date": report_date})

    has_data = bool(totals) and totals.get("total_yield_kg") is not None

    return {
        "report_date": report_date,
        "has_data": has_data,
        "totals": totals,
        "active_farms": active.get("active_farms"),
        "top_farms": top_farms,
        "sensors": sensors,
    }
