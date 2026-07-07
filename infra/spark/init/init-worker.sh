#!/bin/sh

set -eu

exec /opt/spark/bin/spark-class \
    org.apache.spark.deploy.worker.Worker \
    "spark://urbangreen-spark-master:${SPARK_MASTER_PORT:-7077}" \
    --cores "${SPARK_WORKER_CORES:-1}" \
    --memory "${SPARK_WORKER_MEMORY:-1g}"