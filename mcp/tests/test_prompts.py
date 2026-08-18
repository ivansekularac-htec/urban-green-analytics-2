"""Tests for UrbanGreen MCP prompt templates."""

import pytest

from app.prompts import analyze_metric, compare_farms, investigate_anomaly


def test_analyze_metric_workflow():
    prompt = analyze_metric("Energy Efficiency")

    assert "Energy Efficiency" in prompt
    assert "last 30 days" in prompt
    assert "urbangreen://metrics" in prompt
    assert "urbangreen://conventions" in prompt
    assert "describe_table" in prompt
    assert "execute_query` exactly once" in prompt
    assert "canonical unit" in prompt
    assert "source table" in prompt


def test_analyze_metric_accepts_custom_window():
    prompt = analyze_metric("Total Harvest Yield", "last 90 days")

    assert "Total Harvest Yield" in prompt
    assert "last 90 days" in prompt


def test_compare_farms_workflow():
    prompt = compare_farms("101, 205")

    assert "101, 205" in prompt
    assert "composite rank" in prompt
    assert "dim_farm FINAL" in prompt
    assert "is_current = 1" in prompt
    assert "fact_farm_leaderboard" in prompt
    assert "Markdown table" in prompt
    assert "leader and the laggard" in prompt


def test_compare_farms_accepts_custom_dimension():
    prompt = compare_farms("101, 205", "energy efficiency")

    assert "energy efficiency" in prompt


def test_investigate_anomaly_workflow():
    prompt = investigate_anomaly("101", "temperature")

    assert "101" in prompt
    assert "temperature" in prompt
    assert "last 7 days" in prompt
    assert "optimal_min" in prompt
    assert "optimal_max" in prompt
    assert "fact_daily_sensor_metrics FINAL" in prompt
    assert "dim_sensor_type FINAL" in prompt
    assert "fact_sensor_readings" in prompt
    assert "only if the user explicitly requests" in prompt


def test_investigate_anomaly_accepts_custom_window():
    prompt = investigate_anomaly("101", "humidity", "last 14 days")

    assert "humidity" in prompt
    assert "last 14 days" in prompt


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
def test_prompts_have_terse_one_line_docstrings(prompt_function):
    docstring = prompt_function.__doc__

    assert docstring
    assert "\n" not in docstring
    assert len(docstring) <= 80
