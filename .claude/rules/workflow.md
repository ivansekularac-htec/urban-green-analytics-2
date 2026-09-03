# Workflow

How Python dependencies are owned in this repo. Test style lives in
`.claude/rules/testing.md`; this file is only about *where a package is
declared*.

## Root `pyproject.toml` is the Airflow/reports local env

The root manifest exists so `etl/dags/` and `reports/` can run
`uv run pytest` from the repo root without an Airflow container.
`[tool.pytest.ini_options] testpaths` is `tests/reports`.

It tracks `infra/airflow/requirements.txt` with two deliberate omissions
that ship in the images, not via pip in this venv:

- `apache-airflow`
- `pyspark`

Do not "complete" the mirror by adding those. Do not add a package here
unless `etl/dags/` or `reports/` actually imports it.

## This is not a per-service dependency rollup

`api/` and `mcp/` each own runtime deps in their own `pyproject.toml`
and `uv.lock`. CI (`uv sync --frozen`) and each service Dockerfile use
those files only.

Do not duplicate `api/` or `mcp/` packages into the root manifest. Do
not invent `# api/` or `# mcp/` comment blocks here — they would look
like a contract and then drift.

## Adding a Python dependency

1. From the service directory that imports the package (`api/`, `mcp/`,
   or the repo root for reports/DAGs), add it to **that** `pyproject.toml`
   (`uv add <package>` or an explicit pin, matching how neighbours are
   specified).
2. Refresh **that** service's lock with `uv lock`. Never hand-edit a
   `uv.lock`.
3. If the import is in `etl/dags/` or `reports/`, update
   `infra/airflow/requirements.txt` in the same change as the root
   `pyproject.toml`.
4. Before the PR, in that service directory: `uv run pytest`,
   `uv run ruff check`, `uv run ruff format --check`.