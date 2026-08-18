"""
Tests for reusable UrbanGreen MCP prompt templates.

Covers stable prompt contracts for resources, workflow ordering,
defaults, table selection, and validation.
"""

import pytest

from app.prompts import (
    analyze_metric,
    compare_farms,
    investigate_anomaly,
)
from app.resources import CONVENTIONS_URI, METRICS_URI


def test_analyze_metric_uses_required_resources_and_tool_order():
    result = analyze_metric("Energy Efficiency")

    assert METRICS_URI in result
    assert CONVENTIONS_URI in result
    assert result.index("describe_table") < result.index("execute_query")
    assert result.count("execute_query") == 1


def test_analyze_metric_renders_default_window():
    result = analyze_metric("Energy Efficiency")

    assert "Energy Efficiency" in result
    assert "INTERVAL 29 DAY" in result
    assert "today()" in result


def test_analyze_metric_renders_custom_window():
    result = analyze_metric(
        "Total Harvest Yield",
        window_days=7,
    )

    assert "Total Harvest Yield" in result
    assert "INTERVAL 6 DAY" in result


def test_analyze_metric_renders_today_window():
    result = analyze_metric(
        "Total Harvest Yield",
        window_days=1,
    )

    assert "toDate(<time_column>) = today()" in result


def test_compare_farms_uses_resources_current_names_and_defaults():
    result = compare_farms("1, 2, 3")

    assert METRICS_URI in result
    assert CONVENTIONS_URI in result
    assert "1, 2, 3" in result
    assert "Total Harvest Yield" in result
    assert "dim_farm FINAL" in result
    assert "is_current = 1" in result
    assert "INTERVAL 29 DAY" in result


def test_compare_farms_describes_tables_before_query():
    result = compare_farms(
        "10, 20",
        dimension="Energy Efficiency",
        window_days=90,
    )

    assert "Energy Efficiency" in result
    assert "INTERVAL 89 DAY" in result
    assert result.index("describe_table") < result.index("execute_query")
    assert result.count("execute_query") == 1


def test_investigate_anomaly_uses_resources_and_default_daily_context():
    result = investigate_anomaly(
        12,
        "CO2",
    )

    assert METRICS_URI in result
    assert CONVENTIONS_URI in result
    assert "farm 12" in result
    assert "CO2" in result
    assert "dim_sensor_type FINAL" in result
    assert "is_current = 1" in result
    assert "fact_daily_sensor_metrics" in result
    assert "fact_sensor_readings" in result
    assert "INTERVAL 6 DAY" in result


def test_investigate_anomaly_uses_atomic_readings_for_today():
    result = investigate_anomaly(
        12,
        "CO2",
        since_days=1,
    )

    assert "toDate(<time_column>) = today()" in result
    assert "fact_sensor_readings" in result
    assert "fact_daily_sensor_metrics" not in result


def test_investigate_anomaly_describes_tables_before_query():
    result = investigate_anomaly(
        12,
        "Temperature",
    )

    assert result.index("describe_table") < result.index("execute_query")


@pytest.mark.parametrize("days", [0, -1])
def test_analyze_metric_rejects_invalid_window(days):
    with pytest.raises(ValueError):
        analyze_metric(
            "Energy Efficiency",
            window_days=days,
        )


@pytest.mark.parametrize("days", [0, -1])
def test_compare_farms_rejects_invalid_window(days):
    with pytest.raises(ValueError):
        compare_farms(
            "1, 2",
            window_days=days,
        )


@pytest.mark.parametrize("days", [0, -1])
def test_investigate_anomaly_rejects_invalid_window(days):
    with pytest.raises(ValueError):
        investigate_anomaly(
            12,
            "CO2",
            since_days=days,
        )


def test_prompt_docstrings_are_short_single_lines():
    prompt_functions = (
        analyze_metric,
        compare_farms,
        investigate_anomaly,
    )

    for prompt_function in prompt_functions:
        assert prompt_function.__doc__
        assert "\n" not in prompt_function.__doc__
