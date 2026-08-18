"""
Tests for reusable UrbanGreen MCP prompt templates.

Covers the workflow rules that prompts must preserve for metric analysis,
farm comparison, and anomaly investigation.
"""

from app.prompts import (
    analyze_metric,
    compare_farms,
    investigate_anomaly,
)


def test_analyze_metric_uses_canonical_resources_and_single_query():
    result = analyze_metric(
        "Energy Efficiency",
        "last 7 days",
    )

    assert "Energy Efficiency" in result
    assert "last 7 days" in result
    assert "urbangreen://metrics" in result
    assert "urbangreen://conventions" in result
    assert "describe_table" in result
    assert "execute_query` exactly once" in result


def test_analyze_metric_requires_units_and_sources():
    result = analyze_metric("Total Harvest Yield")

    assert "unit" in result
    assert "source table or tables" in result
    assert "last 30 days" in result


def test_compare_farms_uses_current_names_and_aggregate_sources():
    result = compare_farms(
        "1, 2, 3",
        "Total Harvest Yield",
    )

    assert "urbangreen://metrics" in result
    assert "dim_farm FINAL" in result
    assert "is_current = 1" in result
    assert "pre-aggregated or precomputed" in result
    assert "leader" in result
    assert "laggard" in result


def test_compare_farms_uses_requested_window():
    result = compare_farms(
        "10, 20",
        "Energy Efficiency",
        "last 90 days",
    )

    assert "10, 20" in result
    assert "Energy Efficiency" in result
    assert "last 90 days" in result


def test_investigate_anomaly_uses_configured_sensor_range():
    result = investigate_anomaly(
        12,
        "CO2",
        "last 48 hours",
    )

    assert "farm 12" in result
    assert "CO2" in result
    assert "last 48 hours" in result
    assert "dim_sensor_type FINAL" in result
    assert "Do not hardcode threshold values" in result


def test_investigate_anomaly_prefers_aggregate_context():
    result = investigate_anomaly(
        12,
        "Temperature",
    )

    assert "fact_daily_sensor_metrics" in result
    assert "fact_sensor_readings" in result
    assert "actual offending readings" in result
    assert "only when" in result
    assert "last 24 hours" in result


def test_prompt_docstrings_are_short_single_lines():
    prompt_functions = (
        analyze_metric,
        compare_farms,
        investigate_anomaly,
    )

    for prompt_function in prompt_functions:
        assert prompt_function.__doc__
        assert "\n" not in prompt_function.__doc__
