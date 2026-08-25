"""Fill the self-contained HTML template with KPI figures and the briefing."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from reports.state import ReportState

_TEMPLATES = Path(__file__).resolve().parent / "templates"
_jinja = Environment(
    loader=FileSystemLoader(_TEMPLATES),
    autoescape=select_autoescape(["html"]),
)


def _fmt(value: Any, unit: str = "", percent: bool = False) -> str:
    if value is None:
        return "n/a"
    if percent:
        return f"{float(value) * 100:.1f}%"
    if isinstance(value, float):
        body = f"{value:,.2f}"
    else:
        body = f"{value:,}"
    return f"{body} {unit}".strip()


def render_html(state: ReportState) -> dict:
    """Render the executive report HTML from the shared template."""
    kpis = state["kpis"]
    html = _jinja.get_template("executive_report.html").render(
        report_date=kpis["report_date"],
        cards=[
            {"label": "Total harvest yield", "value": _fmt(kpis.get("total_yield_kg"), "kg")},
            {
                "label": "Yield efficiency",
                "value": _fmt(kpis.get("yield_efficiency_kg_per_m2"), "kg/m²"),
            },
            {"label": "Energy consumed", "value": _fmt(kpis.get("energy_kwh"), "kWh")},
            {
                "label": "Energy efficiency",
                "value": _fmt(kpis.get("energy_efficiency_kwh_per_kg"), "kWh/kg"),
            },
            {
                "label": "Waste (non-premium share)",
                "value": _fmt(kpis.get("waste_reduction_progress"), percent=True),
            },
            {
                "label": "Sensor compliance",
                "value": _fmt(kpis.get("compliance_rate"), percent=True),
            },
            {
                "label": "Sensor anomaly rate",
                "value": _fmt(kpis.get("anomaly_rate"), percent=True),
            },
            {
                "label": "Farm expansion vs 100",
                "value": _fmt(kpis.get("expansion_progress"), percent=True),
            },
        ],
        narrative=state["narrative"],
        insights=state["insights"],
        top_farms=kpis.get("top_farms") or [],
    )
    return {"html": html}
