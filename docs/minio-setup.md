# MinIO Setup

## Overview

The system uses [MinIO](https://min.io/) as an S3-compatible object store for the data lake. It runs as a Docker container defined in `docker-compose.yaml`. On stack-up a one-shot init container automatically creates the `staging` bucket, so other modules can read from and write to it without any manual setup.

---

## Docker Setup

### Service Configuration

* Image: built from `infra/minio/Dockerfile` (`FROM minio/minio:latest`)
* Service name: `minio`
* Container name: `urbangreen-minio`
* In-network endpoint: `http://urbangreen-minio:9000` (also reachable as `http://minio:9000` — the init container uses this alias)
* Host (S3) endpoint: `http://localhost:9000`
* Web console: `http://localhost:9001`

The API listen port and console port are driven by env vars (see below), so the ports above assume the defaults.

### Environment Variables

MinIO settings are configured in the `.env` file (see `.env.example` for the template):

| Variable               | Purpose                                             | Default   |
| ---------------------- | --------------------------------------------------- | --------- |
| `MINIO_ROOT_USER`      | Root (admin) username, also the console login       | —         |
| `MINIO_ROOT_PASSWORD`  | Root password (min. 8 characters), console login    | —         |
| `MINIO_API_PORT`       | S3 API port (host and in-network)                   | `9000`    |
| `MINIO_CONSOLE_PORT`   | Web console port                                    | `9001`    |
| `MINIO_STAGING_BUCKET` | Name of the bucket created on stack-up              | `staging` |

`MINIO_ROOT_USER` and `MINIO_ROOT_PASSWORD` have no defaults and must be set in your own `.env`. The `.env` file is gitignored and is never committed.

### Volumes

| Volume                  | Mounted at | Purpose                                     |
| ----------------------- | ---------- | ------------------------------------------- |
| `urbangreen-minio-volume` | `/data`  | Persistent object storage (buckets + data)  |

Object data survives `docker compose down`. It is only deleted by `docker compose down -v`, which removes the volume.

### Starting MinIO

Start the stack:

```bash
docker compose up -d
```

Check container status:

```bash
docker compose ps -a
```

View logs:

```bash
docker compose logs -f minio
```

Stop the stack:

```bash
docker compose down
```

---

## Bucket Initialization

The `staging` bucket is created automatically by a one-shot init container.

* Service name: `minio-init`
* Container name: `urbangreen-minio-init`
* Image: `minio/mc:latest`
* Script: `infra/minio/init/init-bucket.sh`

The init container waits until MinIO is healthy (`depends_on: condition: service_healthy`), points `mc` at the running MinIO, waits for it to be ready (`mc ready`), then creates the bucket with `mc mb --ignore-existing`. Because of `--ignore-existing`, the script is idempotent: re-running leaves an existing bucket untouched and the container exits with code `0`.

After a successful run the container shows as `Exited (0)` in `docker compose ps -a`. To inspect what it did:

```bash
docker compose logs minio-init
```

---

## Connecting to MinIO

### Web Console

Open the console in a browser and sign in with the root credentials:

| Property | Value                          |
| -------- | ------------------------------ |
| URL      | `http://localhost:9001`        |
| Username | `MINIO_ROOT_USER`              |
| Password | `MINIO_ROOT_PASSWORD`          |

The `staging` bucket should be listed under **Buckets** / **Object Browser**.

### From Another Service (in-network)

Services on the `urbangreen-network` reach MinIO over the S3 API at:

```text
http://urbangreen-minio:9000
```

Use `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD` as the access key / secret key.

### From the Host

Tools running on your machine (e.g. the `mc` client, an S3 SDK) connect to:

```text
http://localhost:9000
```

---

## Bucket Convention

`staging` is the agreed bucket for **raw lake data** going forward. New modules that land raw, unprocessed data should write to `staging` rather than creating their own buckets, so the lake has a single, predictable entry point. The bucket name is configurable via `MINIO_STAGING_BUCKET`, but `staging` is the default and the shared convention across the project.
