"""Tests for the slash-command prompt templates.

These cover the branching and the contracts with the MCP client: which window
clause is rendered, which farm version the model is pointed at, and what the
picker sees. The prose itself is deliberately not asserted line by line - a
prompt is text, and pinning every phrase only reports that it was reworded.
"""

import re

from app.prompts import analyze_metric, compare_farms, investigate_anomaly

PROMPTS = (analyze_metric, compare_farms, investigate_anomaly)

# Instructions are phrased as actions to take. The one deliberate exception is
# the rail in analyze_metric against substituting an invented metric formula.
NEGATIVE_PATTERN = re.compile(r"\b(?:[Dd]o not|[Nn]ever|[Dd]on't)\b")

PAST_WINDOW = "2025-03-31"


def flatten(message: str) -> str:
    """Collapse whitespace so phrase assertions survive line wrapping."""

    return " ".join(message.split())


def default_messages() -> list[str]:
    return [
        analyze_metric("Total Harvest Yield"),
        compare_farms(),
        investigate_anomaly("Riverside"),
    ]


def past_messages() -> list[str]:
    return [
        analyze_metric("Total Harvest Yield", ending=PAST_WINDOW),
        compare_farms(ending=PAST_WINDOW),
        investigate_anomaly("Riverside", ending=PAST_WINDOW),
    ]


# --- contracts with the client ---------------------------------------------


def test_docstrings_suit_a_slash_command_picker():
    for prompt in PROMPTS:
        docstring = prompt.__doc__

        assert docstring is not None
        assert "\n" not in docstring
        assert len(docstring) <= 80


def test_every_prompt_renders_the_same_sections():
    for message in default_messages() + past_messages():
        assert message == message.strip()
        assert message.startswith("You are answering a question about the UrbanGreen")
        assert "### Task" in message
        assert "### Steps" in message
        assert "### Answer format" in message
        assert "Source: <tables you read>." in flatten(message)


def test_only_the_metric_formula_rail_is_phrased_as_a_prohibition():
    assert NEGATIVE_PATTERN.findall(analyze_metric("Total Harvest Yield")) == ["do not"]
    assert NEGATIVE_PATTERN.findall(compare_farms()) == []
    assert NEGATIVE_PATTERN.findall(investigate_anomaly("Riverside")) == []


# --- window ----------------------------------------------------------------


def test_open_ended_window_anchors_to_the_latest_loaded_data():
    for message in default_messages():
        flat = flatten(message)

        assert "most recent" in flat
        assert "(SELECT max(metric_date) FROM fact_daily" in flat
        assert "toDate(" not in flat


def test_past_window_is_pinned_to_the_date_the_user_named():
    for message in past_messages():
        flat = flatten(message)

        assert f"days ending {PAST_WINDOW}" in flat
        assert f"WHERE metric_date > toDate('{PAST_WINDOW}') -" in flat
        assert f"AND metric_date <= toDate('{PAST_WINDOW}')" in flat
        assert "SELECT max(metric_date)" not in flat


def test_windows_default_to_thirty_days_and_honour_the_argument():
    assert "most recent 30 days" in flatten(analyze_metric("Total Harvest Yield"))
    assert "most recent 30 days" in flatten(compare_farms())
    assert "most recent 7 days" in flatten(investigate_anomaly("Riverside"))
    assert "most recent 14 days" in flatten(analyze_metric("Total Harvest Yield", days=14))


# --- analyze_metric --------------------------------------------------------


def test_analyze_metric_steers_the_model_and_keeps_the_formula_rail():
    flat = flatten(analyze_metric("Energy Efficiency"))

    assert 'Report the "Energy Efficiency" metric' in flat
    assert 'copy the definition of "Energy Efficiency" verbatim' in flat
    assert "do not substitute your own" in flat
    assert "list the metric names it does define and stop there" in flat
    assert "urbangreen://conventions" in flat
    assert "describe_table" in flat
    assert "a single execute_query" in flat
    assert "Energy Efficiency: <value> <unit>" in flat


# --- compare_farms ---------------------------------------------------------


def test_compare_farms_defaults_to_every_farm():
    flat = flatten(compare_farms())

    assert 'Rank every farm by "yield"' in flat
    assert "Compare every farm that reported in the window." in flat
    assert "Resolve" not in flat


def test_compare_farms_resolves_free_text_to_farms():
    flat = flatten(compare_farms(farms="Riverside, Novi Sad, 7"))

    assert 'Rank the farms matching "Riverside, Novi Sad, 7"' in flat
    assert 'Resolve "Riverside, Novi Sad, 7" against dim_farm FINAL' in flat
    assert "match each term case-insensitively on farm name, on city, or on farm_id" in flat
    assert "list the candidates with their city and ask which was meant" in flat


def test_compare_farms_keeps_idle_farms_in_scope_for_either_window():
    for message in (compare_farms(), compare_farms(ending=PAST_WINDOW)):
        flat = flatten(message)

        assert "Filter dim_farm.status only when the request names one" in flat
        assert "compare farms of every status" in flat
        assert "idle today may have been producing during the window" in flat
        assert "Label every farm by name, taken from dim_farm FINAL WHERE is_current = 1." in flat


def test_compare_farms_steers_to_aggregates_and_a_ranked_answer():
    message = compare_farms(dimension="yield efficiency")
    flat = flatten(message)

    assert "Build the query from the pre-aggregated daily facts" in flat
    assert "read the stored value from fact_farm_leaderboard" in flat
    assert "| Rank | Farm | yield efficiency (<unit>) |" in message
    assert "Leader: <farm> at <value> <unit>." in message
    assert "Laggard: <farm> at <value> <unit>." in message


def test_compare_farms_answer_table_stays_aligned_whatever_the_dimension():
    for dimension in ("yield", "environmental compliance rate"):
        rows = [
            line
            for line in compare_farms(dimension=dimension).splitlines()
            if line.startswith("| ")
        ]

        assert len({len(row) for row in rows}) == 1


# --- investigate_anomaly ---------------------------------------------------


def test_investigate_anomaly_resolves_the_farm_and_keeps_idle_farms_in_scope():
    flat = flatten(investigate_anomaly("Novi Sad"))

    assert 'readings at the farm matching "Novi Sad"' in flat
    assert 'Resolve "Novi Sad" against dim_farm FINAL' in flat
    assert "match case-insensitively on farm name, on city, or on farm_id" in flat
    assert "Match on any status" in flat
    assert "If it matches several farms, list them with their city" in flat


def test_investigate_anomaly_treats_the_stored_flag_as_the_definition():
    flat = flatten(investigate_anomaly("Riverside"))

    assert "outside its sensor type's optimal_min / optimal_max range in dim_sensor_type" in flat
    assert "fact_sensor_readings.is_anomaly" in flat
    assert "fact_daily_sensor_metrics.anomaly_count" in flat
    assert "thresholds in force at reading time" in flat
    assert "Treat those stored columns as the definition" in flat


def test_investigate_anomaly_uses_the_aggregate_and_drills_down_only_on_request():
    message = investigate_anomaly("Riverside")
    flat = flatten(message)

    assert "fact_daily_sensor_metrics FINAL joined to dim_sensor_type FINAL" in flat
    assert "Reach for fact_sensor_readings FINAL WHERE is_anomaly = 1" in flat
    assert "otherwise stay with the daily aggregate" in flat
    assert "| Sensor type | Readings | Anomalies | Anomaly rate | Optimal range |" in message


def test_investigate_anomaly_scopes_to_one_sensor_type_when_named():
    every_type = flatten(investigate_anomaly("Riverside"))
    one_type = flatten(investigate_anomaly("Riverside", sensor_type=" temperature "))

    assert "anomalous sensor readings" in every_type
    assert "Cover every sensor type reporting at that farm." in every_type

    assert 'anomalous "temperature" readings' in one_type
    assert 'Restrict to the sensor type named "temperature" in dim_sensor_type.name.' in one_type
