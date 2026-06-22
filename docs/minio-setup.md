# MinIO Setup

## Overview

MinIO provides S3-compatible object storage for the platform. It runs in Docker as part of the Compose stack on `urbangreen-network`. On stack startup, the one-shot `minio-init` service creates the staging bucket if it does not already exist.

Infrastructure lives under `infra/minio/` (Dockerfile and `init-bucket.sh`). Service definitions are in `docker-compose.yaml`.

---

## Endpoints

Use the **host** endpoints when connecting from your machine (browser, local scripts). Use the **in-network** endpoint when connecting from another Docker service on `urbangreen-network` (API, Spark, simulators, etc.).

| Purpose | URL | Notes |
| -------- | ----- | ----- |
| S3 API (in-network) | `http://urbangreen-minio:9000` | From containers on `urbangreen-network` |
| S3 API (host) | `http://localhost:9000` | Default; uses `MINIO_API_PORT` if overridden |
| Web console (host) | `http://localhost:9001` | Default; uses `MINIO_CONSOLE_PORT` if overridden |

**Examples with custom ports** (if set in `.env`):

- Host API: `http://localhost:<MINIO_API_PORT>`
- Host console: `http://localhost:<MINIO_CONSOLE_PORT>`

---

## Web console login

1. Open the console: [http://localhost:9001](http://localhost:9001) (or your `MINIO_CONSOLE_PORT`).
2. Sign in with the root credentials from your root `.env` file:

| Field | Environment variable |
| ----- | -------------------- |
| Username | `MINIO_ROOT_USER` |
| Password | `MINIO_ROOT_PASSWORD` |

Defaults in `.env.example` use `MINIO_ROOT_USER=minioadmin`. Set a strong password in your local `.env`; do not commit secrets.

---

## Environment variables

Configure these in the **root** `.env` file (same directory as `docker-compose.yaml`). See `.env.example` for a template.

| Variable | Purpose | Default |
| -------- | ------- | ------- |
| `MINIO_ROOT_USER` | Root / console username | `minioadmin` (example) |
| `MINIO_ROOT_PASSWORD` | Root / console password | *(required — set in `.env`)* |
| `MINIO_API_PORT` | Host and in-container S3 API port | `9000` |
| `MINIO_CONSOLE_PORT` | Host and in-container web console port | `9001` |
| `MINIO_STAGING_BUCKET` | Name of the staging bucket created on stack-up | `staging` |

---

## Staging bucket convention

The **`staging`** bucket (or whatever value you set for `MINIO_STAGING_BUCKET`) is the agreed location for **raw lake data** in this platform. Downstream modules (ingestion, Spark, analytics) should read and write raw files there unless a later epic defines additional buckets.

The bucket is created automatically by `minio-init` using `mc mb --ignore-existing`, so re-running `docker compose up` is safe when the volume already exists.

---

## Docker services

| Service | Container name | Role |
| ------- | -------------- | ---- |
| `minio` | `urbangreen-minio` | MinIO server (persistent volume at `/data`) |
| `minio-init` | `urbangreen-minio-init` | One-shot bucket initialization (`restart: "no"`) |

### Starting MinIO

From the repository root:

```bash
docker compose up -d minio
```
Or start the full stack:
```bash
docker compose up -d
```
Check status:
```bash
docker compose ps minio minio-init
docker compose logs minio-init
```
After a successful start, minio-init should show Exited (0) and the staging bucket should appear in the web console.

