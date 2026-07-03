set -eu

BOOTSTRAP_SERVER="urbangreen-kafka:${KAFKA_PORT_INTERNAL:-9092}"
TOPIC_NAME="${KAFKA_TOPIC_SENSOR_READINGS:-sensor_readings}"

echo "Creating Kafka topic if it does not exist..."
echo "Bootstrap server: ${BOOTSTRAP_SERVER}"
echo "Topic: ${TOPIC_NAME}"

/opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server "${BOOTSTRAP_SERVER}" \
  --create \
  --if-not-exists \
  --topic "${TOPIC_NAME}" \
  --partitions 3 \
  --replication-factor 1

echo "Kafka topic initialization completed."