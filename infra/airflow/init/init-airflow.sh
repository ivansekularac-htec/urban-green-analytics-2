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

CLICKHOUSE_USER="${CLICKHOUSE_USER}"
CLICKHOUSE_PASSWORD="${CLICKHOUSE_PASSWORD}"
CLICKHOUSE_DB_NAME="${CLICKHOUSE_DB_NAME:-urbangreen_dw}"

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
  --conn-type generic \
  --conn-host "urbangreen-clickhouse" \
  --conn-login "${CLICKHOUSE_USER}" \
  --conn-password "${CLICKHOUSE_PASSWORD}" \
  --conn-schema "${CLICKHOUSE_DB_NAME:-urbangreen_dw}" \
  --conn-port 8123 \
  --conn-extra "{\"tcp_port\": 9000, \"jdbc_url\": \"jdbc:clickhouse://urbangreen-clickhouse:8123/${CLICKHOUSE_DB_NAME:-urbangreen_dw}\"}" \
  || true

exec airflow standalone
