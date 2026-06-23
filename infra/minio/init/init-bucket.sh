#!/bin/sh
# Create the staging bucket on stack-up. Idempotent: safe to re-run.
#
# Runs inside a one-shot `minio/mc` container (the `minio-init` service),
# which only starts after the MinIO service is healthy.
set -eu

MINIO_API_PORT="${MINIO_API_PORT:-9000}"
MINIO_ENDPOINT="http://minio:${MINIO_API_PORT}"

# Point `mc` at the running MinIO using the root credentials.
mc alias set local "${MINIO_ENDPOINT}" "${MINIO_ROOT_USER}" "${MINIO_ROOT_PASSWORD}"

# Wait until MinIO is ready to serve requests.
mc ready local

# Create the bucket; --ignore-existing makes a re-run a no-op (exit 0).
mc mb --ignore-existing "local/${MINIO_STAGING_BUCKET}"

echo "Bucket '${MINIO_STAGING_BUCKET}' is ready."
