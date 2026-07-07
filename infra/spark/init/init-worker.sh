#!/bin/sh
set -eu

SPARK_MASTER_PORT="${SPARK_MASTER_PORT:-7077}"
SPARK_MASTER_URL="spark://urbangreen-spark-master:${SPARK_MASTER_PORT}"
SPARK_WORKER_CORES="${SPARK_WORKER_CORES:-1}"
SPARK_WORKER_MEMORY="${SPARK_WORKER_MEMORY:-1g}"

echo "Starting Spark Worker..."
echo "Master URL: ${SPARK_MASTER_URL}"
echo "Cores: ${SPARK_WORKER_CORES}"
echo "Memory: ${SPARK_WORKER_MEMORY}"

exec /opt/spark/bin/spark-class \
  org.apache.spark.deploy.worker.Worker \
  "${SPARK_MASTER_URL}" \
  --cores "${SPARK_WORKER_CORES}" \
  --memory "${SPARK_WORKER_MEMORY}"
