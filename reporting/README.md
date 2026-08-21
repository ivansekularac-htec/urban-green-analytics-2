# UrbanGreen reporting service

Builds the daily executive report: it reads the day's KPIs from the ClickHouse
warehouse, has the local Ollama model write a short narrative, renders one
self-contained HTML document, and publishes it to the MinIO staging bucket and
as an email.

The pipeline is a linear [LangGraph](https://langchain-ai.github.io/langgraph/)
graph:

```
fetch_metrics -> summarize -> render -> publish
```

## The model never chooses a number

The KPI queries in `app/metrics.py` are fixed, and every figure in the report
comes from them. The model is given those figures and writes prose about them;
it does not query the warehouse and it does not compute anything.

If the model is slow, unreachable, or answers with something unusable, the run
falls back to a fixed narrative built from the same figures. The report is
published either way, and its footer names which of the two wrote the summary.

## Running it

```bash
docker compose up -d --build urbangreen-reporting urbangreen-mailpit
curl http://localhost:8002/health
```

Build a report:

```bash
# a specific day
curl -X POST http://localhost:8002/reports/2026-08-15

# the newest day loaded in the warehouse
curl -X POST http://localhost:8002/reports/latest
```

The response carries the object key and what happened:

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

The `daily_executive_report` DAG runs at 06:00 and posts its logical date to
this service. It retries twice, because the first inference after a restart has
to load the model and takes considerably longer than a warm run. The published
object key is the task result.

## Local development

```bash
cd reporting
uv sync --frozen --group dev
uv run ruff check app tests && uv run ruff format --check app tests
uv run pytest
```

To run against the containerised stack from the host, copy `.env.example` to
`.env` (it points at `localhost` rather than the container names) and:

```bash
uv run python -m app.main --date 2026-08-15   # one run, no server
uv run python -m app.main                     # serve on 8002
```

## Notes

- The warehouse is loaded in batches, so `latest` means the newest day that was
  loaded, not today.
- MinIO belongs to the `backend` compose profile while this service belongs to
  `analytics`. It is deliberately not a startup dependency, so this service can
  run under `--profile analytics` alone; without MinIO the report is emailed
  and the missing object is reported as a warning.
