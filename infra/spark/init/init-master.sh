#!/bin/sh
set -eu

SPARK_MASTER_HOST="urbangreen-spark-master"
SPARK_MASTER_PORT="${SPARK_MASTER_PORT:-7077}"
SPARK_MASTER_UI_PORT="${SPARK_MASTER_UI_PORT:-8090}"

echo "Starting Spark Master..."
echo "Host: ${SPARK_MASTER_HOST}"
echo "RPC Port: ${SPARK_MASTER_PORT}"
echo "Web UI Port: ${SPARK_MASTER_UI_PORT}"

exec /opt/spark/bin/spark-class \
  org.apache.spark.deploy.master.Master \
  --host "${SPARK_MASTER_HOST}" \
  --port "${SPARK_MASTER_PORT}" \
  --webui-port "${SPARK_MASTER_UI_PORT}"