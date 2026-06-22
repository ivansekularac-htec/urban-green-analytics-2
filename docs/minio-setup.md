# MinIO Setup

## Overview

The system uses MinIO as an S3-compatible object storage for storing raw and processed files.

It is primarily used as a **staging layer for raw data ingestion** and internal service file exchange.

---

## Docker Setup

MinIO runs inside a Docker container defined in `docker-compose.yaml`.

### Service Configuration

- Container name: `urbangreen-minio`
- Image: official MinIO latest

---

## Environment Variables

Defined in `.env`:

- `MINIO_ROOT_USER`
- `MINIO_ROOT_PASSWORD`
- `MINIO_API_PORT`
- `MINIO_CONSOLE_PORT`
- `MINIO_HOST`
- `MINIO_STAGING_BUCKET`

---

## Network Endpoints

| Type | URL |
|------|-----|
| Internal (Docker) | http://urbangreen-minio:9000 |
| External (Local) | http://localhost:9000 |

---

## MinIO Web Console

| Property | Value |
|----------|------|
| URL | http://localhost:9001 |
| Username | MINIO_ROOT_USER |
| Password | MINIO_ROOT_PASSWORD |

---

## Volumes

| Volume | Purpose |
|--------|--------|
| /data | Persistent object storage |

---

## Staging Bucket

| Property | Value |
|----------|------|
| Bucket | staging |

### Rules

- All raw data MUST go to `staging`
- `staging` is default ingestion layer
- Bucket is created automatically on startup

---

## Bucket Initialization

Init container runs:

mc mb --ignore-existing local/staging

---

## Health Check

MinIO is healthy when this endpoint responds:

``` http://urbangreen-minio:9000/minio/health/live ```

---

## Starting MinIO

```bash
docker compose up -d minio
```

Logs:
```bash
docker compose logs -f minio
```

Stop:
```bash
docker compose down
```

Rebuild (WARNING: deletes data):
```bash
docker compose down -v
docker compose up -d
```

---

## Connecting

### Web Console
http://localhost:9001

### S3 Endpoints

| Scenario | Endpoint |
|----------|----------|
| Backend | http://urbangreen-minio:9000 |
| Local tools | http://localhost:9000 |