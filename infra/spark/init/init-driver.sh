#!/bin/sh
set -eu

SPARK_MASTER_HOST="urbangreen-spark-master"
SPARK_MASTER_PORT="${SPARK_MASTER_PORT:-7077}"

echo "Starting Spark Streaming Driver..."
echo "Master: spark://${SPARK_MASTER_HOST}:${SPARK_MASTER_PORT}"
echo "Kafka: ${KAFKA_BOOTSTRAP}"
echo "MinIO: ${MINIO_ENDPOINT}"

exec /opt/spark/bin/spark-submit \
  --master "spark://${SPARK_MASTER_HOST}:${SPARK_MASTER_PORT}" \
  --deploy-mode client \
  --name sensor_readings_stream \
  --conf spark.driver.host=urbangreen-spark-streaming \
  --conf spark.driver.bindAddress=0.0.0.0 \
  --conf spark.executor.cores=1 \
  --conf spark.cores.max=1 \
  --conf spark.ui.port=4050 \
  --conf spark.sql.session.timeZone=UTC \
  /opt/spark/work-dir/ingestion/sensor_readings_stream.py