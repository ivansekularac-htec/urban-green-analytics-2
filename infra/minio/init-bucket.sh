#!/bin/sh
set -eu

MINIO_HOST="${MINIO_HOST:-minio}"
MINIO_PORT="${MINIO_API_PORT:-9000}"
MINIO_URL="http://${MINIO_HOST}:${MINIO_PORT}"
MAX_ATTEMPTS=30

echo "Waiting for MinIO at ${MINIO_URL}..."

attempts=0
until mc alias set local "${MINIO_URL}" "${MINIO_ROOT_USER}" "${MINIO_ROOT_PASSWORD}" >/dev/null 2>&1; do
  attempts=$((attempts + 1))
  if [ "$attempts" -ge "$MAX_ATTEMPTS" ]; then
    echo "Gave up waiting for MinIO after ${MAX_ATTEMPTS} attempts." >&2
    exit 1
  fi
  echo "MinIO is not ready yet. Retrying (${attempts}/${MAX_ATTEMPTS})..."
  sleep 2
done

echo "MinIO alias configured. Checking server readiness..."
mc ready local

echo "Ensuring bucket '${MINIO_STAGING_BUCKET}' exists..."
mc mb --ignore-existing "local/${MINIO_STAGING_BUCKET}"

echo "Verifying bucket exists..."
mc ls "local/${MINIO_STAGING_BUCKET}"
mc ls local/

echo "Bucket '${MINIO_STAGING_BUCKET}' is ready."