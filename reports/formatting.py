"""Formatting helpers for executive report values."""


def format_number(value: float | int | None, decimals: int = 2) -> str:
    """Format a numeric KPI."""
    if value is None:
        return "N/A"
    return f"{value:,.{decimals}f}"


def format_integer(value: int | None) -> str:
    """Format an integer KPI."""
    if value is None:
        return "N/A"
    return f"{value:,}"


def format_percent(value: float | None) -> str:
    """Format a ratio as a percentage."""
    if value is None:
        return "N/A"
    return f"{value * 100:.2f}%"
