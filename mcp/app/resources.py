"""Markdown knowledge resources for ClickHouse SQL generation."""

from pathlib import Path
from typing import Literal

from clickhouse_connect.driver.client import Client

_RESOURCE_DOCS_DIR = Path(__file__).with_name("resource_docs")

# The URIs these resources are published under. They live beside the resources
# themselves so the prompts, which tell the model what to read, and the server
# registration, which decides what is readable, cannot drift apart.
SCHEMA_URI = "urbangreen://schema"
METRICS_URI = "urbangreen://metrics"
CONVENTIONS_URI = "urbangreen://conventions"

type WarehouseResourceName = Literal["schema", "metrics", "conventions"]

# The model-facing reader accepts stable names rather than arbitrary URIs. The
# mapping stays beside the URI constants so registration and tool access cannot
# disagree about which resource a name identifies.
RESOURCE_URIS: dict[WarehouseResourceName, str] = {
    "schema": SCHEMA_URI,
    "metrics": METRICS_URI,
    "conventions": CONVENTIONS_URI,
}

_SCHEMA_TABLES_SQL = """
SELECT name, create_table_query
FROM system.tables
WHERE database = {database:String}
  AND NOT startsWith(name, '.inner')
ORDER BY name
"""


def load_schema_markdown(client: Client, database: str) -> str:
    """Introspect ClickHouse and render the warehouse schema as Markdown."""

    result = client.query(
        _SCHEMA_TABLES_SQL,
        parameters={"database": database},
    )

    return render_schema_markdown(database, result.result_rows)


def render_schema_markdown(database: str, table_ddls: list[tuple[str, str]]) -> str:
    """Render already-loaded table DDL as Markdown without external I/O."""

    sections = [
        "# UrbanGreen ClickHouse schema",
        "",
        f"Database: `{database}`",
        "",
    ]

    for table_name, ddl in table_ddls:
        sections.extend(
            [
                f"## `{table_name}`",
                "",
                "```sql",
                ddl.strip(),
                "```",
                "",
            ]
        )

    return "\n".join(sections).rstrip() + "\n"


def metrics_resource() -> str:
    """Return the canonical warehouse metric definitions."""

    return METRICS_MARKDOWN


def conventions_resource() -> str:
    """Return ClickHouse rules that cannot be inferred from DDL alone."""

    return CONVENTIONS_MARKDOWN


def _read_resource_doc(filename: str) -> str:
    """Read a bundled static Markdown resource as UTF-8 text."""

    return (_RESOURCE_DOCS_DIR / filename).read_text(encoding="utf-8")


# Load static documents once at import time. The public resource functions
# remain deterministic and perform no file I/O when MCP reads them.
METRICS_MARKDOWN = _read_resource_doc("metrics.md")
CONVENTIONS_MARKDOWN = _read_resource_doc("conventions.md")
