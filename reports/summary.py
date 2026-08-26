"""Generate the executive report summary with Ollama."""

import json
import logging
import re
from datetime import date

from ollama import Client

from reports.config import get_ollama_settings
from reports.formatting import format_integer, format_number, format_percent
from reports.models import ReportState, ReportSummary, SensorMetric, TopFarm

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """
You write factual UrbanGreen executive reports from supplied warehouse data.

Use only supplied facts.

Never invent or infer:
- causes or explanations
- trends or changes over time
- spikes, increases, or decreases
- risks or recommended actions
- business or operational significance
- compliance
- sensor health or stability

Direct comparisons between values supplied for the same report date are allowed.

An anomaly rate is the share of sensor readings classified as anomalous.
It is not the percentage of farms with anomalies.

The number of farms with anomalies is supplied separately.

A 100% in-range rate means only that all supplied readings were classified
in range. It does not establish compliance or perfect performance.

Leaderboard ranks and scores are stored warehouse values. Report them exactly
as supplied and do not reinterpret or recalculate them.

A stored energy-efficiency value of 0.0 for a farm with zero harvested yield
does not mean perfect energy efficiency.

Preserve supplied numbers, units, percentages, ranks, and names.

Zero is valid data.
N/A means unavailable.

Avoid repeating the same fact across report sections.

Write natural, concise executive English.
""".strip()


_FORBIDDEN_PATTERNS = (
    r"\bspike\b",
    r"\bspiked\b",
    r"\bincrease(?:d)?\b",
    r"\bdecrease(?:d)?\b",
    r"\bimprov(?:e|ed|ement)\b",
    r"\bdeteriorat(?:e|ed|ion)\b",
    r"\bsuggest(?:s|ed|ing)?\b",
    r"\blikely\b",
    r"\bpotential(?:ly)?\b",
    r"\bcaused by\b",
    r"\battributable to\b",
    r"\blinked to\b",
    r"\brisk(?:s)?\b",
    r"\brecommend(?:s|ed|ation)?\b",
    r"\brequire(?:s|d)? action\b",
    r"\bcompliance\b",
    r"\bcompliant\b",
    r"\bperfect\b",
    r"\bhealthy\b",
    r"\bunhealthy\b",
    r"\bunstable\b",
    r"\bsignificant(?:ly)?\b",
)


def _get_ollama_client(url: str) -> Client:
    """Create the Ollama client used for report summarization."""
    return Client(host=url)


def _format_report_date(value: str) -> str:
    """Format the report date for narrative text."""
    report_date = date.fromisoformat(value)
    return f"{report_date.strftime('%B')} {report_date.day}, {report_date.year}"


def _format_measurement(
    value: float | int | None,
    unit: str,
) -> str:
    """Format a KPI value with its unit."""
    if value is None:
        return "N/A"

    formatted = format_number(value)
    return f"{formatted} {unit}" if unit else formatted


def _build_summary_metrics(
    state: ReportState,
) -> dict[str, str]:
    """Build presentation-ready executive KPI values."""
    metrics = state["metrics"]

    return {
        "farms_reporting": format_integer(metrics["farms_reporting"]),
        "total_yield": _format_measurement(
            metrics["total_yield_kg"],
            "kg",
        ),
        "harvest_count": format_integer(metrics["harvest_count"]),
        "premium_yield": _format_measurement(
            metrics["premium_yield_kg"],
            "kg",
        ),
        "premium_yield_share": format_percent(metrics["premium_yield_share"]),
        "energy_consumption": _format_measurement(
            metrics["energy_kwh"],
            "kWh",
        ),
        "energy_efficiency": _format_measurement(
            metrics["energy_efficiency_kwh_per_kg"],
            "kWh/kg",
        ),
        "sensor_readings": format_integer(metrics["reading_count"]),
        "sensor_anomalies": format_integer(metrics["anomaly_count"]),
        "sensor_anomaly_rate": format_percent(metrics["sensor_anomaly_rate"]),
    }


def _build_top_rank_entries(
    top_farms: list[TopFarm],
    top_rank: int | None,
) -> list[dict[str, str]]:
    """Build displayed entries belonging to the highest stored rank."""
    if top_rank is None:
        return []

    return [
        {
            "rank": str(farm["rank"]),
            "farm_name": farm["farm_name"],
            "total_yield": _format_measurement(
                farm["total_yield_kg"],
                "kg",
            ),
            "premium_yield_share": format_percent(farm["premium_yield_share"]),
            "energy_efficiency": _format_measurement(
                farm["energy_efficiency_kwh_per_kg"],
                "kWh/kg",
            ),
            "composite_score": format_number(farm["composite_score"]),
        }
        for farm in top_farms
        if farm["rank"] == top_rank
    ]


def _build_sensor_payload(
    sensor_metrics: list[SensorMetric],
) -> list[dict[str, str]]:
    """Build presentation-ready sensor facts for the language model."""
    return [
        {
            "sensor_name": sensor["sensor_name"],
            "unit": sensor["unit"],
            "reporting_farms": format_integer(sensor["farms_reporting"]),
            "farms_with_anomalies": format_integer(sensor["farms_with_anomalies"]),
            "readings": format_integer(sensor["reading_count"]),
            "average": _format_measurement(
                sensor["average_value"],
                sensor["unit"],
            ),
            "minimum": _format_measurement(
                sensor["min_value"],
                sensor["unit"],
            ),
            "maximum": _format_measurement(
                sensor["max_value"],
                sensor["unit"],
            ),
            "anomalies": format_integer(sensor["anomaly_count"]),
            "anomaly_rate": format_percent(sensor["anomaly_rate"]),
            "in_range_rate": format_percent(sensor["in_range_rate"]),
        }
        for sensor in sensor_metrics
    ]


def _validate_summary_language(
    summary: ReportSummary,
) -> None:
    """Reject unsupported interpretive language from the model."""
    text = " ".join(
        [
            summary.narrative,
            summary.sensor_analysis,
            *summary.insights,
        ]
    ).lower()

    for pattern in _FORBIDDEN_PATTERNS:
        if re.search(pattern, text):
            raise ValueError(f"LLM summary contains unsupported language: {pattern}")


def _build_fallback_sensor_analysis(
    sensor_metrics: list[SensorMetric],
) -> str:
    """Build deterministic factual sensor analysis."""
    if not sensor_metrics:
        return "Detailed sensor metrics were unavailable for this report date."

    total_readings = sum(sensor["reading_count"] for sensor in sensor_metrics)

    total_anomalies = sum(sensor["anomaly_count"] for sensor in sensor_metrics)

    sensor_type_count = len(sensor_metrics)

    if total_readings == 0:
        return (
            f"{format_integer(sensor_type_count)} sensor types "
            "were represented, but no readings were recorded."
        )

    if total_anomalies == 0:
        return (
            f"{format_integer(sensor_type_count)} sensor types recorded "
            f"{format_integer(total_readings)} readings. "
            "No anomalous readings were recorded in the supplied "
            "daily sensor metrics."
        )

    comparable = [
        sensor for sensor in sensor_metrics if sensor["anomaly_rate"] is not None
    ]

    if not comparable:
        return (
            f"{format_integer(sensor_type_count)} sensor types recorded "
            f"{format_integer(total_readings)} readings, including "
            f"{format_integer(total_anomalies)} anomalous readings."
        )

    highest = max(
        comparable,
        key=lambda sensor: sensor["anomaly_rate"] or 0.0,
    )

    overall_rate = total_anomalies / total_readings

    return (
        f"{format_integer(sensor_type_count)} sensor types recorded "
        f"{format_integer(total_readings)} readings, including "
        f"{format_integer(total_anomalies)} anomalous readings "
        f"({format_percent(overall_rate)} overall). "
        f"{highest['sensor_name']} had the highest anomaly rate among "
        f"the reported sensor types at "
        f"{format_percent(highest['anomaly_rate'])}, with anomalies "
        f"recorded on "
        f"{format_integer(highest['farms_with_anomalies'])} of "
        f"{format_integer(highest['farms_reporting'])} reporting farms."
    )


def _build_fallback_insights(
    state: ReportState,
) -> list[str]:
    """Build one to three factual fallback insights."""
    insights: list[str] = []

    if state["top_rank"] is not None and state["top_farms"]:
        top_entries = [
            farm for farm in state["top_farms"] if farm["rank"] == state["top_rank"]
        ]

        if state["top_rank_count"] == 1 and top_entries:
            insights.append(
                f"{top_entries[0]['farm_name']} held stored "
                f"leaderboard rank {state['top_rank']}."
            )
        elif state["top_rank_count"] > 1:
            insights.append(
                f"{format_integer(state['top_rank_count'])} farms "
                f"shared stored leaderboard rank "
                f"{state['top_rank']}."
            )

    sensor_metrics = state["sensor_metrics"]

    if sensor_metrics and len(insights) < 3:
        reporting_counts = {
            sensor["farms_reporting"]
            for sensor in sensor_metrics
            if sensor["reading_count"] > 0
        }

        if len(reporting_counts) == 1:
            farms_reporting = next(iter(reporting_counts))

            insights.append(
                f"All {format_integer(len(sensor_metrics))} sensor types "
                f"received readings from "
                f"{format_integer(farms_reporting)} reporting farms."
            )

    if sensor_metrics and len(insights) < 3:
        zero_anomaly_sensors = [
            sensor
            for sensor in sensor_metrics
            if sensor["reading_count"] > 0 and sensor["anomaly_count"] == 0
        ]

        if zero_anomaly_sensors:
            sensor = zero_anomaly_sensors[0]

            insights.append(
                f"{sensor['sensor_name']} recorded "
                f"{format_integer(sensor['reading_count'])} readings "
                "with no anomalous readings."
            )

    if not insights:
        insights.append(
            f"{format_integer(state['metrics']['farms_reporting'])} farms "
            "reported data for the report date."
        )

    return insights[:3]


def _build_fallback_summary(
    state: ReportState,
    report_date: str,
    metrics: dict[str, str],
) -> ReportSummary:
    """Build deterministic report content when Ollama is unavailable."""
    executive = state["metrics"]

    narrative_parts = [
        (f"On {report_date}, {metrics['farms_reporting']} farms reported data.")
    ]

    if executive["harvest_count"] == 0:
        narrative_parts.append("No harvests or harvested yield were recorded.")
    else:
        narrative_parts.append(
            f"Total harvested yield was "
            f"{metrics['total_yield']} from "
            f"{metrics['harvest_count']} harvests."
        )

    narrative_parts.append(
        f"Energy consumption totaled {metrics['energy_consumption']}."
    )

    if executive["energy_efficiency_kwh_per_kg"] is not None:
        narrative_parts.append(f"Energy efficiency was {metrics['energy_efficiency']}.")

    if executive["premium_yield_share"] is not None:
        narrative_parts.append(
            f"Premium yield represented "
            f"{metrics['premium_yield_share']} "
            "of total yield."
        )

    return ReportSummary(
        narrative=" ".join(narrative_parts),
        sensor_analysis=_build_fallback_sensor_analysis(state["sensor_metrics"]),
        insights=_build_fallback_insights(state),
    )


def summarize_metrics(
    state: ReportState,
) -> dict[str, object]:
    """Generate factual executive and sensor report text."""
    settings = get_ollama_settings()

    metrics = _build_summary_metrics(state)
    report_date = _format_report_date(state["report_date"])

    top_rank_entries = _build_top_rank_entries(
        state["top_farms"],
        state["top_rank"],
    )

    leaderboard = {
        "top_rank": state["top_rank"],
        "top_rank_count": state["top_rank_count"],
        "displayed_top_rank_entries": top_rank_entries,
    }

    sensor_payload = _build_sensor_payload(state["sensor_metrics"])

    logger.info(f"Summarizing executive KPIs for {state['report_date']}")

    prompt = f"""
Create the executive content for the UrbanGreen daily report dated {report_date}.

Network KPI values:
{json.dumps(metrics, indent=2)}

Leaderboard:
{json.dumps(leaderboard, indent=2)}

Sensor-type daily metrics:
{json.dumps(sensor_payload, indent=2)}

Return JSON matching the supplied schema.

NARRATIVE

Write a natural executive overview of approximately 3 to 5 sentences.

Focus on the overall daily picture:
- number of reporting farms
- harvested yield
- harvest activity
- premium yield when available
- energy consumption
- energy efficiency when available

Do not provide detailed sensor-type analysis in the narrative.

The Top Farms table is rendered separately, so do not list or describe
individual farms in the narrative.

If there were zero harvests, state that fact neutrally.
Do not treat zero harvested yield as positive or negative performance.

SENSOR_ANALYSIS

Write approximately 2 to 4 factual sentences about the supplied sensor data.

You may state:
- number of sensor types represented
- reporting farms
- farms with at least one anomaly
- reading counts
- average, minimum, and maximum observed values
- anomaly counts
- anomaly rates
- which supplied sensor type has the highest anomaly rate
- in-range rates

Anomaly rate is the percentage of readings classified as anomalous.
It is not the percentage of farms with anomalies.

Use farms_with_anomalies only when describing how many farms recorded
at least one anomalous reading.

A 100% in-range rate means only that all supplied readings were classified
in range.

Do not infer causes, trends, spikes, changes, risks, stability, compliance,
performance, environmental sources, or recommended actions.

INSIGHTS

Return between one and three concise factual insights.

Each insight must add useful information that is not already stated in the
narrative or sensor_analysis.

The leaderboard is displayed separately, but a concise leaderboard fact may
be used as an insight when it adds useful information.

Use stored leaderboard ranks exactly as supplied.

If leaderboard rows have zero harvested yield, the stored ranks are still
valid warehouse values and may be reported.

Do not interpret zero-yield leaderboard entries as strong performance.

A stored energy-efficiency value of 0.0 for a zero-yield farm does not mean
perfect energy efficiency.

Prefer insights that add a different perspective, such as:
- a stored leaderboard fact
- complete sensor reporting coverage
- a sensor type with readings but no recorded anomalies

Do not create filler merely to reach three insights.
Do not repeat the same KPI in different words.
Do not infer causes, trends, risks, compliance, or recommendations.

Use only the supplied data.
""".strip()

    try:
        response = _get_ollama_client(settings.url).chat(
            model=settings.model,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            format=ReportSummary.model_json_schema(),
            think=False,
            options={
                "temperature": 0,
                "num_predict": settings.max_tokens,
            },
        )

        summary = ReportSummary.model_validate_json(response.message.content)

        logger.info(
            f"Ollama summary for {state['report_date']}: {summary.model_dump_json()}"
        )

        _validate_summary_language(summary)

        logger.info(f"Generated executive summary for {state['report_date']}")

    except Exception:  # noqa: BLE001 - intentional LLM boundary.
        logger.exception(
            f"Ollama summary failed validation for "
            f"{state['report_date']}; "
            "using deterministic fallback"
        )

        summary = _build_fallback_summary(
            state=state,
            report_date=report_date,
            metrics=metrics,
        )

    return {
        "narrative": summary.narrative.strip(),
        "sensor_analysis": summary.sensor_analysis.strip(),
        "insights": [insight.strip() for insight in summary.insights],
    }
