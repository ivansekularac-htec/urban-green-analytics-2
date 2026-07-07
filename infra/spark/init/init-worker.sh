#!/bin/sh
set -eu

SPARK_MASTER_URL="spark://urbangreen-spark-master:${SPARK_MASTER_PORT:-7077}"

echo "Starting Spark Worker..."
echo "Master: ${SPARK_MASTER_URL}"

exec /opt/spark/bin/spark-class \
  org.apache.spark.deploy.worker.Worker \
  "${SPARK_MASTER_URL}" \
  --cores "${SPARK_WORKER_CORES:-1}" \
  --memory "${SPARK_WORKER_MEMORY:-1g}"