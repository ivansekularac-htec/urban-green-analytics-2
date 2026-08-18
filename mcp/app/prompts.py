"""
Reusable prompt templates surfaced as slash commands by the MCP client.

Each function is a pure template: it takes the parameters a user would type in
a slash-command picker and returns the user message that steers the model
through the warehouse. Prompts never touch ClickHouse themselves. They tell the
model which knowledge resource to read, which table to describe, and how to
shape the final answer, so the model reaches a correct query on the first try.

Every message follows the same shape - a role line, a ``### Task`` statement,
numbered ``### Steps``, and an ``### Answer format`` skeleton. The skeleton is
shown rather than described because a small local model reproduces a layout it
can see far more reliably than one it has to infer from prose. Steps are phrased
as actions to take rather than mistakes to avoid, which is the more reliable
framing; the single exception is the rail against substituting an invented
metric formula, where naming the failure mode is worth the cost.

The resource URIs referenced here (``urbangreen://metrics``,
``urbangreen://conventions``) must match the URIs the resources are registered
under when the server wires them up.
"""

from textwrap import dedent

_ROLE = (
    "You are answering a question about the UrbanGreen ClickHouse warehouse "
    "using the MCP tools available to you."
)


def _clean_id_list(raw: str) -> list[str]:
    """Split a comma-separated id argument into individual, whitespace-free ids."""

    return [token.strip() for token in raw.split(",") if token.strip()]


def analyze_metric(metric: str, days: int = 30) -> str:
    """Analyze one canonical warehouse metric over a recent window."""

    return dedent(f"""
        {_ROLE}

        ### Task
        Report the "{metric}" metric over the most recent {days} days of data.

        ### Steps
        1. Read urbangreen://metrics and copy the definition of "{metric}" verbatim: its
           formula, its unit, and the tables it names. That formula is the only correct
           one for this metric; do not substitute your own. If the resource defines no
           such metric, list the metric names it does define and stop there.
        2. Read urbangreen://conventions and apply its FINAL / argMax rules to every
           table you read. These tables keep replaced rows until merges complete, so an
           aggregation without FINAL can double-count.
        3. Call describe_table on every table the definition names, before you write SQL.
        4. Produce the answer with a single execute_query. Anchor the window to the data
           itself, substituting the table and date column the definition named:

               WHERE metric_date > (SELECT max(metric_date) FROM fact_daily_farm_metrics) - {days}

        5. If the query returns no rows, widen the window and say so in your answer.

        ### Answer format
        {metric}: <value> <unit>
        Window: <first date> to <last date>. Source: <tables you read>.
    """).strip()


def compare_farms(farm_ids: str = "", dimension: str = "yield", days: int = 30) -> str:
    """Rank farms against each other on one dimension over a recent window."""

    ids = _clean_id_list(farm_ids)

    if ids:
        scope = f"farms {', '.join(ids)}"
        farm_filter = f"Restrict the comparison to farm_id IN ({', '.join(ids)})."
    else:
        scope = "all currently active farms"
        farm_filter = "Include every farm that reported in the window."

    return dedent(f"""
        {_ROLE}

        ### Task
        Rank {scope} by "{dimension}" over the most recent {days} days of data.

        ### Steps
        1. Read urbangreen://metrics and copy the definition of "{dimension}" verbatim:
           its formula, its unit, and the tables it names. If the resource defines no
           such metric, list the metric names it does define and stop there.
        2. Read urbangreen://conventions and apply its FINAL / argMax rules to every
           table you read.
        3. Build the query from the pre-aggregated daily facts: fact_daily_farm_metrics,
           fact_daily_sensor_metrics, fact_daily_farm_quality_metrics. For a leaderboard
           measure or a rank, read the stored value from fact_farm_leaderboard.
        4. Take each farm's name from dim_farm FINAL WHERE is_current = 1, joined on
           farm_id, and show every farm by name.
        5. {farm_filter}
        6. Call describe_table on every table you are about to query.
        7. Anchor the window to the data itself, substituting the table you chose:

               WHERE metric_date > (SELECT max(metric_date) FROM fact_daily_farm_metrics) - {days}

        8. If the query returns no rows, widen the window and say so in your answer.

        ### Answer format
        | Rank | Farm | {dimension} (<unit>) |
        | ---- | ---- | -------------------- |
        | 1    | ...  | ...                  |

        Leader: <farm> at <value> <unit>.
        Laggard: <farm> at <value> <unit>.
        Window: <first date> to <last date>. Source: <tables you read>.
    """).strip()


def investigate_anomaly(farm_id: int, sensor_type: str = "", days: int = 7) -> str:
    """Investigate anomalous sensor readings at one farm."""

    sensor_type = sensor_type.strip()

    if sensor_type:
        reading_scope = f'"{sensor_type}"'
        sensor_filter = (
            f'Restrict to the sensor type named "{sensor_type}" in dim_sensor_type.name.'
        )
    else:
        reading_scope = "sensor"
        sensor_filter = "Cover every sensor type reporting at that farm."

    return dedent(f"""
        {_ROLE}

        ### Task
        Investigate anomalous {reading_scope} readings at farm {farm_id} over the most
        recent {days} days of data.

        ### Anomaly definition
        An anomaly is a reading outside its sensor type's optimal_min / optimal_max range
        in dim_sensor_type. The warehouse has already applied that rule:
        fact_sensor_readings.is_anomaly was evaluated against the thresholds in force at
        reading time, and fact_daily_sensor_metrics.anomaly_count aggregates it. Treat
        those stored columns as the definition, and read dim_sensor_type for the type
        name, unit, and range you report alongside them.

        ### Steps
        1. Read urbangreen://conventions for the FINAL / argMax rules and
           urbangreen://metrics for the Sensor Anomaly Rate definition.
        2. For trend context, query fact_daily_sensor_metrics FINAL joined to
           dim_sensor_type FINAL (WHERE is_current = 1) on sensor_type_id. The fact table
           carries only sensor_type_id, so this join supplies the type name, its unit,
           and its optimal range.
        3. Filter farm_id = {farm_id}.
           {sensor_filter}
        4. Call describe_table on every table you are about to query.
        5. Anchor the window to the data itself:

               WHERE metric_date > (SELECT max(metric_date) FROM fact_daily_sensor_metrics) - {days}

        6. Reach for fact_sensor_readings FINAL WHERE is_anomaly = 1 when the user wants
           the actual offending readings; otherwise stay with the daily aggregate. It is
           the raw per-reading table and is far larger.
        7. If the query returns no rows, widen the window and say so in your answer.

        ### Answer format
        | Sensor type | Readings | Anomalies | Anomaly rate | Optimal range |
        | ----------- | -------- | --------- | ------------ | ------------- |
        | ...         | ...      | ...       | ...          | ... <unit>    |

        Name the two or three days with the highest anomaly rate, each with its date and
        rate. Window: <first date> to <last date>. Source: <tables you read>.
    """).strip()
