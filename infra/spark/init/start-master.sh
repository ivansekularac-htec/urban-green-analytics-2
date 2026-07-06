#!/bin/sh

set -eu

exec /opt/spark/bin/spark-class \
    org.apache.spark.deploy.master.Master \
    --host urbangreen-spark-master \
    --port "${SPARK_MASTER_PORT:-7077}" \
    --webui-port "${SPARK_MASTER_UI_PORT:-8090}"