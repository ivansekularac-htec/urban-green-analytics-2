#!/bin/sh
set -eu

SPARK_MASTER_PORT="${SPARK_MASTER_PORT:-7077}"

exec /opt/spark/bin/spark-submit \
  --master "spark://urbangreen-spark-master:${SPARK_MASTER_PORT:-7077}" \
  --deploy-mode client \
  --name sensor_readings_stream \
  --conf spark.driver.host=urbangreen-spark-streaming \
  --conf spark.ui.port=4040 \
  --conf spark.sql.session.timeZone=UTC \
  /opt/spark/work-dir/ingestion/sensor_readings_stream.py
  