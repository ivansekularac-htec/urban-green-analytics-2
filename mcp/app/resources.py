"""
Markdown resources for the UrbanGreen MCP service.

Provides the live ClickHouse schema, canonical metric definitions,
and SQL conventions needed by an LLM.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

from clickhouse_connect.driver.client import Client

WAREHOUSE_DATABASE: Final[str] = "urbangreen_dw"
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

    if _schema_cache is None:
        # Cache only a fully successful schema build.
        _schema_cache = _build_schema_markdown(client)

    return _schema_cache


def _build_schema_markdown(client: Client) -> str:
    """Build schema Markdown by introspecting ClickHouse."""
    result = client.query(
        """
        SELECT name
        FROM system.tables
        WHERE database = {database:String}
          AND NOT startsWith(name, {internal_prefix:String})
        ORDER BY name
        """,
        parameters={
            "database": WAREHOUSE_DATABASE,
            "internal_prefix": _INTERNAL_TABLE_PREFIX,
        },
    )

    table_names = [row[0] for row in result.result_rows]

    sections = [
        "# UrbanGreen ClickHouse Schema",
        "",
        f"Live DDL for `{WAREHOUSE_DATABASE}`.",
    ]

    if not table_names:
        sections.extend(
            [
                "",
                "_No warehouse tables were found._",
            ]
        )
        return "\n".join(sections)

    for table_name in table_names:
        ddl = _show_create_table(
            client=client,
            database=WAREHOUSE_DATABASE,
            table=table_name,
        )

        sections.extend(
            [
                "",
                f"## `{WAREHOUSE_DATABASE}.{table_name}`",
                "",
                "```sql",
                ddl,
                "```",
            ]
        )

    return "\n".join(sections)


def _show_create_table(
    client: Client,
    database: str,
    table: str,
) -> str:
    """Return the ClickHouse DDL for one table."""
    qualified_name = f"{_quote_identifier(database)}.{_quote_identifier(table)}"
    ddl = client.command(f"SHOW CREATE TABLE {qualified_name}")

    return str(ddl).strip()


def _quote_identifier(identifier: str) -> str:
    """Quote a ClickHouse identifier with backticks."""
    escaped = identifier.replace("`", "``")
    return f"`{escaped}`"


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
