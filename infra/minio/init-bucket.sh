#!/bin/sh
set -e

echo "Waiting for MinIO..."

MINIO_URL="http://${MINIO_HOST}:${MINIO_API_PORT}"

until mc alias set local "$MINIO_URL" "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD" >/dev/null 2>&1
do
  echo "MinIO not ready yet..."
  sleep 2
done

echo "Creating bucket: $MINIO_STAGING_BUCKET"

mc mb --ignore-existing "local/$MINIO_STAGING_BUCKET"

echo "Done"
