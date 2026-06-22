#!/bin/sh
set -eu

: "${MINIO_ROOT_USER:?MINIO_ROOT_USER is required}"
: "${MINIO_ROOT_PASSWORD:?MINIO_ROOT_PASSWORD is required}"
: "${MINIO_STAGING_BUCKET:?MINIO_STAGING_BUCKET is required}"

MINIO_ENDPOINT="${MINIO_ENDPOINT:-http://minio:9000}"

echo "Waiting for MinIO at ${MINIO_ENDPOINT}..."

until mc alias set local "${MINIO_ENDPOINT}" "${MINIO_ROOT_USER}" "${MINIO_ROOT_PASSWORD}"; do
  echo "MinIO is not ready yet. Retrying..."
  sleep 2
done

echo "Creating staging bucket: ${MINIO_STAGING_BUCKET}"

mc mb --ignore-existing "local/${MINIO_STAGING_BUCKET}"

echo "MinIO staging bucket is ready."