#!/bin/sh
set -eu

MINIO_HOST="${MINIO_HOST:-minio}"
MINIO_PORT="${MINIO_API_PORT:-9000}"
MINIO_URL="http://${MINIO_HOST}:${MINIO_PORT}"

echo "Waiting for MinIO at ${MINIO_URL}..."

until mc alias set local "${MINIO_URL}" "${MINIO_ROOT_USER}" "${MINIO_ROOT_PASSWORD}" >/dev/null 2>&1; do
  sleep 2
done

echo "MinIO is ready. Ensuring bucket '${MINIO_STAGING_BUCKET}' exists..."

mc mb --ignore-existing "local/${MINIO_STAGING_BUCKET}"

echo "Bucket '${MINIO_STAGING_BUCKET}' is ready."