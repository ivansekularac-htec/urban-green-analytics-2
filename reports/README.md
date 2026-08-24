# UrbanGreen executive reports

This package builds the daily executive report independently from its schedule.
The fixed four-stage LangGraph is:

```text
retrieve_metrics -> summarize_metrics -> render_html -> publish_report
```

The model writes only a bounded narrative and three or four insight bullets.
Authoritative KPI values are read from ClickHouse and injected with the model
text into `templates/executive_report.html.j2`; the model never generates HTML.

## Delivery

Every successful run writes the report to the MinIO `staging` bucket at:

```text
reports/executive/date=YYYY-MM-DD/report.html
```

The same date always produces the same key, so reruns overwrite rather than
duplicate the object. The rendered HTML is also sent to the local Mailpit inbox.

- MinIO console: `http://localhost:9001`
- Mailpit inbox: `http://localhost:8025`

## Run without Airflow

With ClickHouse, Ollama, MinIO, and Mailpit available, run:

```bash
uv run python -m reports.pipeline --date 2026-08-15
```

When running from the host rather than the compose network, override service
addresses such as `OLLAMA_HOST`, `CLICKHOUSE_HOST`, `MINIO_ENDPOINT`, and
`SMTP_HOST` to use `localhost`.

## Airflow schedule

`daily_executive_report` runs at 06:00 UTC with catchup disabled. Its only task
uses the run's `logical_date` as the report date. For scheduled runs, Airflow
assigns that date to the start of the completed daily data interval, so no
additional day is subtracted. The task invokes the graph, logs the full S3 URI,
and returns the object key through XCom. Two retries allow a cold local model to
load without turning the first timeout into a lost report.

## Verification

```bash
uv sync --frozen --group dev
uv run ruff check reports tests/reports etl/dags/daily_executive_report.py
uv run ruff format --check reports tests/reports etl/dags/daily_executive_report.py
uv run pytest
docker compose config --quiet
```
