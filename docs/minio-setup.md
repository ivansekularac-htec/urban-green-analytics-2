# MinIO Setup

## Overview

The system uses MinIO as an S3-compatible object storage service for storing raw and processed files.

MinIO serves as the primary staging layer for raw data ingestion and internal file exchange between services.

---

## Docker Setup

MinIO runs as a Docker service defined in `docker-compose.yaml`.

### Service Configuration

* Container name: `urbangreen-minio`
* S3-compatible object storage service

---

## Environment Variables

The following variables must be configured:

* `MINIO_ROOT_USER`
* `MINIO_ROOT_PASSWORD`
* `MINIO_API_PORT`
* `MINIO_CONSOLE_PORT`
* `MINIO_HOST`
* `MINIO_STAGING_BUCKET`

---

## Network Endpoints

| Type                      | URL                            |
| ------------------------- | ------------------------------ |
| Internal (Docker network) | `http://urbangreen-minio:9000` |
| External (Host machine)   | `http://localhost:9000`        |

---

## MinIO Web Console

| Property | Value                   |
| -------- | ----------------------- |
| URL      | `http://localhost:9001` |
| Username | `MINIO_ROOT_USER`       |
| Password | `MINIO_ROOT_PASSWORD`   |

---

## Storage Volume

| Volume  | Purpose                   |
| ------- | ------------------------- |
| `/data` | Persistent object storage |

---

## Data Lake Convention

The bucket defined by `MINIO_STAGING_BUCKET` is the agreed entry point for all raw data entering the platform.

Future ingestion pipelines, simulators, ETL jobs, and external integrations should upload raw files to this bucket.

Processed or curated datasets should be stored separately from the staging layer.

---

## Staging Bucket

| Property | Value                             |
| -------- | --------------------------------- |
| Bucket   | Defined by `MINIO_STAGING_BUCKET` |

### Rules

* All raw data must be uploaded to the staging bucket.
* The staging bucket is the default ingestion layer.
* The bucket is created automatically during startup.
* Bucket creation is idempotent and safe to re-run.

---

## Bucket Initialization

A one-shot initialization container creates the staging bucket automatically during startup.

The initialization script executes:

```bash
mc mb --ignore-existing local/${MINIO_STAGING_BUCKET}
```

This guarantees that the bucket exists while avoiding failures when the bucket has already been created.

---

## Health Check

MinIO is considered healthy when the following endpoint returns `200 OK`:

```text
http://urbangreen-minio:9000/minio/health/live
```

---

## Starting MinIO

Start all services:

```bash
docker compose up -d
```

View MinIO logs:

```bash
docker compose logs -f minio
```

Stop the stack:

```bash
docker compose down
```

Recreate containers and volumes (warning: deletes persisted data):

```bash
docker compose down -v
docker compose up -d
```

---

## Connecting

### Web Console

```text
http://localhost:9001
```

### S3 Endpoints

| Scenario                | Endpoint                       |
| ----------------------- | ------------------------------ |
| Backend services        | `http://urbangreen-minio:9000` |
| Local tools and clients | `http://localhost:9000`        |

```

This setup standardizes object storage usage across services and establishes the staging bucket as the default raw data ingestion layer.
```
