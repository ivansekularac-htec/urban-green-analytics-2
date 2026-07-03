#!/bin/sh
# Create the sensor_readings topic on stack-up. Idempotent: safe to re-run.
#
# Runs inside a one-shot `apache/kafka` container (the `kafka-init` service),
# which only starts after the Kafka broker is healthy.
set -eu

KAFKA_PORT_INTERNAL="${KAFKA_PORT_INTERNAL:-9092}"
KAFKA_BOOTSTRAP="urbangreen-kafka:${KAFKA_PORT_INTERNAL}"
KAFKA_TOPIC_SENSOR_READINGS="${KAFKA_TOPIC_SENSOR_READINGS:-sensor_readings}"

# Create the topic; --if-not-exists makes a re-run a no-op (exit 0).
/opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server "${KAFKA_BOOTSTRAP}" \
  --create --if-not-exists \
  --topic "${KAFKA_TOPIC_SENSOR_READINGS}" \
  --partitions 3 \
  --replication-factor 1

echo "Topic '${KAFKA_TOPIC_SENSOR_READINGS}' is ready."
