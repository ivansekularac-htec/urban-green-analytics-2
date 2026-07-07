#!/bin/sh
set -eu

SPARK_MASTER_HOST="urbangreen-spark-master"
SPARK_MASTER_PORT="${SPARK_MASTER_PORT:-7077}"
SPARK_WORKER_CORES="${SPARK_WORKER_CORES:-1}"
SPARK_WORKER_MEMORY="${SPARK_WORKER_MEMORY:-1g}"

SPARK_MASTER_URL="spark://${SPARK_MASTER_HOST}:${SPARK_MASTER_PORT}"

echo "Starting Spark Worker..."
echo "Master URL: ${SPARK_MASTER_URL}"
echo "Worker cores: ${SPARK_WORKER_CORES}"
echo "Worker memory: ${SPARK_WORKER_MEMORY}"

exec /opt/spark/bin/spark-class \
  org.apache.spark.deploy.worker.Worker \
  "${SPARK_MASTER_URL}" \
  --cores "${SPARK_WORKER_CORES}" \
  --memory "${SPARK_WORKER_MEMORY}"