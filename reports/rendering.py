"""Render the executive report as a self-contained HTML document."""

import logging
from functools import lru_cache
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from reports.models import ReportState

logger = logging.getLogger(__name__)

TEMPLATE_DIRECTORY = Path(__file__).with_name("templates")
TEMPLATE_NAME = "executive_report.html.j2"


def format_number(value: float | int | None, decimals: int = 2) -> str:
    """Format a KPI number or mark an unavailable measurement."""

    if value is None:
        return "Not measured"
    return f"{value:,.{decimals}f}"


def format_integer(value: int | None) -> str:
    """Format an integer KPI."""

    return "Not measured" if value is None else f"{value:,}"


def format_percent(value: float | None) -> str:
    """Format a ratio as a percentage."""

    return "Not measured" if value is None else f"{value * 100:.2f}%"


@lru_cache(maxsize=1)
def get_template_environment() -> Environment:
    """Create the strict, autoescaping Jinja environment once."""

    environment = Environment(
        loader=FileSystemLoader(TEMPLATE_DIRECTORY),
        autoescape=select_autoescape(
            enabled_extensions=("html", "j2"),
            default_for_string=True,
        ),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    environment.filters.update(
        integer=format_integer,
        number=format_number,
        percent=format_percent,
    )
    return environment


def render_html(state: ReportState) -> dict[str, str]:
    """Inject authoritative KPI values and model prose into the template."""

    report_date = state["report_date"]
    logger.info("Rendering executive report HTML for %s", report_date)

    template = get_template_environment().get_template(TEMPLATE_NAME)
    html = template.render(
        report_date=report_date,
        metrics=state["metrics"],
        top_farms=state["top_farms"],
        narrative=state["summary"].narrative,
        insights=state["summary"].insights,
    )
    return {"html": html}
