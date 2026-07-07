#!/bin/sh
set -eu

SPARK_MASTER_PORT="${SPARK_MASTER_PORT:-7077}"
SPARK_WORKER_CORES="${SPARK_WORKER_CORES:-1}"
SPARK_WORKER_MEMORY="${SPARK_WORKER_MEMORY:-1g}"

echo "Starting Spark Worker..."
echo "RPC Port: ${SPARK_MASTER_PORT}"
echo "Worker Cores: ${SPARK_WORKER_CORES}"
echo "Worker memory: ${SPARK_WORKER_MEMORY}"

exec /opt/spark/bin/spark-class \
    org.apache.spark.deploy.worker.Worker \
    spark://urbangreen-spark-master:"${SPARK_MASTER_PORT}" \
    --cores "${SPARK_WORKER_CORES}" \
    --memory "${SPARK_WORKER_MEMORY}"