# UrbanGreen reporting pipeline

Builds the daily executive report: it reads the day's KPIs from the ClickHouse
warehouse, has the local Ollama model write a short narrative, renders one
self-contained HTML document, and publishes it to the MinIO staging bucket and
as an email.

The pipeline is a linear [LangGraph](https://langchain-ai.github.io/langgraph/)
graph:

```
fetch_metrics -> summarize -> render -> publish
```

It runs inside Airflow. `app/` is mounted into the scheduler at
`/opt/airflow/reporting/app` and its dependencies are installed in the Airflow
image, so the `daily_executive_report` DAG imports `run_report` and calls it in
process. There is no separate service and no HTTP hop.

## The model never chooses a number

The KPI queries in `app/metrics.py` are fixed, and every figure in the report
comes from them. The model is given those figures and writes prose about them;
it does not query the warehouse and it does not compute anything.

If the model is slow, unreachable, or answers with something unusable, the run
falls back to a fixed narrative built from the same figures. The report is
published either way, and its footer names which of the two wrote the summary.

## Running it

The report needs ClickHouse and MinIO (`backend`) as well as Ollama and Mailpit
(`analytics`), so it needs both profiles:

```bash
docker compose --profile all up -d
# or, equivalently
docker compose --profile backend --profile analytics up -d
```

Under `--profile backend` alone the DAG parses and runs but has no model and no
mail sink, and the task fails on the fallback narrative.

Trigger the DAG from <http://localhost:8080>, or run one day directly:

```bash
docker compose exec urbangreen-airflow python -m app.main --date 2026-08-15
```

Either way the run reports what it published:

```json
{
  "day": "2026-08-15",
  "key": "reports/executive/date=2026-08-15/report.html",
  "stored": true,
  "emailed": true,
  "summary_source": "qwen3.5:2b",
  "warnings": []
}
```

Re-running the same date overwrites that object rather than adding another:
the key is derived from the date, so there is no path that can duplicate.

## Reading the report

- **Mailpit** — <http://localhost:8025>. The report arrives as an email, which
  is how an executive would receive it.
- **MinIO console** — <http://localhost:9001>, under
  `staging/reports/executive/date=YYYY-MM-DD/report.html`.

## Schedule

The `daily_executive_report` DAG runs at 06:00 and builds the report for its
logical date. The published object key is the task result.

The DAG fails the task, and so retries it, when either the report was not stored
or the summary fell back to the fixed narrative. A green run therefore means
there is an object at the reported key and the model wrote the prose. Retrying
is safe because the key is derived from the date, so a later attempt overwrites
the earlier report rather than adding one. A failed email is logged as a warning
and does not fail the run.

## Local development

The package is tested on its own, without Airflow:

```bash
cd reporting
uv sync --frozen --group dev
uv run ruff check app tests && uv run ruff format --check app tests
uv run pytest
```

To run the pipeline against the containerised stack from the host, copy
`.env.example` to `.env` (it points at `localhost` rather than the container
names) and:

```bash
uv run python -m app.main --date 2026-08-15   # one specific day
uv run python -m app.main                     # the newest loaded day
```

## Notes

- The warehouse is loaded in batches, so `latest` means the newest day that was
  loaded, not today. A date with no rows produces an honest empty report.
- The dependency pins in `pyproject.toml` are mirrored in
  `infra/airflow/requirements.txt`. They have to agree: the tests run against
  the pins here, and the DAG runs against the pins there.
- The package requires Python 3.10, not because it wants to, but because the
  Airflow image is `apache/airflow:3.1.1-python3.10` and the pipeline is
  imported into it.
