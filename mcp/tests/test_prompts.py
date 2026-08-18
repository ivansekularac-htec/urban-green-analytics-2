"""Tests for UrbanGreen MCP prompt templates."""

import pytest

from app.prompts import analyze_metric, compare_farms, investigate_anomaly
from app.resources import (
    CONVENTIONS_RESOURCE_URI,
    METRICS_RESOURCE_URI,
    WAREHOUSE_DATABASE,
)


def test_analyze_metric_contract():
    prompt = analyze_metric("Energy Efficiency")

    assert "Energy Efficiency" in prompt
    assert "last 30 days" in prompt
    assert "INTERVAL 29 DAY" in prompt
    assert "INTERVAL 30 DAY" in prompt
    assert METRICS_RESOURCE_URI in prompt
    assert CONVENTIONS_RESOURCE_URI in prompt
    assert prompt.index("describe_table") < prompt.index("execute_query")
    assert "unit" in prompt.lower()
    assert "source table" in prompt.lower()


def test_analyze_metric_renders_custom_window():
    prompt = analyze_metric("Total Harvest Yield", 90)

    assert "Total Harvest Yield" in prompt
    assert "last 90 days" in prompt
    assert "INTERVAL 89 DAY" in prompt
    assert "INTERVAL 90 DAY" in prompt


def test_compare_farms_contract():
    prompt = compare_farms("101, 205")

    assert "101, 205" in prompt
    assert "composite rank" in prompt
    assert "last 30 days" in prompt
    assert "INTERVAL 29 DAY" in prompt
    assert METRICS_RESOURCE_URI in prompt
    assert CONVENTIONS_RESOURCE_URI in prompt
    assert f"{WAREHOUSE_DATABASE}.dim_farm FINAL" in prompt
    assert f"{WAREHOUSE_DATABASE}.fact_farm_leaderboard" in prompt
    assert "metric_date" in prompt
    assert "leader" in prompt.lower()
    assert "laggard" in prompt.lower()


def test_compare_farms_renders_custom_values():
    prompt = compare_farms("101, 205", "energy efficiency", 90)

    assert "101, 205" in prompt
    assert "energy efficiency" in prompt
    assert "last 90 days" in prompt
    assert "INTERVAL 89 DAY" in prompt


def test_investigate_anomaly_contract():
    prompt = investigate_anomaly("101", "temperature")

    assert "101" in prompt
    assert "temperature" in prompt
    assert "last 7 days" in prompt
    assert "INTERVAL 6 DAY" in prompt
    assert "INTERVAL 7 DAY" in prompt
    assert CONVENTIONS_RESOURCE_URI in prompt
    assert "optimal_min" in prompt
    assert "optimal_max" in prompt
    assert f"{WAREHOUSE_DATABASE}.fact_daily_sensor_metrics FINAL" in prompt
    assert f"{WAREHOUSE_DATABASE}.dim_sensor_type FINAL" in prompt
    assert f"{WAREHOUSE_DATABASE}.fact_sensor_readings" in prompt
    assert prompt.index("fact_daily_sensor_metrics") < prompt.index(
        "fact_sensor_readings"
    )


def test_investigate_anomaly_renders_custom_window():
    prompt = investigate_anomaly("101", "humidity", 14)

    assert "101" in prompt
    assert "humidity" in prompt
    assert "last 14 days" in prompt
    assert "INTERVAL 13 DAY" in prompt
    assert "INTERVAL 14 DAY" in prompt


@pytest.mark.parametrize("days", [0, -1, True, 30.5, "30"])
@pytest.mark.parametrize(
    ("prompt_function", "arguments"),
    [
        (analyze_metric, ("Energy Efficiency",)),
        (compare_farms, ("101, 205", "composite rank")),
        (investigate_anomaly, ("101", "temperature")),
    ],
)
def test_prompts_reject_invalid_day_counts(prompt_function, arguments, days):
    with pytest.raises(ValueError, match="positive integer"):
        prompt_function(*arguments, days)


def test_prompts_do_not_reference_nonexistent_tables():
    prompts = [
        compare_farms("101, 205"),
        investigate_anomaly("101", "temperature"),
    ]

    assert all("agg_hourly_farm_sensor" not in prompt for prompt in prompts)


@pytest.mark.parametrize(
    "prompt_function",
    [analyze_metric, compare_farms, investigate_anomaly],
)
def test_prompts_have_one_line_docstrings(prompt_function):
    docstring = prompt_function.__doc__

    assert docstring
    assert "\n" not in docstring
    assert len(docstring) <= 80
