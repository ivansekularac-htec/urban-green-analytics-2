#!/bin/sh
set -e

echo "Waiting for MinIO..."

until mc alias set local "http://minio:${MINIO_API_PORT:-9000}" "${MINIO_ROOT_USER}" "${MINIO_ROOT_PASSWORD}"; do
  echo "MinIO is not ready yet. Retrying..."
  sleep 2
done

echo "Creating staging bucket: ${MINIO_STAGING_BUCKET}"

mc mb --ignore-existing "local/${MINIO_STAGING_BUCKET}"

echo "MinIO bucket initialization completed."