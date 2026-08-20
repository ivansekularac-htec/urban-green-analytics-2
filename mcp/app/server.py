"""The FastMCP server: one factory that wires everything together.

`create_server` is where the parts built in earlier tickets meet. It takes the
ClickHouse client, falling back to opening one, and hands it to everything that
needs it - so the tool functions stay pure, the client is not fetched again on
every call, and a test passes a double instead of patching a module lookup.

The schema is the one resource that needs that client, and its cache lives here
rather than in `app.resources` for the same reason. A cache on a module-level
function is process-wide state: it outlives the server that filled it, so a test
has to remember to clear it and a failing test leaks a stale warehouse into
every test after it. Built inside the factory, the cache belongs to the server
and goes when it does.

The tools are registered as thin wrappers rather than directly. `@mcp.tool`
turns every parameter of the decorated function into a field the model is asked
to fill, and `app.tools` functions take a `client` the model cannot supply and
row limits that are this service's policy rather than the model's choice. The
wrappers close over both and expose only `sql`, `table`, `database` and
`limit`; their docstrings are what the model reads as the tool description.

Resources and prompts need no wrapper - their signatures are already the ones
the model should see, which is why the prompts are named for the slash command
rather than for the module.

Both do need a second channel, though. Under MCP a resource is read by the
client and a prompt is chosen by the user, so neither is something the model can
reach for, and the clients this server is used with offer neither. Registration
alone would leave the conventions unread and the templates unused.
`read_resource` and `get_prompt` put the same content behind a call the model
can make. Each reads the registry the registration loop reads rather than
repeating the names, so the two channels cannot come apart, and each answers a
bad argument with what it does accept instead of failing the turn.

One tool each rather than FastMCP's transforms, which add a `list_*` alongside
every `get_*`. The names are already in the instructions, so the listing tools
would spend two entries of a small model's attention on something it has been
told.

`get_prompt` takes its arguments as an object or as the JSON text of one. The
published schema says object, but a client that flattens a nested schema sends
the text instead, and that has been seen from a real one - so the alternative to
accepting it is refusing a call that carried everything needed.

Two log lines, in the shape `etl/transformations` uses: the outcome of building
the server, and a warning when a tool hands back an error. `execute_query`
deliberately returns a ClickHouse failure as a payload so the model can correct
itself, which means without that line a failing query would leave no trace in
`docker logs` at all.
"""

import inspect
import json
import logging
from functools import lru_cache

from clickhouse_connect.driver.client import Client
from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from app import prompts, resources, tools
from app.clickhouse import get_client
from app.config import get_settings
from app.resources import CONVENTIONS_URI, METRICS_URI, SCHEMA_URI

logger = logging.getLogger(__name__)

SERVER_NAME = "UrbanGreen MCP"

_PROMPTS = {
    "analyze_metric": prompts.analyze_metric,
    "compare_farms": prompts.compare_farms,
    "investigate_anomaly": prompts.investigate_anomaly,
}

# Named from the registry above so the instructions cannot list a prompt the
# server does not serve.
INSTRUCTIONS = f"""Read-only access to the Urban Green ClickHouse warehouse.

Call read_resource with {CONVENTIONS_URI} before the first query of a session.
It carries the rules that change the numbers, such as which tables must be read
with FINAL and which column a fact joins to a dimension on. Take any named
metric from {METRICS_URI} rather than deriving a formula, and read {SCHEMA_URI}
for the live DDL of every table. All three are read through read_resource.

Work from list_tables to describe_table to execute_query. Queries run in a
read-only session and are rewritten to carry a row limit, so a result can come
back cut short - the payload says when it did, and a total taken from it is not
the whole total.

Three prompts hold the procedure for the questions they name:
{", ".join(_PROMPTS)}. When one of them fits, call get_prompt for it before
anything else and follow what it returns."""


def _reported(tool_name: str, payload: dict) -> dict:
    """Log a tool failure the model is allowed to recover from, then return it."""
    if "error" in payload:
        logger.warning(f"{tool_name} returned an error: {payload['error']}")

    return payload


def _accepted(template) -> str:
    """Name a template's parameters, so a rejected call says what would work."""
    return ", ".join(inspect.signature(template).parameters)


def create_server(client: Client | None = None) -> FastMCP:
    """Build the FastMCP instance with every tool, resource and prompt attached.

    Args:
        client: The ClickHouse client every database-backed part shares. One is
            opened when it is not given, which is what `main` relies on.
    """
    settings = get_settings()
    client = get_client() if client is None else client
    warehouse = settings.clickhouse_db

    mcp = FastMCP(name=SERVER_NAME, instructions=INSTRUCTIONS)

    @lru_cache(maxsize=1)
    def schema_resource() -> str:
        """Return the live DDL of every table in the warehouse."""
        logger.info(f"reading the schema of {warehouse}")

        return resources.load_schema_markdown(client, warehouse)

    resource_readers = {
        SCHEMA_URI: schema_resource,
        METRICS_URI: resources.metrics_resource,
        CONVENTIONS_URI: resources.conventions_resource,
    }

    @mcp.custom_route("/health", methods=["GET"])
    async def health_check(_request: Request) -> JSONResponse:
        """Unauthenticated liveness probe for the compose healthcheck."""
        return JSONResponse({"status": "healthy"})

    @mcp.tool
    def read_resource(uri: str) -> dict:
        """Read one of the server's knowledge resources and return its Markdown.

        The URIs are named in the server instructions. Passing one that is not
        served returns the list of those that are, so a wrong guess costs one
        call rather than the answer.
        """
        read = resource_readers.get(uri)

        if read is None:
            return _reported(
                "read_resource",
                {"error": f"no resource at {uri}, served: {sorted(resource_readers)}"},
            )

        return {"uri": uri, "content": read()}

    @mcp.tool
    def get_prompt(name: str, arguments: dict | str | None = None) -> dict:
        """Render one of the server's prompt templates into a procedure to follow.

        The names are given in the server instructions. A name that is not
        served, or arguments a template does not take, comes back with what
        would have worked. `arguments` is an object of parameter names, or the
        JSON text of one.
        """
        template = _PROMPTS.get(name)

        if template is None:
            return _reported(
                "get_prompt",
                {"error": f"no prompt named {name}, served: {sorted(_PROMPTS)}"},
            )

        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError as exc:
                return _reported("get_prompt", {"error": f"arguments is not JSON: {exc}"})

        if arguments is not None and not isinstance(arguments, dict):
            return _reported(
                "get_prompt",
                {"error": f"arguments must name parameters, got {type(arguments).__name__}"},
            )

        try:
            rendered = template(**(arguments or {}))
        except TypeError as exc:
            return _reported(
                "get_prompt",
                {"error": f"{name} takes {_accepted(template)}: {exc}"},
            )

        return {"name": name, "prompt": rendered}

    @mcp.tool
    def list_tables(database: str = warehouse) -> dict:
        """List the tables and views in a warehouse database."""
        return _reported("list_tables", tools.list_tables(client, database))

    @mcp.tool
    def describe_table(table: str, database: str = warehouse) -> dict:
        """Return the columns of a table with their types, defaults and comments."""
        return _reported("describe_table", tools.describe_table(client, table, database))

    @mcp.tool
    def execute_query(sql: str, limit: int | None = None) -> dict:
        """Run one read-only SELECT and return its rows.

        The statement is checked and rewritten to carry a row limit before it
        runs. Pass `limit` to ask for fewer rows than the service default; it
        cannot raise the ceiling.
        """
        return _reported(
            "execute_query",
            tools.execute_query(
                client,
                sql,
                default_limit=settings.default_row_limit,
                max_limit=settings.max_row_limit,
                limit=limit,
            ),
        )

    registered_tools = (
        read_resource,
        get_prompt,
        list_tables,
        describe_table,
        execute_query,
    )

    for uri, read in resource_readers.items():
        mcp.resource(uri)(read)

    for prompt in _PROMPTS.values():
        mcp.prompt(prompt)

    logger.info(
        f"registered {len(registered_tools)} tool(s), "
        f"{len(resource_readers)} resource(s), {len(_PROMPTS)} prompt(s) "
        f"against {warehouse}"
    )

    return mcp
