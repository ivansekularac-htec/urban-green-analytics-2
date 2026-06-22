#!/bin/sh
set -eu

MAX_ATTEMPTS=${MINIO_INIT_MAX_ATTEMPTS:-30}
RETRY_INTERVAL=${MINIO_INIT_RETRY_INTERVAL:-2}
attempts=0

echo "Waiting for MinIO to be ready..."

until mc alias set local "http://minio:${MINIO_API_PORT:-9000}" "${MINIO_ROOT_USER}" "${MINIO_ROOT_PASSWORD}" >/dev/null 2>&1; do
  attempts=$((attempts + 1))
  if [ "$attempts" -ge "$MAX_ATTEMPTS" ]; then
    echo "ERROR: Gave up waiting for MinIO after $MAX_ATTEMPTS attempts." >&2
    exit 1
  fi
  sleep "$RETRY_INTERVAL"
  echo "MinIO not ready yet, retrying ($attempts/$MAX_ATTEMPTS)..."
done

echo "MinIO is ready."
echo "Creating staging bucket: ${MINIO_STAGING_BUCKET}"

mc mb --ignore-existing "local/${MINIO_STAGING_BUCKET}"

echo "Verifying bucket exists:"
mc ls "local/${MINIO_STAGING_BUCKET}" >/dev/null 2>&1 || { echo "ERROR: Bucket '${MINIO_STAGING_BUCKET}' not found after creation." >&2; exit 1; }

echo "Bucket '${MINIO_STAGING_BUCKET}' initialized successfully."