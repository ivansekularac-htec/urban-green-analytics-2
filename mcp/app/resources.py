"""Model-facing Markdown resources for the UrbanGreen warehouse.

This module contains no FastMCP registration. It only builds the text returned
by the schema, metrics, and conventions resources; the MCP server can expose
these functions under stable resource URIs in a later integration ticket.
"""

from functools import lru_cache
from pathlib import Path

from clickhouse_connect.driver.client import Client

from app.clickhouse import get_client

WAREHOUSE_DATABASE = "urbangreen_dw"
INTERNAL_TABLE_PREFIX = ".inner"

RESOURCE_DOCS = Path(__file__).with_name("resource_docs")


def _load_table_ddls(client: Client) -> list[tuple[str, str]]:
    """Return visible warehouse table names and their live ClickHouse DDL."""
    tables_result = client.query(
        """
        SELECT name
        FROM system.tables
        WHERE database = {database:String}
        AND NOT startsWith(name, {internal_prefix:String})
        ORDER BY name
        """,
        parameters={
            "database": WAREHOUSE_DATABASE,
            "internal_prefix": INTERNAL_TABLE_PREFIX,
        },
    )

    # Keep the Python-side guard as a second line of defence. It also protects
    # callers using a ClickHouse version or test double that does not apply the
    # startsWith predicate as expected.
    table_names = [
        row[0] for row in tables_result.result_rows if not row[0].startswith(INTERNAL_TABLE_PREFIX)
    ]

    table_ddls = []
    for table_name in table_names:
        ddl_result = client.query(
            "SHOW CREATE TABLE {database:Identifier}.{table:Identifier}",
            parameters={
                "database": WAREHOUSE_DATABASE,
                "table": table_name,
            },
        )

        if not ddl_result.result_rows:
            raise RuntimeError(
                f"ClickHouse returned no DDL for '{WAREHOUSE_DATABASE}.{table_name}'."
            )

        table_ddls.append((table_name, ddl_result.result_rows[0][0]))

    return table_ddls


def _render_schema_markdown(table_ddls: list[tuple[str, str]]) -> str:
    """Render table names and DDL statements as deterministic Markdown."""
    sections = [
        "# UrbanGreen ClickHouse schema",
        "",
        f"Database: `{WAREHOUSE_DATABASE}`",
        "",
        "The definitions below are read from ClickHouse at runtime. Internal "
        "materialized-view storage tables are omitted.",
    ]

    if not table_ddls:
        sections.extend(["", "No user-visible tables were found."])

    for table_name, ddl in table_ddls:
        sections.extend(
            [
                "",
                f"## `{table_name}`",
                "",
                "```sql",
                ddl.strip(),
                "```",
            ]
        )

    return "\n".join(sections) + "\n"


@lru_cache(maxsize=1)
def get_schema_markdown() -> str:
    """Build the live warehouse schema once, then reuse it for this process."""
    return _render_schema_markdown(_load_table_ddls(get_client()))


def get_metrics_markdown() -> str:
    """Return canonical KPI definitions for the current warehouse design."""
    return (RESOURCE_DOCS / "metrics.md").read_text(encoding="utf-8")


def get_conventions_markdown() -> str:
    """Return warehouse rules that cannot be inferred reliably from DDL."""
    return (RESOURCE_DOCS / "conventions.md").read_text(encoding="utf-8")
