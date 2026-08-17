"""
Static knowledge resources exposed to the model.

Each function returns markdown that an LLM reads before writing SQL: the live
warehouse DDL, the canonical metric definitions, and the query conventions the
DDL cannot express. They are plain functions so they can be tested directly;
the MCP layer wraps them as ``urbangreen://`` resources separately.
"""

from functools import cache, lru_cache
from pathlib import Path

from clickhouse_connect.driver.client import Client
from clickhouse_connect.driver.exceptions import ClickHouseError

SCHEMA_DATABASE = "urbangreen_dw"

CONTENT_DIRECTORY = Path(__file__).parent / "content"

# ClickHouse stores the data behind a materialized view in a companion table
# named `.inner.<view>` or `.inner_id.<uuid>`. Those are an implementation
# detail of the view and only add noise to the schema the model reads.
INTERNAL_TABLE_PREFIX = ".inner"

_SCHEMA_QUERY = """
SELECT
    name,
    create_table_query
FROM system.tables
WHERE database = {database:String}
AND NOT startsWith(name, {internal_prefix:String})
ORDER BY name
"""


def render_schema(client: Client) -> str:
    """
    Return the live warehouse DDL as markdown.

    The schema is read from the server rather than hard-coded so it cannot
    drift from the tables that actually exist. It is built on first read and
    kept for the life of the process, because the schema does not change while
    the stack is up.

    Args:
        client: ClickHouse client used to introspect the warehouse.

    Returns:
        Markdown listing every warehouse table with its ``CREATE TABLE``
        statement, or a short markdown notice when the schema cannot be read.
    """
    try:
        return _load_schema(client)
    except ClickHouseError as exc:
        # Deliberately outside the cached call: lru_cache does not store
        # exceptions, so a transient ClickHouse failure is retried on the next
        # read instead of being frozen in for the life of the process.
        return f"# Warehouse schema\n\nThe schema could not be read from ClickHouse: {exc}\n"


def render_metrics() -> str:
    """
    Return the canonical metric definitions as markdown.

    Returns:
        Markdown describing each dashboard metric and the query it is computed
        from.
    """
    return _read_content("metrics.md")


def render_conventions() -> str:
    """
    Return the query conventions as markdown.

    Returns:
        Markdown describing the rules that span more than one table, such as
        joining a fact to the dimension version valid at the time and joining
        on ``*_id`` rather than ``*_key``. Facts about a single table or column
        belong in that object's ``COMMENT`` and reach the model through the
        schema resource instead.
    """
    return _read_content("conventions.md")


@lru_cache(maxsize=1)
def _load_schema(client: Client) -> str:
    """
    Introspect the warehouse and render its DDL as markdown.

    Args:
        client: ClickHouse client used to introspect the warehouse.

    Returns:
        Markdown listing every warehouse table with its ``CREATE TABLE``
        statement.

    Raises:
        ClickHouseError: If the introspection query fails.
    """
    result = client.query(
        _SCHEMA_QUERY,
        parameters={
            "database": SCHEMA_DATABASE,
            "internal_prefix": INTERNAL_TABLE_PREFIX,
        },
    )

    sections = [
        "# Warehouse schema\n",
        f"Database `{SCHEMA_DATABASE}`, read from the live server.\n",
    ]

    for name, create_table_query in result.result_rows:
        sections.append(f"## {name}\n")
        sections.append(f"```sql\n{create_table_query}\n```\n")

    return "\n".join(sections)


@cache
def _read_content(filename: str) -> str:
    """
    Read a markdown document that ships with the service.

    Args:
        filename: Name of the file inside the content directory.

    Returns:
        The file contents.
    """
    return (CONTENT_DIRECTORY / filename).read_text(encoding="utf-8")
