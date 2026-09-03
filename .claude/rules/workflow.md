# Workflow conventions

## Root `pyproject.toml` mirrors `infra/airflow/requirements.txt` - nothing else

The root `pyproject.toml` exists so the Airflow DAG code (`etl/dags/`,
`reports/`) and its test suite (`tests/reports/`, which is this file's
`testpaths`) can run locally with `uv run pytest` from the repo root,
without a running Airflow container. Its dependency list mirrors
`infra/airflow/requirements.txt` - `apache-airflow` and `pyspark` are
intentionally left out, since those ship via the Airflow/Spark base
images rather than being pip-installed.

**This is not a general per-service dependency mirror.** `api/` and `mcp/`
each own their runtime dependencies entirely in their own
`pyproject.toml` / `uv.lock` - those are not duplicated here. Only add a
package to the root manifest if `etl/dags/` or `reports/` actually imports
it; anything else doesn't belong in this file, however plausible a
comment block might look.

## Adding a Python dependency

- Add it to the owning service's own `pyproject.toml` via `uv add <package>`
  from inside that service's directory (`api/`, `mcp/`, ...). Never hand-edit
  a `uv.lock`.
- Only touch the root `pyproject.toml` if the new import is used by
  `etl/dags/` or `reports/`, and keep `infra/airflow/requirements.txt` in
  sync with it in the same change.
- Run that service's own `uv run pytest`, `uv run ruff check`, and
  `uv run ruff format --check` before opening a PR. Per-service test
  conventions are in `.claude/rules/testing.md`.