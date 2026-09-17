# Module 6 — Observability Stack

Prometheus + Loki/Promtail + Grafana, wired around the platform built in
earlier modules. This document is the closing summary for Module 6

## Components

| Service | Role | Notes |
|---|---|---|
| `urbangreen-prometheus` | Metrics scrape + storage | 15s scrape interval, 10 scrape jobs |
| `urbangreen-loki` | Log storage | File-provisioned; no Airflow exporter exists, so Airflow signal is entirely log-derived |
| `urbangreen-promtail` | Log shipper | Docker socket discovery (`urbangreen-*` containers) + Airflow task-log file scrape |
| `urbangreen-grafana` | Dashboards | Provisioned datasources + dashboards, `Urban Green` folder |
| `urbangreen-kafka-exporter` | Kafka metrics | `kafka_topic_partition_current_offset` reliable; `kafka_consumergroup_lag` is not (see Known gaps) |

## Scrape jobs (`infra/prometheus/prometheus.yml`)

`urbangreen-api`, `urbangreen-mcp`, `urbangreen-minio`, `urbangreen-clickhouse`,
`urbangreen-spark-master`, `urbangreen-spark-applications`,
`urbangreen-spark-worker-1`, `urbangreen-spark-worker-2`,
`urbangreen-spark-streaming`, `urbangreen-kafka-exporter`.

MinIO's metrics path is `/minio/v2/metrics/cluster`, not the older
`/minio/metrics/prometheus` some documentation still references (T6.1.5).

## Dashboards (`infra/grafana/dashboards/Urban Green/`)

**System Overview** (`system-overview.json`) — platform-wide health at a
glance: services down, error/log volume, per-job up/down status, 24h uptime,
flap rate, and log/error volume by service.

**App Performance** (`app-performance.json`) — FastAPI and MCP request
health: request rate by route, p50/p95/p99 latency against the 1.5s SLA
(computed from `http_request_duration_highr_seconds`, the high-resolution
histogram — the coarser per-handler histogram has no bucket boundary near
1.5s and can't estimate that quantile meaningfully), 4xx/5xx rate, MCP tool
call rate/latency/error ratio, and the actual AI-generated SQL text read live
from MCP logs.

**Pipeline** (`pipeline.json`) — Kafka, Spark, and Airflow: topic offset
growth, Spark cluster/streaming state, JVM GC time, and Airflow task
SUCCESS/FAILED counts with an error/traceback log panel, all derived from
Loki since Airflow has no Prometheus exporter.

## End-to-end verification

```bash
docker compose down
docker compose --profile all up -d --build
```

Then, once every container reports healthy:

```bash
curl -s "http://localhost:${PROMETHEUS_UI_PORT:-9090}/api/v1/targets?state=active" \
  | python3 -c "import json,sys; [print(t['health'], t['labels']['job']) for t in json.load(sys.stdin)['data']['activeTargets']]"
```

Every line should read `up`. Generate synthetic load (a few dozen API
requests, one MCP `execute_query` call, one `warehouse_load` DAG run), wait
one scrape interval, then confirm each dashboard renders against real data.