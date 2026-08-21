"""Generate the executive report summary with Ollama."""

import json
import logging
from datetime import date

from ollama import Client

from reports.config import get_ollama_settings
from reports.formatting import format_integer, format_number, format_percent
from reports.models import ReportState, ReportSummary, TopFarm

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """
You write concise executive summaries for UrbanGreen daily reports.

Use only supplied values.

Rules:
- never invent, interpret, evaluate, or explain KPI values
- do not infer causes, trends, comparisons, performance, or business impact
- do not use relative dates such as "today" or "yesterday"
- do not use causal wording such as "resulting in", "leading to", or "because"
- do not use interpretive wording such as "shows", "indicates", or "suggests"
- preserve supplied numbers, formatting, units, percentages, ranks, and names
- numeric zero is valid data and must remain numeric
- N/A means only that the supplied value is unavailable
- use leaderboard ranks exactly as supplied
- do not infer information beyond the supplied leaderboard metadata

Write direct, neutral, factual English suitable for management.
""".strip()


def _get_ollama_client() -> Client:
    """Create the Ollama client used for report summarization."""
    settings = get_ollama_settings()
    return Client(host=settings.url)


def _format_report_date(value: str) -> str:
    """Format the report date for narrative text."""
    report_date = date.fromisoformat(value)
    return f"{report_date.strftime('%B')} {report_date.day}, {report_date.year}"


def _format_measurement(value: float | int | None, unit: str) -> str:
    """Format a KPI value with its unit."""
    if value is None:
        return "N/A"
    return f"{format_number(value)} {unit}"


def _build_summary_metrics(state: ReportState) -> dict[str, str]:
    """Build presentation-ready KPI values for the language model."""
    metrics = state["metrics"]
    return {
        "farms_reporting": format_integer(metrics["farms_reporting"]),
        "total_yield": _format_measurement(metrics["total_yield_kg"], "kg"),
        "harvest_count": format_integer(metrics["harvest_count"]),
        "premium_yield": _format_measurement(metrics["premium_yield_kg"], "kg"),
        "premium_yield_share": format_percent(metrics["premium_yield_share"]),
        "energy_consumption": _format_measurement(metrics["energy_kwh"], "kWh"),
        "energy_efficiency": _format_measurement(
            metrics["energy_efficiency_kwh_per_kg"], "kWh/kg"
        ),
        "sensor_readings": format_integer(metrics["reading_count"]),
        "sensor_anomalies": format_integer(metrics["anomaly_count"]),
        "sensor_anomaly_rate": format_percent(metrics["sensor_anomaly_rate"]),
    }


def _build_top_rank_entries(
    top_farms: list[TopFarm],
    top_rank: int | None,
) -> list[dict[str, str]]:
    """Build displayed entries belonging to the highest leaderboard rank."""
    if top_rank is None:
        return []

    return [
        {
            "rank": str(farm["rank"]),
            "farm_name": farm["farm_name"],
            "composite_score": format_number(farm["composite_score"]),
        }
        for farm in top_farms
        if farm["rank"] == top_rank
    ]


def summarize_metrics(state: ReportState) -> dict[str, object]:
    """Generate the executive narrative and three insight bullets."""
    settings = get_ollama_settings()
    metrics = _build_summary_metrics(state)
    report_date = _format_report_date(state["report_date"])
    top_rank = state["top_rank"]
    top_rank_count = state["top_rank_count"]
    top_rank_entries = _build_top_rank_entries(state["top_farms"], top_rank)

    leaderboard = {
        "top_rank": str(top_rank) if top_rank is not None else "N/A",
        "top_rank_count": format_integer(top_rank_count),
        "displayed_top_rank_entries": top_rank_entries,
    }

    logger.info(f"Summarizing executive KPIs for {state['report_date']}")

    prompt = f"""
Create UrbanGreen executive report content for {report_date}.

KPI values:
{json.dumps(metrics, indent=2)}

Leaderboard:
{json.dumps(leaderboard, indent=2)}

Return exactly these five fields.

narrative_production:
Write one sentence using this structure:
"On {report_date}, UrbanGreen recorded [total_yield] across [farms_reporting]
reporting farms with [harvest_count] harvests."

Use the supplied values exactly.

narrative_energy:
If energy_efficiency is available, write:
"Energy consumption totaled [energy_consumption], with energy efficiency of
[energy_efficiency]."

If energy_efficiency is N/A, write:
"Energy consumption totaled [energy_consumption]."

premium_insight:
If premium_yield_share is available, write:
"Premium yield totaled [premium_yield], representing [premium_yield_share]
of total yield."

If premium_yield_share is N/A, write:
"Premium yield totaled [premium_yield]; premium yield share was unavailable."

leaderboard_insight:
If top_rank_count is greater than 1, write:
"[top_rank_count] farms shared rank [top_rank], including [displayed farm names]."

If top_rank_count is 1, write:
"[displayed farm name] held rank [top_rank] with a composite score of
[composite_score]."

The displayed farms are examples when multiple farms share the rank.
Do not say "top rank count".

sensor_insight:
Write:
"[sensor_anomalies] sensor anomalies were recorded across [sensor_readings]
sensor readings, corresponding to a sensor anomaly rate of [sensor_anomaly_rate]."

Preserve all supplied values exactly.
Do not add, remove, reinterpret, or move information between fields.
Return only the structured report content.
""".strip()

    response = _get_ollama_client().chat(
        model=settings.model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        format=ReportSummary.model_json_schema(),
        think=False,
        options={
            "temperature": 0,
            "num_predict": settings.max_tokens,
        },
    )

    summary = ReportSummary.model_validate_json(response.message.content)

    logger.info(f"Generated executive summary for {state['report_date']}")

    return {
        "narrative": (
            f"{summary.narrative_production.strip()} {summary.narrative_energy.strip()}"
        ),
        "insights": [
            summary.premium_insight.strip(),
            summary.leaderboard_insight.strip(),
            summary.sensor_insight.strip(),
        ],
    }
