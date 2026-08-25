"""HTML rendering for the executive report."""

from pathlib import Path
from typing import Any

from jinja2 import (
    Environment,
    FileSystemLoader,
    StrictUndefined,
    select_autoescape,
)

from report.state import ReportState

_TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
_TEMPLATE_NAME = "executive_report.html"

_TEMPLATE_ENV = Environment(
    loader=FileSystemLoader(_TEMPLATE_DIR),
    autoescape=select_autoescape(["html"]),
    undefined=StrictUndefined,
)


def _format_number(
    value: Any,
    decimals: int = 1,
) -> str:
    """Format a numeric value for display."""
    if value is None:
        return "N/A"

    return f"{float(value):,.{decimals}f}"


def _format_integer(value: Any) -> str:
    """Format an integer count for display."""
    if value is None:
        return "N/A"

    return f"{int(value):,}"


def _format_percent(
    value: Any,
    decimals: int = 1,
) -> str:
    """Format a ratio between 0 and 1 as a percentage."""
    if value is None:
        return "N/A"

    return f"{float(value) * 100:.{decimals}f}%"


def _display_text(value: Any) -> str:
    """Return a safe display value for optional text."""
    if value is None or value == "":
        return "N/A"

    return str(value)


def _kpi_cards(
    metrics: dict[str, Any],
) -> list[dict[str, str]]:
    """Build display-ready cards for the fixed executive KPI set."""
    return [
        {
            "label": "Total Harvest Yield",
            "value": _format_number(metrics.get("total_harvest_yield_kg")),
            "unit": "kg",
            "description": "Harvest recorded for the reporting day",
        },
        {
            "label": "Total Energy Consumption",
            "value": _format_number(metrics.get("total_energy_kwh")),
            "unit": "kWh",
            "description": "Energy consumed across reporting farms",
        },
        {
            "label": "Energy Efficiency",
            "value": _format_number(metrics.get("energy_efficiency_kwh_per_kg"), 2),
            "unit": "kWh/kg",
            "description": "Energy used per kilogram of harvest",
        },
        {
            "label": "Waste Reduction Progress",
            "value": _format_percent(metrics.get("waste_reduction_progress")),
            "unit": "non-premium share",
            "description": "Lower values indicate less non-premium yield",
        },
        {
            "label": "Environmental Compliance",
            "value": _format_percent(metrics.get("environmental_compliance_rate")),
            "unit": "in-range readings",
            "description": "Share of sensor readings within optimal range",
        },
        {
            "label": "Sensor Anomaly Rate",
            "value": _format_percent(metrics.get("sensor_anomaly_rate")),
            "unit": "anomalous readings",
            "description": "Share of readings classified as anomalies",
        },
        {
            "label": "Reporting Farms",
            "value": _format_integer(metrics.get("reporting_farms")),
            "unit": "farms",
            "description": "Farms represented in the daily aggregate",
        },
        {
            "label": "Total Sensor Readings",
            "value": _format_integer(metrics.get("total_sensor_readings")),
            "unit": "readings",
            "description": "Sensor observations processed during the reporting day",
        },
    ]


def _top_farm_rows(
    top_farms: list[dict[str, Any]],
) -> list[dict[str, str]]:
    """Prepare top-farm leaderboard rows for the HTML template."""
    return [
        {
            "rank": _format_integer(farm.get("rank")),
            "farm": _display_text(farm.get("farm")),
            "city": _display_text(farm.get("city")),
            "total_yield_kg": _format_number(farm.get("total_yield_kg")),
            "premium_yield_share": _format_percent(farm.get("premium_yield_share")),
            "energy_efficiency": _format_number(
                farm.get("energy_efficiency_kwh_per_kg"), 2
            ),
        }
        for farm in top_farms
    ]


def _sensor_rows(
    sensors: list[dict[str, Any]],
) -> list[dict[str, str]]:
    """Prepare sensor-type aggregates for the HTML template."""
    return [
        {
            "sensor_type": _display_text(sensor.get("sensor_type")),
            "unit": _display_text(sensor.get("unit")),
            "readings": _format_integer(sensor.get("readings")),
            "anomalies": _format_integer(sensor.get("anomalies")),
            "anomaly_rate": _format_percent(sensor.get("anomaly_rate")),
            "compliance_rate": _format_percent(sensor.get("compliance_rate")),
        }
        for sensor in sensors
    ]


def render_html(
    state: ReportState,
) -> dict[str, str]:
    """Render the report from the fixed HTML template."""
    template = _TEMPLATE_ENV.get_template(_TEMPLATE_NAME)

    html = template.render(
        report_date=state["report_date"],
        kpis=_kpi_cards(state["metrics"]),
        narrative=state["narrative"],
        insights=state["insights"],
        top_farms=_top_farm_rows(state.get("top_farms", [])),
        sensors=_sensor_rows(state.get("sensors", [])),
    )

    return {"html": html}
