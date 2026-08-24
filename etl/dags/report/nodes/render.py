"""Third node: render the figures and narrative into one self-contained document.

The layout is a fixed Jinja template; the model's text and the warehouse figures
are injected into it, never the other way round, so every report looks the same
and a model that emits markup cannot change the page. Jinja autoescaping escapes
every injected value. The CSS and the small icons live in the template, and there
are no external assets, so the file opens on its own.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from report.deps import ReportDeps
from report.nodes.summarize import SOURCE_MODEL
from report.state import ReportState

__all__ = ["render_html", "make_render"]

_TEMPLATES_DIR = Path(__file__).parents[1] / "templates"

_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "j2"]),
    trim_blocks=True,
    lstrip_blocks=True,
)
_template = _env.get_template("report.html.j2")


def _num(value: object, digits: int = 2) -> str:
    """Format a figure for display, or an em dash where there is none."""
    if value is None:
        return "—"
    if isinstance(value, (int, Decimal, float)):
        return f"{float(value):,.{digits}f}"
    return str(value)


def _pct(value: object) -> str:
    """Render a 0..1 ratio as a percentage, or an em dash for a missing one."""
    if value is None:
        return "—"
    return f"{float(value) * 100:.1f}%"


def _kpi_cards(kpis: dict, totals: dict) -> list[dict]:
    """The eight headline cards, formatted for display."""
    return [
        {
            "label": "Active farms",
            "value": _num(kpis.get("active_farms"), 0),
            "unit": "",
        },
        {"label": "Harvests", "value": _num(totals.get("harvests"), 0), "unit": ""},
        {
            "label": "Total yield",
            "value": _num(totals.get("total_yield_kg")),
            "unit": "kg",
        },
        {
            "label": "Energy used",
            "value": _num(totals.get("total_energy_kwh")),
            "unit": "kWh",
        },
        {
            "label": "Energy per kg",
            "value": _num(totals.get("energy_efficiency_kwh_per_kg"), 2),
            "unit": "kWh/kg",
        },
        {
            "label": "Compliance rate",
            "value": _pct(totals.get("compliance_rate")),
            "unit": "",
        },
        {
            "label": "Non-premium share",
            "value": _pct(totals.get("non_premium_share")),
            "unit": "",
        },
        {
            "label": "Anomaly rate",
            "value": _pct(totals.get("anomaly_rate")),
            "unit": "",
        },
    ]


def _farm_rows(top_farms: list[dict]) -> list[dict]:
    return [
        {
            "rank": _num(row.get("rank"), 0),
            "farm": row.get("farm", ""),
            "city": row.get("city", ""),
            "yield": f"{_num(row.get('total_yield_kg'))} kg",
            "premium": _pct(row.get("premium_yield_share")),
        }
        for row in top_farms
    ]


def _sensor_rows(sensors: list[dict]) -> list[dict]:
    return [
        {
            "type": row.get("sensor_type", ""),
            "unit": row.get("unit", ""),
            "readings": _num(row.get("readings"), 0),
            "anomalies": _num(row.get("anomalies"), 0),
        }
        for row in sensors
    ]


def render_html(state: ReportState, generated_at: str | None = None) -> str:
    """Render the full report as a self-contained HTML string.

    Pure apart from the generated-at stamp: given a state it returns the
    document with no I/O, so the escaping and the self-contained requirement are
    both testable directly.
    """
    kpis = state["kpis"]
    totals = kpis.get("totals") or {}

    if generated_at is None:
        generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    footer_note = (
        "the summary was written by the local model"
        if state.get("summary_source") == SOURCE_MODEL
        else "the summary is a generated fallback; the model did not respond"
    )

    return _template.render(
        report_date=str(kpis.get("report_date", "")),
        generated_at=generated_at,
        narrative=state.get("narrative") or "No narrative available.",
        insights=state.get("insights", []),
        kpis=_kpi_cards(kpis, totals),
        top_farms=_farm_rows(kpis.get("top_farms") or []),
        sensors=_sensor_rows(kpis.get("sensors") or []),
        footer_note=footer_note,
    )


def make_render(_deps: ReportDeps) -> Callable[[ReportState], dict]:
    """Build the render node. It needs nothing from deps; the signature matches
    the others so the graph wires them the same way."""

    def render(state: ReportState) -> dict:
        return {"html": render_html(state)}

    return render
