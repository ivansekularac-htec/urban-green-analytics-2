"""Renders the report as one self-contained HTML document.

The layout lives in a template so every day's report has the same shape and
only the values change.
"""

from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

_ENV = Environment(
    loader=FileSystemLoader(Path(__file__).parent / "templates"),
    # Farm names come from user input and the narrative comes from the model.
    # Both land in HTML.
    autoescape=True,
    trim_blocks=True,
    lstrip_blocks=True,
)


def number(value, digits: int = 1) -> str:
    """Format a figure, or say so when there is nothing to show."""

    if value is None:
        return "not measured"

    return f"{value:,.{digits}f}" if isinstance(value, float) else f"{value:,}"


def percent(value, digits: int = 2) -> str:
    """Format a fraction as a percentage."""

    return "not measured" if value is None else f"{value * 100:.{digits}f}%"


_ENV.filters["number"] = number
_ENV.filters["percent"] = percent


def render(metrics: dict, summary: dict) -> str:
    """Return the day's report as one HTML document."""

    return _ENV.get_template("report.html.j2").render(
        metrics=metrics,
        totals=metrics["totals"],
        summary=summary,
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    )
