#!/bin/sh
set -eu

echo "[INFO] Waiting for MinIO..."

MINIO_HOST="${MINIO_HOST:-urbangreen-minio}"
MINIO_API_PORT="${MINIO_API_PORT:-9000}"
MINIO_URL="http://${MINIO_HOST}:${MINIO_API_PORT}"

attempts=0
until mc alias set local "$MINIO_URL" "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD" >/dev/null 2>&1
do
  attempts=$((attempts + 1))

  if [ "$attempts" -ge 30 ]; then
    echo "[ERROR] gave up waiting for MinIO after 30 attempts" >&2
    exit 1
  fi

  echo "[INFO] MinIO not ready yet. Retrying ($attempts/30)..."
  sleep 2
done

# verify connection
# mc ls local >/dev/null 2>&1
mc ready local >/dev/null 2>&1

echo "[INFO] Creating bucket: $MINIO_STAGING_BUCKET"
mc mb --ignore-existing "local/$MINIO_STAGING_BUCKET"

# verify bucket exists
mc ls "local/$MINIO_STAGING_BUCKET" >/dev/null 2>&1 || {
  echo "[ERROR] bucket verification failed" >&2
  exit 1
}

echo "[INFO] Done"
