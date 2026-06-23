#!/bin/sh
set -eu

echo "Waiting for MinIO..."

attempts=0

until mc alias set local "http://minio:${MINIO_API_PORT:-9000}" "${MINIO_ROOT_USER}" "${MINIO_ROOT_PASSWORD}"; do
  attempts=$((attempts + 1))

  if [ "$attempts" -ge 30 ]; then
    echo "Failed to connect to MinIO after 30 attempts." >&2
    exit 1
  fi

  echo "MinIO is not ready yet. Retrying ($attempts/30)..."
  sleep 2
done

echo "Creating staging bucket: ${MINIO_STAGING_BUCKET}"

mc mb --ignore-existing "local/${MINIO_STAGING_BUCKET}"

echo "Verifying bucket exists..."

mc ls "local/${MINIO_STAGING_BUCKET}"

echo "MinIO bucket initialization completed."