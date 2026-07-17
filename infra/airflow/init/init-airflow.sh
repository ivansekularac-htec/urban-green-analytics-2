#!/bin/sh

set -eu

POSTGRES_HOST="${POSTGRES_HOST:-urbangreen-postgres}"
POSTGRES_USER="${POSTGRES_USER}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD}"
POSTGRES_DB="${POSTGRES_DB}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"

MINIO_ROOT_USER="${MINIO_ROOT_USER:-minio}"
MINIO_ROOT_PASSWORD="${MINIO_ROOT_PASSWORD}"
MINIO_API_PORT="${MINIO_API_PORT:-9000}"

SPARK_MASTER_PORT="${SPARK_MASTER_PORT:-7077}"

AIRFLOW_PORT="${AIRFLOW_PORT:-8080}"

airflow db migrate

airflow connections add urbangreen_db \
  --conn-type postgres \
  --conn-host "${POSTGRES_HOST}" \
  --conn-login "${POSTGRES_USER}" \
  --conn-password "${POSTGRES_PASSWORD}" \
  --conn-schema "${POSTGRES_DB}" \
  --conn-port "${POSTGRES_PORT}" || true

airflow connections add urbangreen_minio \
  --conn-type aws \
  --conn-login "${MINIO_ROOT_USER}" \
  --conn-password "${MINIO_ROOT_PASSWORD}" \
  --conn-extra "{\"endpoint_url\": \"http://urbangreen-minio:${MINIO_API_PORT}\"}" || true

airflow connections add urbangreen_spark \
  --conn-type spark \
  --conn-host "spark://urbangreen-spark-master" \
  --conn-port "${SPARK_MASTER_PORT}" || true

airflow connections add urbangreen_clickhouse \
  --conn-json "{
    \"conn_type\": \"generic\",
    \"host\": \"urbangreen-clickhouse\",
    \"login\": \"${CLICKHOUSE_USER}\",
    \"password\": \"${CLICKHOUSE_PASSWORD}\",
    \"schema\": \"${CLICKHOUSE_DB:-urbangreen_analytics}\",
    \"port\": 8123,
    \"extra\": {
      \"tcp_port\": 9000,
      \"jdbc_url\": \"jdbc:clickhouse://urbangreen-clickhouse:8123/${CLICKHOUSE_DB:-urbangreen_analytics}\"
    }
  }" || true

exec airflow standalone