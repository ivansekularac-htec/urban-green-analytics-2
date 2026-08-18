"""
Reusable prompt templates surfaced as slash commands by the MCP client.

Each function is a pure template: it takes the parameters a user would type in
a slash-command picker and returns the user message that steers the model
through the warehouse. Prompts never touch ClickHouse themselves. They tell the
model which knowledge resource to read, which table to describe, and how to
shape the final answer, so the model reaches a correct query on the first try.

Parameters are what a platform user knows, not what the warehouse stores. MCP
prompts are user-controlled: the client renders the message before the model is
involved, so an argument the user cannot fill is an argument nobody fills.
Farms are therefore named in free text - farm name, city, or id - and the model
resolves them against ``dim_farm``.

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

# Farm attributes are a Type-2 dimension, so which version to read depends on
# whether the window is the present or the past. The daily facts carry a
# farm_key resolved as of the event, which makes the historical lookup a plain
# equi-join rather than an interval join.
_CURRENT_FRAME = "Take each farm's name from dim_farm FINAL WHERE is_current = 1."

_HISTORICAL_FRAME = dedent("""\
    The window is in the past, so join the fact's farm_key to dim_farm.farm_key:
    each farm then carries the name, city, and status it had during the window
    rather than the ones it has today. A farm_key of 0 means the version was
    never resolved, so fall back to dim_farm FINAL WHERE is_current = 1 matched
    on farm_id.""")

_STATUS_RULE = dedent("""\
    Farm status is ACTIVE, MAINTENANCE, or INACTIVE. Filter dim_farm.status only
    when the request names one; otherwise compare farms of every status, since a
    farm that is idle today may have been producing during the window.""")


def _hanging(block: str, spaces: int = 11) -> str:
    """Re-indent the continuation lines of a block to sit under a numbered step."""

    lines = block.splitlines()
    padding = " " * spaces

    return "\n".join([lines[0]] + [padding + line for line in lines[1:]])


def _window_phrase(days: int, ending: str) -> str:
    """Describe the reporting window in the words the task statement uses."""

    if ending:
        return f"the {days} days ending {ending}"

    return f"the most recent {days} days of data"


def _window_clause(days: int, ending: str, table: str) -> str:
    """Render the date filter for the window, anchored to the data when open-ended."""

    if ending:
        return (
            f"WHERE metric_date > toDate('{ending}') - {days} AND metric_date <= toDate('{ending}')"
        )

    return f"WHERE metric_date > (SELECT max(metric_date) FROM {table}) - {days}"


def analyze_metric(metric: str, days: int = 30, ending: str = "") -> str:
    """Analyze one canonical warehouse metric over a window of days."""

    ending = ending.strip()

    return dedent(f"""
        {_ROLE}

        ### Task
        Report the "{metric}" metric over {_window_phrase(days, ending)}.

        ### Steps
        1. Read urbangreen://metrics and copy the definition of "{metric}" verbatim: its
           formula, its unit, and the tables it names. That formula is the only correct
           one for this metric; do not substitute your own. If the resource defines no
           such metric, list the metric names it does define and stop there.
        2. Read urbangreen://conventions and apply its FINAL / argMax rules to every
           table you read. These tables keep replaced rows until merges complete, so an
           aggregation without FINAL can double-count.
        3. Call describe_table on every table the definition names, before you write SQL.
        4. Produce the answer with a single execute_query, restricted to the window by
           this filter, substituting the table and date column the definition named:

               {_window_clause(days, ending, "fact_daily_farm_metrics")}

        5. If the query returns no rows, widen the window and say so in your answer.

        ### Answer format
        {metric}: <value> <unit>
        Window: <first date> to <last date>. Source: <tables you read>.
    """).strip()


def compare_farms(
    farms: str = "",
    dimension: str = "yield",
    days: int = 30,
    ending: str = "",
) -> str:
    """Rank farms against each other on one dimension over a window of days."""

    farms = farms.strip()
    ending = ending.strip()

    if farms:
        scope = f'the farms matching "{farms}"'
        resolution = dedent(f"""\
            Resolve "{farms}" against dim_farm FINAL: match each term
            case-insensitively on farm name, on city, or on farm_id, so the user can
            name farms whichever way they know them. If a term matches nothing, or
            matches several farms, list the candidates with their city and ask which
            was meant before querying anything else.""")
    else:
        scope = "every farm"
        resolution = "Compare every farm that reported in the window."

    frame = _HISTORICAL_FRAME if ending else _CURRENT_FRAME

    # Size the answer skeleton to the dimension name so the rendered table stays
    # aligned whatever the user asked to rank by.
    metric_header = f"{dimension} (<unit>)"
    metric_rule = "-" * len(metric_header)
    metric_cell = "...".ljust(len(metric_header))

    return dedent(f"""
        {_ROLE}

        ### Task
        Rank {scope} by "{dimension}" over {_window_phrase(days, ending)}.

        ### Steps
        1. {_hanging(resolution)}
           {_hanging(_STATUS_RULE)}
        2. Read urbangreen://metrics and copy the definition of "{dimension}" verbatim:
           its formula, its unit, and the tables it names. If the resource defines no
           such metric, list the metric names it does define and stop there.
        3. Read urbangreen://conventions and apply its FINAL / argMax rules to every
           table you read.
        4. Build the query from the pre-aggregated daily facts: fact_daily_farm_metrics,
           fact_daily_sensor_metrics, fact_daily_farm_quality_metrics. For a leaderboard
           measure or a rank, read the stored value from fact_farm_leaderboard.
        5. Label every farm by name in the answer.
           {_hanging(frame)}
        6. Call describe_table on every table you are about to query.
        7. Restrict the query to the window with this filter, substituting the table you
           chose:

               {_window_clause(days, ending, "fact_daily_farm_metrics")}

        8. If the query returns no rows, widen the window and say so in your answer.

        ### Answer format
        | Rank | Farm | {metric_header} |
        | ---- | ---- | {metric_rule} |
        | 1    | ...  | {metric_cell} |

        Leader: <farm> at <value> <unit>.
        Laggard: <farm> at <value> <unit>.
        Window: <first date> to <last date>. Source: <tables you read>.
    """).strip()


def investigate_anomaly(
    farm: str,
    sensor_type: str = "",
    days: int = 7,
    ending: str = "",
) -> str:
    """Investigate anomalous sensor readings at one farm."""

    farm = farm.strip()
    sensor_type = sensor_type.strip()
    ending = ending.strip()

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
        Investigate anomalous {reading_scope} readings at the farm matching "{farm}"
        over {_window_phrase(days, ending)}.

        ### Anomaly definition
        An anomaly is a reading outside its sensor type's optimal_min / optimal_max range
        in dim_sensor_type. The warehouse has already applied that rule:
        fact_sensor_readings.is_anomaly was evaluated against the thresholds in force at
        reading time, and fact_daily_sensor_metrics.anomaly_count aggregates it. Treat
        those stored columns as the definition, and read dim_sensor_type for the type
        name, unit, and range you report alongside them.

        ### Steps
        1. Resolve "{farm}" against dim_farm FINAL: match case-insensitively on farm
           name, on city, or on farm_id, so the user can name the farm whichever way
           they know it. Match on any status, since a farm that is idle today may have
           been reporting during the window. If it matches several farms, list them with
           their city and ask which was meant before querying anything else.
        2. Read urbangreen://conventions for the FINAL / argMax rules and
           urbangreen://metrics for the Sensor Anomaly Rate definition.
        3. For trend context, query fact_daily_sensor_metrics FINAL joined to
           dim_sensor_type FINAL (WHERE is_current = 1) on sensor_type_id. The fact table
           carries only sensor_type_id, so this join supplies the type name, its unit,
           and its optimal range.
        4. {sensor_filter}
        5. Call describe_table on every table you are about to query.
        6. Restrict the query to the window with this filter:

               {_window_clause(days, ending, "fact_daily_sensor_metrics")}

        7. Reach for fact_sensor_readings FINAL WHERE is_anomaly = 1 when the user wants
           the actual offending readings; otherwise stay with the daily aggregate. It is
           the raw per-reading table and is far larger.
        8. If the query returns no rows, widen the window and say so in your answer.

        ### Answer format
        | Sensor type | Readings | Anomalies | Anomaly rate | Optimal range |
        | ----------- | -------- | --------- | ------------ | ------------- |
        | ...         | ...      | ...       | ...          | ... <unit>    |

        Name the two or three days with the highest anomaly rate, each with its date and
        rate. Window: <first date> to <last date>. Source: <tables you read>.
    """).strip()
