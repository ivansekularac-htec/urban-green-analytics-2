# MinIO

MinIO is used as S3-compatible object storage for the Urban Green platform.

## Start MinIO

Build the image:

```bash
docker compose build minio
```

Start the service:

```bash
docker compose up -d minio
```

Or start the entire stack:

```bash
docker compose up -d
```

## Access the Console

Open:

```text
http://localhost:9001
```

Login using the credentials defined in `.env`:

```env
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin
```

## Staging Bucket

The staging bucket is automatically created during startup by the `urbangreen-minio-init` container.

Default bucket:

```env
MINIO_STAGING_BUCKET=staging
```

Bucket creation is idempotent and can be safely re-run.

## Health Check

Verify MinIO health:

```bash
curl http://localhost:9000/minio/health/live
```

Expected response:

```text
OK
```