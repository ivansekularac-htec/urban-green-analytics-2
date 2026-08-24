"""Second node: the local model writes a short narrative around the figures.

The model is given the numbers and asked only for prose. It never produces a
figure the report shows and never produces HTML. Output length is bounded on the
Ollama call itself (`num_predict`) rather than requested in the prompt, so a run
finishes predictably whatever the model does.

When the call fails or comes back empty, a deterministic fallback narrative is
built from the same figures and `summary_source` is set to `fallback`, so a
degraded run is visible in the state, the footer and the log rather than looking
identical to a real one.
"""

from __future__ import annotations

import json
import logging
import re
import urllib.error
import urllib.request
from collections.abc import Callable

from report.deps import OllamaConfig, ReportDeps
from report.state import ReportState

logger = logging.getLogger(__name__)

SOURCE_MODEL = "model"
SOURCE_FALLBACK = "fallback"

_SYSTEM = (
    "You write a short executive summary for a daily vertical-farming report. "
    "Use only the figures you are given. Do not state any number that is not in "
    "the list, and repeat counts such as the number of active farms exactly as "
    "given - never round them or make them up. Do not write HTML. Reply with two "
    "or three sentences of narrative, then three lines each starting with '- ' "
    "giving one insight each."
)


def _fmt(value: object) -> str:
    """Render a figure for the prompt, leaving a gap where there is none."""
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def build_prompt(kpis: dict) -> str:
    """Turn the KPI dict into the user message the model summarises.

    Pure: the same figures produce the same prompt, so the prompt can be
    asserted in a test without a model.
    """
    totals = kpis.get("totals") or {}
    lines = [
        f"Date: {kpis.get('report_date')}",
        f"Active farms: {_fmt(kpis.get('active_farms'))}",
        f"Total yield (kg): {_fmt(totals.get('total_yield_kg'))}",
        f"Total energy (kWh): {_fmt(totals.get('total_energy_kwh'))}",
        f"Energy efficiency (kWh/kg): {_fmt(totals.get('energy_efficiency_kwh_per_kg'))}",
        f"Non-premium share: {_fmt(totals.get('non_premium_share'))}",
        f"Compliance rate: {_fmt(totals.get('compliance_rate'))}",
    ]

    top = kpis.get("top_farms") or []
    if top:
        leaders = ", ".join(f"{row['farm']} ({row['city']})" for row in top[:3])
        lines.append(f"Top farms by composite rank: {leaders}")

    return "\n".join(lines)


_THINK_BLOCK = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)


def strip_reasoning(text: str) -> str:
    """Remove a reasoning model's `<think>...</think>` block from its reply.

    Qwen3 emits its chain of thought inside such a block before the answer.
    Left in, it would become the narrative; removed, only the answer remains.
    An unclosed block (the reply was cut off mid-thought) leaves nothing, which
    then reads as an empty narrative and falls back - the right outcome.
    """
    without_closed = _THINK_BLOCK.sub("", text)
    # Drop an unclosed trailing block, e.g. a reply truncated inside <think>.
    open_at = without_closed.lower().find("<think>")
    if open_at != -1:
        without_closed = without_closed[:open_at]

    return without_closed.strip()


def parse_summary(text: str) -> tuple[str, list[str]]:
    """Split the model's reply into a narrative and insight bullets.

    Lines that start with a bullet marker are insights; the rest join into the
    narrative. Robust to a model that omits bullets or adds noise.
    """
    narrative_parts: list[str] = []
    insights: list[str] = []

    for raw in strip_reasoning(text).splitlines():
        line = raw.strip()
        if not line:
            continue
        if line[0] in "-*•":
            insights.append(line.lstrip("-*• ").strip())
        else:
            narrative_parts.append(line)

    return " ".join(narrative_parts).strip(), insights


def fallback_summary(kpis: dict) -> tuple[str, list[str]]:
    """Build a narrative from the figures when the model is unavailable."""
    totals = kpis.get("totals") or {}

    if not kpis.get("has_data"):
        return (
            f"No warehouse metrics were loaded for {kpis.get('report_date')}, "
            "so this report has no figures to summarise.",
            [],
        )

    narrative = (
        f"On {kpis.get('report_date')}, {_fmt(kpis.get('active_farms'))} active farms produced "
        f"{_fmt(totals.get('total_yield_kg'))} kg of yield using "
        f"{_fmt(totals.get('total_energy_kwh'))} kWh of energy."
    )
    insights = [
        f"Energy efficiency: {_fmt(totals.get('energy_efficiency_kwh_per_kg'))} kWh/kg.",
        f"Compliance rate: {_fmt(totals.get('compliance_rate'))}.",
        f"Non-premium share: {_fmt(totals.get('non_premium_share'))}.",
    ]
    return narrative, insights


def call_ollama(config: OllamaConfig, prompt: str) -> str:
    """POST one prompt to Ollama and return the generated text.

    Raises on any transport or protocol failure, so the caller can fall back.
    Output is bounded by `num_predict` on the request, not by asking for it.
    """
    payload = json.dumps(
        {
            "model": config.model,
            "prompt": prompt,
            "system": _SYSTEM,
            "stream": False,
            # A reasoning model (Qwen3) otherwise spends the whole token budget
            # thinking and emits no answer; `think: false` makes it reply
            # directly. Ignored by non-reasoning models.
            "think": False,
            "options": {"num_predict": config.num_predict, "temperature": 0.2},
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        f"http://{config.host}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=config.timeout_seconds) as response:
        body = json.loads(response.read().decode("utf-8"))

    return body.get("response", "").strip()


def make_summarize(deps: ReportDeps) -> Callable[[ReportState], dict]:
    """Build the summarization node against an Ollama config."""

    def summarize(state: ReportState) -> dict:
        kpis = state["kpis"]
        prompt = build_prompt(kpis)

        try:
            text = call_ollama(deps.ollama, prompt)
            narrative, insights = parse_summary(text)
            if not narrative:
                raise ValueError("model returned no narrative")
        except (
            urllib.error.URLError,
            TimeoutError,
            ValueError,
            OSError,
            json.JSONDecodeError,
        ) as exc:
            logger.warning(f"summarization fell back to a fixed narrative: {exc}")
            narrative, insights = fallback_summary(kpis)
            return {
                "narrative": narrative,
                "insights": insights,
                "summary_source": SOURCE_FALLBACK,
            }

        logger.info("summarization used the model")
        return {
            "narrative": narrative,
            "insights": insights,
            "summary_source": SOURCE_MODEL,
        }

    return summarize
