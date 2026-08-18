"""Markdown knowledge resources for ClickHouse SQL generation."""

from functools import lru_cache
from pathlib import Path

from clickhouse_connect.driver.client import Client

from app.clickhouse import get_client
from app.config import get_settings

_RESOURCE_DOCS_DIR = Path(__file__).with_name("resource_docs")

# The URIs these resources are published under. They live beside the resources
# themselves so the prompts, which tell the model what to read, and the T5.2.8
# registration, which decides what is readable, cannot drift apart.
SCHEMA_URI = "urbangreen://schema"
METRICS_URI = "urbangreen://metrics"
CONVENTIONS_URI = "urbangreen://conventions"

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

    # Keep the Python-side check as a defensive guard in case ClickHouse ever
    # returns internal materialized-view storage despite the query predicate.
    table_ddls = [
        (table_name, create_table_query)
        for table_name, create_table_query in result.result_rows
        if not table_name.startswith(".inner")
    ]

    return render_schema_markdown(database, table_ddls)


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


@lru_cache(maxsize=1)
def schema_resource() -> str:
    """Build the schema lazily and cache it for the process lifetime."""

    settings = get_settings()

    return load_schema_markdown(
        client=get_client(),
        database=settings.clickhouse_db,
    )


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
