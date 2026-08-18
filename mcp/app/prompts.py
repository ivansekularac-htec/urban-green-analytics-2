"""
Reusable prompt templates for the UrbanGreen MCP service.

Guides metric analysis, farm comparison, and anomaly investigation.
"""

from __future__ import annotations

from textwrap import dedent


def analyze_metric(
    metric_name: str,
    window: str = "last 30 days",
) -> str:
    """Analyze a metric over a reporting window."""
    return dedent(
        f"""
        Analyze the UrbanGreen metric "{metric_name}" for {window}.

        Follow this workflow:

        1. Read `urbangreen://metrics` and use the canonical definition,
           unit, calculation, and source table or tables for the requested
           metric.
        2. Read `urbangreen://conventions` and apply the relevant ClickHouse
           rules, including `FINAL`, `argMax`, SCD2 handling, and fact
           deduplication.
        3. Call `describe_table` for every table required by the canonical
           metric definition before writing SQL.
        4. Build one ClickHouse query for the requested reporting window.
        5. Call `execute_query` exactly once.
        6. Report the result clearly, include its unit, and name the source
           table or tables used.

        Do not invent an alternative metric definition, formula, or source
        when `urbangreen://metrics` already defines one.
        """
    ).strip()


def compare_farms(
    farm_ids: str,
    dimension: str,
    window: str = "last 30 days",
) -> str:
    """Compare and rank farms by a selected metric."""
    return dedent(
        f"""
        Compare farms {farm_ids} by "{dimension}" for {window}.

        Follow this workflow:

        1. Read `urbangreen://metrics` and use the canonical definition,
           unit, calculation, and source for "{dimension}".
        2. Read `urbangreen://conventions` and apply the relevant ClickHouse
           rules.
        3. Resolve current farm names from `urbangreen_dw.dim_farm FINAL`
           with `is_current = 1`.
        4. Prefer the pre-aggregated or precomputed warehouse source
           identified by `urbangreen://metrics` when it can answer the
           request. Do not rebuild an available daily aggregate or
           leaderboard metric from atomic facts.
        5. Call `describe_table` for every table used before writing SQL.
        6. Call `execute_query` once for only the requested farms and
           reporting window.
        7. Return a small ranked table containing farm name, metric value,
           unit, and rank.

        After the table, identify the leader and the laggard and briefly
        describe the difference. Name the source table or tables used.
        """
    ).strip()


def investigate_anomaly(
    farm_id: int,
    sensor_type: str,
    since_window: str = "last 24 hours",
) -> str:
    """Investigate anomalous sensor readings for a farm."""
    return dedent(
        f"""
        Investigate sensor anomalies for farm {farm_id}, sensor type
        "{sensor_type}", during {since_window}.

        An anomaly is a sensor reading outside the configured minimum or
        maximum range for its sensor type in
        `urbangreen_dw.dim_sensor_type`. Do not hardcode threshold values.

        Follow this workflow:

        1. Read `urbangreen://metrics` for the canonical anomaly,
           compliance, and sensor metric definitions and their sources.
        2. Read `urbangreen://conventions` for the applicable ClickHouse
           and SCD2 rules.
        3. Call `describe_table` for `urbangreen_dw.dim_sensor_type` and
           every fact table required for the investigation.
        4. Use the current `urbangreen_dw.dim_sensor_type FINAL` row for
           the selected sensor type and use its configured minimum and
           maximum range.
        5. Prefer `urbangreen_dw.fact_daily_sensor_metrics` for trend,
           anomaly-rate, and aggregate context when its daily grain is
           sufficient.
        6. Drill into `urbangreen_dw.fact_sensor_readings` only when the
           user needs the actual offending readings or when aggregate data
           cannot answer the request.
        7. Execute only the query or queries necessary for the requested
           investigation.
        8. Report whether anomalous behavior exists, its extent, and the
           configured range used.

        Clearly distinguish aggregate trend information from individual
        offending readings.
        """
    ).strip()
