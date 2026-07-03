#!/bin/sh

set -eu

KAFKA_PORT_INTERNAL="${KAFKA_PORT_INTERNAL:-9092}"
KAFKA_TOPIC_SENSOR_READINGS="${KAFKA_TOPIC_SENSOR_READINGS:-sensor_readings}"

echo "Creating Kafka topic '${KAFKA_TOPIC_SENSOR_READINGS}'..."

/opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server "urbangreen-kafka:${KAFKA_PORT_INTERNAL}" \
  --create \
  --if-not-exists \
  --topic "${KAFKA_TOPIC_SENSOR_READINGS}" \
  --partitions 3 \
  --replication-factor 1

echo "Kafka topic initialization complete."