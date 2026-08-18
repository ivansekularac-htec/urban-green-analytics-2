"""
Reusable prompt templates for the UrbanGreen MCP service.

Guides metric analysis, farm comparison, and anomaly investigation.
"""

from __future__ import annotations

from textwrap import dedent

from app.resources import CONVENTIONS_URI, METRICS_URI


def _date_window(days: int) -> str:
    """Return a deterministic ClickHouse calendar-day filter."""
    if days < 1:
        raise ValueError("days must be at least 1")

    if days == 1:
        return (
            "Use today only. "
            "After `describe_table` identifies the appropriate date or timestamp "
            "column, apply this filter: "
            "`toDate(<time_column>) = today()`."
        )

    lookback_days = days - 1

    return (
        f"Use exactly {days} calendar days including today. "
        "After `describe_table` identifies the appropriate date or timestamp "
        "column, apply this filter: "
        f"`toDate(<time_column>) >= today() - INTERVAL {lookback_days} DAY "
        "AND toDate(<time_column>) <= today()`."
    )


def analyze_metric(
    metric_name: str,
    window_days: int = 30,
) -> str:
    """Analyze a metric over a reporting window."""
    window = _date_window(window_days)

    return dedent(
        f"""
        Analyze the UrbanGreen metric "{metric_name}".

        Reporting window:
        {window}

        Follow this workflow:

        1. Read `{METRICS_URI}` and locate the canonical definition, unit,
           calculation, and `Source` or `Sources` for the requested metric.
        2. Read `{CONVENTIONS_URI}` and apply the relevant ClickHouse rules,
           including `FINAL`, `argMax`, SCD2 handling, and fact deduplication.
        3. Call `describe_table` for every source table identified by the
           canonical metric definition before writing SQL.
        4. Use the reporting-window filter above with the appropriate date or
           timestamp column identified from the table schema.
        5. Build one ClickHouse query.
        6. Call `execute_query` exactly once.
        7. Report the result with its unit and name the source table or tables
           used.

        Do not invent a formula or source that is not defined by
        `{METRICS_URI}`. If the canonical metric definition does not provide
        enough source information to construct the query safely, report that
        instead of guessing.
        """
    ).strip()


def compare_farms(
    farm_ids: str,
    dimension: str = "Total Harvest Yield",
    window_days: int = 30,
) -> str:
    """Compare and rank farms by a selected metric."""
    window = _date_window(window_days)

    return dedent(
        f"""
        Compare farms {farm_ids} by "{dimension}".

        Reporting window:
        {window}

        Follow this workflow:

        1. Read `{METRICS_URI}` and find the canonical metric matching
           "{dimension}". Use its definition, unit, calculation, and source.
           If no canonical metric matches, report that the requested dimension
           is unsupported instead of inventing a definition.
        2. Read `{CONVENTIONS_URI}` and apply the relevant ClickHouse rules.
        3. Use `dim_farm FINAL` with `is_current = 1` to resolve current farm
           names.
        4. Prefer the pre-aggregated or precomputed warehouse source identified
           by `{METRICS_URI}` when it can answer the request. Do not rebuild an
           available daily aggregate or leaderboard metric from atomic facts.
        5. Call `describe_table` for every table used before writing SQL.
        6. Use the reporting-window filter above with the appropriate date or
           timestamp column identified from the table schema.
        7. Call `execute_query` once for only the requested farms.
        8. Return a small ranked table containing farm name, metric value,
           unit, and rank.

        After the table, identify the leader and the laggard and briefly
        describe the difference. Name the source table or tables used.
        """
    ).strip()


def investigate_anomaly(
    farm_id: int,
    sensor_type: str,
    since_days: int = 7,
) -> str:
    """Investigate anomalous sensor readings for a farm."""
    window = _date_window(since_days)

    if since_days == 1:
        source_guidance = (
            "Use `fact_sensor_readings` for within-day anomaly investigation. "
            "A daily aggregate has only one row for today and cannot provide "
            "a meaningful within-day trend."
        )
    else:
        source_guidance = (
            "Prefer `fact_daily_sensor_metrics` for multi-day trend and "
            "anomaly-rate context. Drill into `fact_sensor_readings` only "
            "when actual offending readings are requested or aggregate data "
            "is insufficient."
        )

    return dedent(
        f"""
        Investigate sensor anomalies for farm {farm_id}, sensor type
        "{sensor_type}".

        Reporting window:
        {window}

        Treat a reading as anomalous when it falls outside the configured
        minimum or maximum range for its sensor type in `dim_sensor_type`.

        Follow this workflow:

        1. Read `{METRICS_URI}` for the canonical anomaly and sensor metric
           definitions.
        2. Read `{CONVENTIONS_URI}` for the applicable ClickHouse and SCD2
           rules.
        3. Call `describe_table` for `dim_sensor_type` and every fact table
           needed for the investigation.
        4. Use `dim_sensor_type FINAL` with `is_current = 1` for the configured
           sensor range.
        5. Use the reporting-window filter above with the appropriate date or
           timestamp column identified from the table schema.
        6. {source_guidance}
        7. Call `execute_query` only for the query or queries needed for the
           investigation.
        8. Report whether anomalous behavior exists, its extent, and the
           configured range used.

        Distinguish aggregate trend evidence from individual offending
        readings.
        """
    ).strip()
