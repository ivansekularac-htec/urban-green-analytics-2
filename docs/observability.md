# Observability

This guide explains how to run, use, verify, and troubleshoot the observability stack.

The stack uses:

- Prometheus for metrics
- Loki for centralized logs
- Promtail for log collection
- Grafana for dashboards
- kafka-exporter for Kafka metrics
- native metrics from FastAPI, MCP, ClickHouse, Spark, and MinIO

## Start the stack

From the repository root:

```bash
sudo docker compose --profile all up -d
```

Check service status:

```bash
sudo docker compose --profile all ps
```

For a clean restart without deleting persistent data:

```bash
sudo docker compose --profile all down
sudo docker compose --profile all up -d
```

Do not use:

```bash
docker compose down -v
```

for normal verification because it removes named volumes.

## Configuration

The main observability configuration is located under:

```text
docker-compose.yaml

infra/prometheus/
infra/loki/
infra/promtail/
infra/grafana/
infra/minio/
infra/spark/
```

Grafana dashboards are stored in:

```text
infra/grafana/dashboards/Urban Green/
```

The available dashboards are:

```text
System Overview
App Performance
Pipeline
```

Grafana datasources and dashboards are provisioned from repository files, so no manual dashboard import is required.

## Prometheus

Prometheus is available on:

```text
http://localhost:9090
```

The targets page is available at:

```text
http://localhost:9090/targets
```

All configured targets should have state:

```text
UP
```

The same information is available through the Prometheus API:

```bash
curl -s http://localhost:9090/api/v1/targets | python -m json.tool
```

If a target is `DOWN`, check its error message on the `/targets` page and then verify the corresponding service metrics endpoint.

## Metrics endpoints

Prometheus scrapes the following endpoints inside the Docker Compose network.

### API

```text
http://urbangreen-api:8000/metrics
```

### MCP

```text
http://urbangreen-mcp:8001/metrics
```

### ClickHouse

```text
http://urbangreen-clickhouse:9363/metrics
```

### Kafka exporter

```text
http://urbangreen-kafka-exporter:9308/metrics
```

### MinIO

```text
http://urbangreen-minio:9000/minio/v2/metrics/cluster
```

### Spark master

```text
http://urbangreen-spark-master:8090/metrics/master/prometheus
```

### Spark applications

```text
http://urbangreen-spark-master:8090/metrics/applications/prometheus
```

### Spark worker 1

```text
http://urbangreen-spark-worker-1:8081/metrics/prometheus
```

### Spark worker 2

```text
http://urbangreen-spark-worker-2:8081/metrics/prometheus
```

### Spark streaming driver

```text
http://urbangreen-spark-streaming:4050/metrics/prometheus
```

## Grafana

Check the published Grafana port with:

```bash
sudo docker compose ps urbangreen-grafana
```

Open the displayed host port in a browser.

Prometheus and Loki are provisioned automatically as Grafana datasources.

Dashboard JSON files are loaded from:

```text
infra/grafana/dashboards/Urban Green/
```

If dashboard changes are not immediately visible, refresh the browser.

If needed, restart only Grafana:

```bash
sudo docker compose restart urbangreen-grafana
```

## System Overview

Use **System Overview** for platform-wide health.

It shows:

- current Prometheus target status
- services or targets that are down
- service flapping
- error logs
- log volume by service

MinIO and ClickHouse are included through their Prometheus target health and service logs.

Detailed pipeline-specific metrics are kept in the Pipeline dashboard.

## App Performance

Use **App Performance** for FastAPI and MCP behavior.

### FastAPI

The dashboard shows:

- request rate
- total requests
- p50 latency
- p95 latency
- p99 latency
- comparison with the 1.5-second SLA reference

Generate test API traffic with:

```bash
for i in $(seq 1 50); do
  curl -s -o /dev/null http://localhost:8000/health
done
```

Refresh the dashboard afterwards.

### MCP

The main MCP metrics are:

```text
mcp_tool_calls_total
mcp_tool_duration_seconds_bucket
```

They are used for:

- total tool calls
- calls per minute
- tool latency
- error ratio
- latency by tool
- errors by tool

The App Performance dashboard also shows SQL sent through the MCP `execute_query` tool.

These queries are logged using:

```text
mcp_sql_query:
```

and are read from Loki.

## Generate MCP activity

From the `mcp` directory:

```powershell
uv run fastmcp call http://localhost:8001/mcp list_tables
```

Describe a table:

```powershell
uv run fastmcp call http://localhost:8001/mcp describe_table 'table=dim_farm'
```

Execute a query:

```powershell
uv run fastmcp call http://localhost:8001/mcp execute_query 'sql=SELECT * FROM dim_farm LIMIT 5'
```

Another example:

```powershell
uv run fastmcp call http://localhost:8001/mcp execute_query 'sql=SELECT count() AS total_sensor_readings FROM fact_sensor_readings'
```

Check MCP metrics with:

```bash
curl -s http://localhost:8001/metrics | grep '^mcp_tool_calls_total'
```

A successful query should increment a metric similar to:

```text
mcp_tool_calls_total{outcome="ok",tool="execute_query"}
```

## Pipeline

Use **Pipeline** to monitor activity through:

```text
Kafka -> Spark -> MinIO -> Airflow
```

The dashboard combines Prometheus metrics and Loki logs.

## Kafka

Kafka metrics are exposed by:

```text
urbangreen-kafka-exporter
```

The exporter provides topic and consumer-group metrics.

The Pipeline dashboard shows:

- topic offset growth
- consumer lag when committed Kafka consumer-group offsets exist

### Consumer Lag can show NO DATA

The current Spark Structured Streaming job stores Kafka offsets in its Spark checkpoint.

It does not commit a persistent Kafka consumer-group offset that `kafka-exporter` can expose through:

```text
kafka_consumergroup_lag
```

Because of this, the Consumer Lag panel can legitimately show:

```text
NO DATA
```

This does not mean that Kafka or kafka-exporter is broken.

Kafka topic offset metrics still show whether messages are being produced.

## Spark

Spark uses its native PrometheusServlet.

The Pipeline dashboard shows:

- registered workers
- alive workers
- running applications
- waiting applications
- streaming batch processing time
- trigger overrun
- input rate
- processing rate
- active executors
- Spark job outcomes
- JVM GC activity

### Trigger interval

The dashboard variable:

```text
Trigger interval (ms)
```

defaults to:

```text
60000
```

which corresponds to a 60-second streaming trigger.

If `STREAM_TRIGGER_INTERVAL` changes, update this dashboard variable.

The trigger-overrun panel uses:

```promql
clamp_min(
  max(
    {__name__=~"metrics_.*_driver_spark_streaming_.*_latency_Value",
     job="urbangreen-spark-streaming"}
  ) - ${trigger_interval_ms:raw},
  0
)
```

The `max(...)` aggregation keeps the range query valid across Spark application restarts because Spark metric names contain dynamic application identifiers.

## MinIO

MinIO metrics are exposed through:

```text
/minio/v2/metrics/cluster
```

MinIO is configured with:

```text
MINIO_PROMETHEUS_AUTH_TYPE=public
```

which allows Prometheus to scrape the metrics endpoint from the internal Docker network without a JWT token.

The Pipeline dashboard shows:

- used capacity
- usable free capacity
- offline drives
- stored objects
- S3 operations
- S3 traffic received
- S3 traffic sent

For the MinIO version used by the project, this path is not the correct Prometheus endpoint:

```text
/minio/metrics/prometheus
```

It returns `403 AccessDenied`.

Use:

```text
/minio/v2/metrics/cluster
```

instead.

The project uses:

```text
quay.io/minio/minio:latest
quay.io/minio/mc:latest
```

The MinIO data volume should be preserved during normal service recreation.

## Generate Pipeline activity

Trigger the warehouse DAG:

```bash
sudo docker compose exec -T urbangreen-airflow \
  airflow dags trigger warehouse_load
```

Check DAG runs:

```bash
sudo docker compose exec -T urbangreen-airflow \
  airflow dags list-runs -d warehouse_load
```

Wait until the latest run reaches:

```text
success
```

This generates real activity for Spark, MinIO, and Airflow.

Refresh the Pipeline dashboard afterwards.

## Airflow

Airflow monitoring is log-based.

Promtail collects:

- Airflow Docker stdout
- Airflow task log files

The Pipeline dashboard shows:

- successful task transitions
- failed task transitions
- Airflow errors
- tracebacks

For the exact state of a specific `warehouse_load` run, use:

```bash
sudo docker compose exec -T urbangreen-airflow \
  airflow dags list-runs -d warehouse_load
```

## Loki and Promtail

Promtail collects Docker logs through:

```text
/var/run/docker.sock
```

and Airflow task logs from:

```text
/opt/airflow/logs
```

The logs are forwarded to Loki and displayed in Grafana.

Depending on the log source, labels can include:

```text
service
dag
task
run_id
```

## Validate configuration

Validate Docker Compose:

```bash
sudo docker compose config >/dev/null && echo "Compose config: OK"
```

Validate Prometheus configuration:

```bash
sudo docker compose exec -T urbangreen-prometheus \
  promtool check config /etc/prometheus/prometheus.yml
```

Expected result:

```text
SUCCESS: /etc/prometheus/prometheus.yml is valid prometheus config file syntax
```

Validate a Grafana dashboard JSON file:

```bash
python -m json.tool \
  "infra/grafana/dashboards/Urban Green/pipeline.json" \
  >/dev/null
```

Before committing:

```bash
git diff --check
```

## Troubleshooting

If a Grafana panel shows `NO DATA` or an error, check in this order:

1. Confirm that the source service is running.
2. Open `http://localhost:9090/targets`.
3. Confirm that the corresponding Prometheus target is `UP`.
4. Check the service metrics endpoint directly.
5. Query the metric in Prometheus.
6. Only then inspect the Grafana PromQL or LogQL query.

Common expected cases:

### Kafka Consumer Lag shows NO DATA

This can be expected because Spark Structured Streaming stores offsets in its checkpoint instead of committing a Kafka consumer group.

### MinIO metrics return 403 on `/minio/metrics/prometheus`

Use:

```text
/minio/v2/metrics/cluster
```

instead.

### Dashboard changes are not visible

Refresh Grafana or restart only the Grafana container:

```bash
sudo docker compose restart urbangreen-grafana
```

## Quick verification

Start the stack:

```bash
sudo docker compose --profile all up -d
```

Check Prometheus:

```text
http://localhost:9090/targets
```

Generate API traffic:

```bash
for i in $(seq 1 20); do
  curl -s -o /dev/null http://localhost:8000/health
done
```

Run one MCP query:

```powershell
uv run fastmcp call http://localhost:8001/mcp execute_query 'sql=SELECT count() AS total_sensor_readings FROM fact_sensor_readings'
```

Trigger the warehouse DAG:

```bash
sudo docker compose exec -T urbangreen-airflow \
  airflow dags trigger warehouse_load
```

Then check:

```text
System Overview
App Performance
Pipeline
```

If Prometheus targets are healthy and the generated activity appears in the dashboards, the observability path is working end to end.