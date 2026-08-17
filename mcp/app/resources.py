"""Model-facing Markdown resources for the UrbanGreen warehouse.

This module contains no FastMCP registration. It only builds the text returned
by the schema, metrics, and conventions resources; the MCP server can expose
these functions under stable resource URIs in a later integration ticket.
"""

from pathlib import Path

from clickhouse_connect.driver.client import Client

WAREHOUSE_DATABASE = "urbangreen_dw"
INTERNAL_TABLE_PREFIX = ".inner"

RESOURCE_DOCS = Path(__file__).with_name("resource_docs")


def _load_table_ddls(client: Client) -> list[tuple[str, str]]:
    """Return visible warehouse table names and their live ClickHouse DDL."""
    result = client.query(
        """
        SELECT
            name,
            create_table_query
        FROM system.tables
        WHERE database = {database:String}
        AND name NOT LIKE '.inner%'
        ORDER BY name
        """,
        parameters={"database": WAREHOUSE_DATABASE},
    )

    return [(table_name, ddl) for table_name, ddl in result.result_rows]


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


def build_schema_markdown(client: Client) -> str:
    """Build Markdown from the live warehouse schema."""
    return _render_schema_markdown(_load_table_ddls(client))


def get_metrics_markdown() -> str:
    """Return canonical KPI definitions for the current warehouse design."""
    return (RESOURCE_DOCS / "metrics.md").read_text(encoding="utf-8")


def get_conventions_markdown() -> str:
    """Return warehouse rules that cannot be inferred reliably from DDL."""
    return (RESOURCE_DOCS / "conventions.md").read_text(encoding="utf-8")
