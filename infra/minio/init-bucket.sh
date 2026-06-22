#!/bin/sh

set -e

URL="http://urbangreen-minio:9000/minio/health/ready"
ALIAS_URL="http://urbangreen-minio:9000"
MAX_ATTEMPTS=30
ATTEMPT=0

echo "Waiting for MinIO to be ready..."

until mc alias set local "$ALIAS_URL" "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD" >/dev/null 2>&1; do
  echo "MinIO not ready yet... retrying"
  sleep 2
done

echo "MinIO is ready!"

# Configure alias
mc alias set local "$ALIAS_URL" "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD"

echo "Creating bucket: $MINIO_STAGING_BUCKET"

mc mb --ignore-existing "local/$MINIO_STAGING_BUCKET"

echo "Bucket ensured successfully"