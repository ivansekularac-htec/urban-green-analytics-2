<!-- # MinIO Setup

## Overview

The system uses MinIO as an S3-compatible object storage for storing raw and processed files.

It is primarily used as a **staging layer for raw data ingestion** and internal service file exchange.

---

## Docker Setup

MinIO runs inside a Docker container defined in `docker-compose.yaml`.

### Service Configuration

- MinIO API version: latest (official image)
- Container name: `urbangreen-minio`

---

## Environment Variables

MinIO configuration is defined in the `.env` file:

- `MINIO_ROOT_USER`
- `MINIO_ROOT_PASSWORD`
- `MINIO_API_PORT` (default `9000`)
- `MINIO_CONSOLE_PORT` (default `9001`)
- `MINIO_HOST`
- `MINIO_STAGING_BUCKET`

---

## Network Endpoints

| Type        | URL |
|------------|-----|
| Internal (Docker) | http://urbangreen-minio:9000 |
| External (Local)  | http://localhost:9000 |

---

## MinIO Web Console

| Property | Value |
|----------|------|
| URL      | http://localhost:9001 |
| Username | minioadmin |
| Password | change-me-in-prod |

---

## Volumes

| Volume | Purpose |
|--------|--------|
| `/data` | Persistent object storage |

---

## Staging Bucket

| Property | Value |
|----------|------|
| Bucket name | `staging` |
| Purpose | Raw data ingestion layer |

### Usage

The `staging` bucket is used for:

- raw simulator output
- unprocessed ingestion data
- temporary storage before processing pipelines

### Rules

- All raw data MUST be written to `staging`
- Services MUST treat `staging` as the default input layer
- Bucket is created automatically on startup

---

## Bucket Initialization

On first startup, a dedicated init container ensures bucket existence.

### Process

1. Wait for MinIO health check
2. Configure `mc` client alias
3. Create bucket if it does not exist (idempotent)

### Command used

```bash id="mc_bucket_create"
mc mb --ignore-existing local/staging
```

### Health Check

MinIO is considered ready when:

http://urbangreen-minio:9000/minio/health/live

returns OK.

### Starting the Service

Start MinIO:

```bash
docker compose up -d minio
```

View logs:

```bash
docker compose logs -f minio
```

Stop service:

```bash
docker compose down
```

Rebuilding Storage:

```bash
docker compose down -v
docker compose up -d
```
⚠️ This will delete all stored objects.

### Connecting to MinIO
#### Using Web Console

Open:

http://localhost:9001

Login with credentials from .env.

#### Using S3 Clients

Use the internal or external endpoint depending on context:

Scenario	Endpoint
Backend service	http://urbangreen-minio:9000
Local tools	http://localhost:9000

--- -->

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