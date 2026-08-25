"""Executive report summarization with the local Ollama model."""

import json
import logging
from typing import Any
from urllib.request import Request, urlopen

from report.config import (
    ollama_base_url,
    ollama_model,
    ollama_timeout_seconds,
)
from report.state import ReportState

logger = logging.getLogger(__name__)


_SUMMARY_SCHEMA = {
    "type": "object",
    "properties": {
        "narrative": {
            "type": "string",
            "maxLength": 600,
        },
        "insights": {
            "type": "array",
            "items": {
                "type": "string",
                "maxLength": 180,
            },
            "minItems": 2,
            "maxItems": 3,
        },
    },
    "required": ["narrative", "insights"],
    "additionalProperties": False,
}


def _summary_prompt(
    report_date: str,
    metrics: dict[str, Any],
    top_farms: list[dict[str, Any]],
    sensors: list[dict[str, Any]],
) -> str:
    """Build the bounded prompt used for the executive narrative."""
    return f"""
        Create a concise executive summary for UrbanGreen Analytics for {report_date}.

        Use only the report data provided below.
        Do not invent trends, targets, causes, comparisons, recommendations,
        or missing context.

        Headline metric meanings:
        - total_harvest_yield_kg: kilograms harvested.
        - total_energy_kwh: total energy consumption in kWh.
        - energy_efficiency_kwh_per_kg: kWh per kg; lower is better.
        - waste_reduction_progress: non-premium yield share; lower is better.
        - environmental_compliance_rate: in-range sensor share; higher is better.
        - sensor_anomaly_rate: anomalous sensor share; lower is better.
        - reporting_farms: number of farms represented in the daily aggregate.

        Additional data:
        - Top farms come from the precomputed farm leaderboard.
        - A lower composite rank number represents a higher leaderboard position.
        - Sensor rows are daily aggregates grouped by sensor type.
        - anomaly_rate and compliance_rate are ratios between 0 and 1.

        Rules:
        - If a value is null, describe it as unavailable rather than zero.
        - Do not describe reporting_farms as active farms.
        - Do not infer why a metric is high, low, zero, or unavailable.
        - Do not claim a trend unless trend data is explicitly provided.
        - Mention top-farm or sensor information only when it is present below.
        - Keep the language factual, concise, and suitable for an executive report.

        Write:
        - a 2-3 sentence executive narrative
        - 2-3 short insight bullets highlighting the most useful facts

        Headline KPIs:
        {json.dumps(metrics, indent=2)}

        Top farms:
        {json.dumps(top_farms, indent=2)}

        Sensor overview:
        {json.dumps(sensors, indent=2)}
    """.strip()


def summarize_metrics(
    state: ReportState,
    model=ollama_model(),
) -> dict[str, Any]:
    """Ask the local Ollama model for a concise structured summary."""
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": _summary_prompt(
                    state["report_date"],
                    state["metrics"],
                    state.get("top_farms", []),
                    state.get("sensors", []),
                ),
            }
        ],
        "format": _SUMMARY_SCHEMA,
        "stream": False,
        "think": False,
        "options": {
            "temperature": 0.2,
            "seed": 42,
            "num_predict": 220,
        },
    }

    request = Request(
        f"{ollama_base_url()}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urlopen(
        request,
        timeout=ollama_timeout_seconds(),
    ) as response:
        body = json.loads(response.read().decode("utf-8"))

    summary = json.loads(body["message"]["content"])

    narrative = summary["narrative"].strip()

    insights = [item.strip() for item in summary["insights"] if item.strip()]

    if not narrative or len(insights) < 2:
        raise ValueError("Ollama returned an incomplete executive summary.")

    logger.info(f"Generated executive summary with {model}.")

    return {"narrative": narrative, "insights": insights[:3]}
