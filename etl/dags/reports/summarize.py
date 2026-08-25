"""Ask the local Ollama model for a short executive briefing."""

from __future__ import annotations

import json
import logging
import os
import re
import urllib.request

from reports.state import ReportState

logger = logging.getLogger(__name__)

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://urbangreen-ollama:11434").rstrip("/")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen3.5:2b")


def _fallback_summary(kpis: dict) -> tuple[str, list[str]]:
    date = kpis.get("report_date", "this date")
    narrative = (
        f"Warehouse snapshot for {date}. "
        "KPI figures in this report are taken from urbangreen_dw. "
        "The language model did not return usable JSON, so this briefing is a fallback."
    )
    insights = [
        f"Farms with activity: {kpis.get('farms_with_activity')}.",
        f"Registered farms: {kpis.get('registered_farms')}.",
        "Open the KPI cards for measured yield, energy, compliance and ranks.",
    ]
    return narrative, insights


def _parse_summary(text: str) -> tuple[str, list[str]] | None:
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    start = cleaned.find("{")
    if start < 0:
        return None
    try:
        payload, _ = json.JSONDecoder().raw_decode(cleaned[start:])
    except json.JSONDecodeError:
        return None
    narrative = str(payload.get("narrative", "")).strip()
    insights = [str(item).strip() for item in payload.get("insights", []) if str(item).strip()]
    if not narrative or not insights:
        return None
    return narrative, insights[:5]


def _ollama_chat(prompt: str) -> str:
    body = json.dumps(
        {
            "model": OLLAMA_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "think": False,
            "options": {"temperature": 0, "num_predict": 512},
        }
    ).encode()
    request = urllib.request.Request(
        f"{OLLAMA_HOST}/api/chat",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        payload = json.loads(response.read().decode())
    message = payload.get("message") or {}
    text = (message.get("content") or message.get("thinking") or "").strip()
    logger.info(
    f"ollama keys={list(message.keys())} chars={len(text)} preview={text[:200]!r}"
    )
    return text


def summarize(state: ReportState) -> dict:
    """Call urbangreen-ollama and return a bounded narrative plus insight bullets."""
    prompt = (
        "You write a daily executive briefing for UrbanGreen urban farms.\n"
        "Use only the KPI JSON below. Do not invent numbers.\n"
        "NULL means the metric could not be measured, not zero.\n"
        "Ratios are fractions in 0..1; say them as percents in prose.\n"
        "Do not put double quotes inside narrative or insight strings.\n"
        "Reply with ONLY JSON: "
        '{"narrative": "2-3 sentences under 80 words", '
        '"insights": ["one sentence", "one sentence", "one sentence"]}\n\n'
        f"{json.dumps(state['kpis'], default=str)}"
    )
    raw = _ollama_chat(prompt)
    parsed = _parse_summary(raw)
    if parsed is None:
        logger.warning("ollama JSON unusable, using fallback briefing")
        narrative, insights = _fallback_summary(state["kpis"])
    else:
        narrative, insights = parsed
    return {"narrative": narrative, "insights": insights}