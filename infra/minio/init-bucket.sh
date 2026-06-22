#!/bin/sh

set -eu

ALIAS_URL="http://urbangreen-minio:9000"
MAX_ATTEMPTS=30
ATTEMPT=0

echo "Waiting for MinIO to be ready..."

until mc alias set local "$ALIAS_URL" "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD" >/dev/null 2>&1; do
    ATTEMPT=$((ATTEMPT + 1))

    if [ "$ATTEMPT" -ge "$MAX_ATTEMPTS" ]; then
        echo "Error: MinIO did not become ready after $MAX_ATTEMPTS attempts."
        exit 1
    fi

    echo "Attempt $ATTEMPT/$MAX_ATTEMPTS: MinIO not ready yet. Retrying in 2s..."
    sleep 2
done

echo "MinIO is ready!"

echo "Creating bucket: $MINIO_STAGING_BUCKET"
mc mb --ignore-existing "local/$MINIO_STAGING_BUCKET"

echo "Verifying bucket exists..."
mc ls local/ | grep -q "^.* $MINIO_STAGING_BUCKET/$"

echo "Bucket verified: $MINIO_STAGING_BUCKET"

echo "Bucket ensured successfully"