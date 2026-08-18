"""
Markdown resources for the UrbanGreen MCP service.

Provides the live ClickHouse schema, canonical metric definitions,
and SQL conventions needed by an LLM.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

from clickhouse_connect.driver.client import Client
from clickhouse_connect.driver.exceptions import DatabaseError, OperationalError

from app.config import get_settings

_INTERNAL_TABLE_PREFIX: Final[str] = ".inner"

_RESOURCE_DIR: Final[Path] = Path(__file__).resolve().parent / "resource_docs"

# Schema is static during one process run, so build it once on first access.
_schema_cache: str | None = None


# ---------------------------------------------------------------------------
# Schema resource
# ---------------------------------------------------------------------------


def get_schema_resource(client: Client) -> str:
    """Return the live warehouse schema as cached Markdown."""
    global _schema_cache

    if _schema_cache is not None:
        return _schema_cache

    try:
        schema = _build_schema_markdown(client)
    except (DatabaseError, OperationalError) as exc:
        return (
            "# UrbanGreen ClickHouse Schema\n\n"
            f"_The schema could not be read from ClickHouse: {exc}_"
        )

    _schema_cache = schema
    return _schema_cache


def _build_schema_markdown(client: Client) -> str:
    """Build schema Markdown by introspecting ClickHouse."""
    database = get_settings().clickhouse_db

    result = client.query(
        """
        SELECT
            name,
            create_table_query
        FROM system.tables
        WHERE database = {database:String}
          AND NOT startsWith(name, {internal_prefix:String})
        ORDER BY name
        """,
        parameters={
            "database": database,
            "internal_prefix": _INTERNAL_TABLE_PREFIX,
        },
    )

    sections = [
        "# UrbanGreen ClickHouse Schema",
        "",
        f"Live DDL for `{database}`.",
    ]

    if not result.result_rows:
        sections.extend(
            [
                "",
                "_No warehouse tables were found._",
            ]
        )
        return "\n".join(sections)

    for table_name, ddl in result.result_rows:
        sections.extend(
            [
                "",
                f"## `{database}.{table_name}`",
                "",
                "```sql",
                ddl.strip(),
                "```",
            ]
        )

    return "\n".join(sections)


# ---------------------------------------------------------------------------
# Static Markdown resources
# ---------------------------------------------------------------------------


def get_metrics_resource() -> str:
    """Return canonical UrbanGreen metric definitions."""
    return _read_markdown("metrics.md")


def get_conventions_resource() -> str:
    """Return UrbanGreen ClickHouse query conventions."""
    return _read_markdown("conventions.md")


def _read_markdown(filename: str) -> str:
    """Read a Markdown resource from the resource_docs directory."""
    return (_RESOURCE_DIR / filename).read_text(encoding="utf-8").strip()
