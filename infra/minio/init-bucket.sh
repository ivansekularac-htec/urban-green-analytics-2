#!/bin/sh
set -e

echo "Waiting for MinIO..."

MINIO_URL="http://${MINIO_HOST}:${MINIO_API_PORT}"

# wait until MinIO responds 
until curl -fs "$MINIO_URL/minio/health/live" >/dev/null 2>&1
do
  echo "MinIO not ready yet..."
  sleep 2
done

echo "MinIO is up"

# configure mc alias
mc alias set local "$MINIO_URL" "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD"

echo "Creating bucket: $MINIO_STAGING_BUCKET"

# idempotent bucket creation
mc mb --ignore-existing "local/$MINIO_STAGING_BUCKET"

echo "Done"
exit 0