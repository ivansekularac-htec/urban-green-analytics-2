"""Tests for the slash-command prompt templates."""

import re

from app.prompts import analyze_metric, compare_farms, investigate_anomaly

PROMPTS = (analyze_metric, compare_farms, investigate_anomaly)

# Every table that exists in the warehouse. A prompt naming anything else would
# steer the model toward a table it cannot query.
WAREHOUSE_TABLES = {
    "dim_crop",
    "dim_date",
    "dim_farm",
    "dim_quality_grade",
    "dim_role",
    "dim_sensor",
    "dim_sensor_type",
    "dim_time",
    "dim_user",
    "dim_user_farm_role",
    "fact_daily_farm_metrics",
    "fact_daily_farm_quality_metrics",
    "fact_daily_sensor_metrics",
    "fact_farm_leaderboard",
    "fact_harvests",
    "fact_sensor_readings",
}

TABLE_TOKEN_PATTERN = re.compile(r"\b(?:dim|fact|agg)_[a-z_]+\b")

# Instructions are phrased as actions to take. The one deliberate exception is
# the rail in analyze_metric against substituting an invented metric formula.
NEGATIVE_PATTERN = re.compile(r"\b(?:[Dd]o not|[Nn]ever|[Dd]on't)\b")

NO_ROWS_RULE = "If the query returns no rows, widen the window and say so in your answer."


def flatten(message: str) -> str:
    """Collapse whitespace so phrase assertions survive line wrapping."""

    return " ".join(message.split())


def default_messages() -> list[str]:
    return [
        analyze_metric("Total Harvest Yield"),
        compare_farms(),
        investigate_anomaly(3),
    ]


def test_docstrings_suit_a_slash_command_picker():
    for prompt in PROMPTS:
        docstring = prompt.__doc__

        assert docstring is not None
        assert "\n" not in docstring
        assert len(docstring) <= 80


def test_prompts_return_one_stripped_message():
    for message in default_messages():
        assert isinstance(message, str)
        assert message == message.strip()


def test_prompts_share_the_same_sections():
    for message in default_messages():
        assert message.startswith("You are answering a question about the UrbanGreen")
        assert "### Task" in message
        assert "### Steps" in message
        assert "### Answer format" in message


def test_prompts_only_reference_tables_that_exist():
    for message in default_messages():
        referenced = set(TABLE_TOKEN_PATTERN.findall(message))

        assert referenced <= WAREHOUSE_TABLES


def test_prompts_show_a_runnable_anchor_rather_than_a_placeholder():
    for message in default_messages():
        flat = flatten(message)

        assert "Anchor the window to the data itself" in flat
        assert "(SELECT max(metric_date) FROM fact_daily" in flat
        assert "<table>" not in message
        assert "<date_column>" not in message


def test_prompts_recover_from_an_empty_result():
    for message in default_messages():
        assert NO_ROWS_RULE in flatten(message)


def test_prompts_ask_for_the_window_and_sources_in_the_answer():
    for message in default_messages():
        flat = flatten(message)

        assert "Window: <first date> to <last date>." in flat
        assert "Source: <tables you read>." in flat


def test_only_the_metric_formula_rail_is_phrased_as_a_prohibition():
    assert NEGATIVE_PATTERN.findall(analyze_metric("Total Harvest Yield")) == ["do not"]
    assert NEGATIVE_PATTERN.findall(compare_farms()) == []
    assert NEGATIVE_PATTERN.findall(investigate_anomaly(3)) == []


def test_analyze_metric_steers_through_resources_then_one_query():
    flat = flatten(analyze_metric("Energy Efficiency"))

    assert 'Report the "Energy Efficiency" metric' in flat
    assert 'copy the definition of "Energy Efficiency" verbatim' in flat
    assert "urbangreen://conventions" in flat
    assert "FINAL / argMax" in flat
    assert "describe_table" in flat
    assert "a single execute_query" in flat


def test_analyze_metric_keeps_the_formula_rail():
    flat = flatten(analyze_metric("Made Up Metric"))

    assert "That formula is the only correct one for this metric" in flat
    assert "do not substitute your own" in flat
    assert "list the metric names it does define and stop there" in flat


def test_analyze_metric_answer_format_carries_the_unit():
    flat = flatten(analyze_metric("Energy Efficiency"))

    assert "Energy Efficiency: <value> <unit>" in flat


def test_analyze_metric_window_defaults_to_thirty_days():
    assert "most recent 30 days" in flatten(analyze_metric("Total Harvest Yield"))
    assert "most recent 7 days" in flatten(analyze_metric("Total Harvest Yield", days=7))


def test_compare_farms_defaults_to_every_farm():
    flat = flatten(compare_farms())

    assert "Rank all currently active farms" in flat
    assert "Include every farm that reported in the window." in flat
    assert "farm_id IN" not in flat


def test_compare_farms_filters_on_supplied_ids():
    flat = flatten(compare_farms(farm_ids="1, 4 ,7"))

    assert "Rank farms 1, 4, 7" in flat
    assert "Restrict the comparison to farm_id IN (1, 4, 7)." in flat


def test_compare_farms_ignores_empty_id_tokens():
    assert "farm_id IN (2, 3)" in flatten(compare_farms(farm_ids=" 2, ,3, "))


def test_compare_farms_names_farms_from_the_current_dimension_version():
    flat = flatten(compare_farms())

    assert "dim_farm FINAL WHERE is_current = 1" in flat
    assert "show every farm by name" in flat


def test_compare_farms_prefers_aggregates_and_stored_ranks():
    flat = flatten(compare_farms(dimension="energy efficiency"))

    assert 'Rank all currently active farms by "energy efficiency"' in flat
    assert "Build the query from the pre-aggregated daily facts" in flat
    assert "fact_daily_farm_metrics" in flat
    assert "read the stored value from fact_farm_leaderboard" in flat


def test_compare_farms_answer_format_ranks_and_calls_out_both_ends():
    message = compare_farms(dimension="yield efficiency")

    assert "| Rank | Farm | yield efficiency (<unit>) |" in message
    assert "Leader: <farm> at <value> <unit>." in message
    assert "Laggard: <farm> at <value> <unit>." in message


def test_investigate_anomaly_defines_an_anomaly_by_sensor_type_thresholds():
    flat = flatten(investigate_anomaly(farm_id=12))

    assert "### Anomaly definition" in flat
    assert "outside its sensor type's optimal_min / optimal_max range in dim_sensor_type" in flat


def test_investigate_anomaly_treats_the_stored_flag_as_the_definition():
    flat = flatten(investigate_anomaly(farm_id=12))

    assert "fact_sensor_readings.is_anomaly" in flat
    assert "fact_daily_sensor_metrics.anomaly_count" in flat
    assert "thresholds in force at reading time" in flat
    assert "Treat those stored columns as the definition" in flat


def test_investigate_anomaly_uses_the_daily_aggregate_joined_to_the_type():
    flat = flatten(investigate_anomaly(farm_id=12))

    assert "fact_daily_sensor_metrics FINAL joined to dim_sensor_type FINAL" in flat
    assert "on sensor_type_id" in flat
    assert "Filter farm_id = 12." in flat


def test_investigate_anomaly_drills_into_raw_readings_only_on_request():
    flat = flatten(investigate_anomaly(farm_id=12))

    assert "Reach for fact_sensor_readings FINAL WHERE is_anomaly = 1" in flat
    assert "when the user wants the actual offending readings" in flat
    assert "otherwise stay with the daily aggregate" in flat


def test_investigate_anomaly_answer_format_reports_rate_and_range():
    message = investigate_anomaly(farm_id=12)

    assert "| Sensor type | Readings | Anomalies | Anomaly rate | Optimal range |" in message
    assert "two or three days with the highest anomaly rate" in flatten(message)


def test_investigate_anomaly_defaults_to_all_sensor_types_over_seven_days():
    flat = flatten(investigate_anomaly(farm_id=12))

    assert "anomalous sensor readings at farm 12" in flat
    assert "most recent 7 days" in flat
    assert "Cover every sensor type reporting at that farm." in flat


def test_investigate_anomaly_filters_on_a_named_sensor_type():
    flat = flatten(investigate_anomaly(farm_id=12, sensor_type=" temperature ", days=14))

    assert 'anomalous "temperature" readings at farm 12' in flat
    assert 'Restrict to the sensor type named "temperature" in dim_sensor_type.name.' in flat
    assert "most recent 14 days" in flat
