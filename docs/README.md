## Local FastAPI Development Setup

The FastAPI backend is located in the `api/` directory.

### 1. Navigate to the API directory

```bash
cd api
```

### 2. Create the virtual environment and install dependencies

```bash
uv sync --extra dev
```

This creates a local `.venv/` directory and installs dependencies from `pyproject.toml`, including development
dependencies.

### 3. Activate the virtual environment

On Windows PowerShell:

```powershell
.\.venv\Scripts\activate
```

### 4. Verify installed packages

```bash
uv pip list
```

The output should include packages such as `fastapi`, `pytest`, and `ruff`.

### 5. Run the FastAPI application locally

```bash
uvicorn app.main:app --reload
```

The API documentation should be available at:

```text
http://localhost:8000/docs
```

### 6. Virtual environment note

The `.venv/` directory is used only for local development and must not be committed.

## 📦 MinIO Setup (Object Storage)

This project uses **MinIO** as a local S3-compatible object storage service for development and data lake ingestion.

MinIO is automatically started via Docker Compose and includes a one-shot initialization container that creates a default staging bucket.

---

## 🌐 Endpoints

### Inside Docker network (service-to-service)

Use this endpoint when accessing MinIO from other containers (API, ETL jobs, workers):
http://urbangreen-minio:9000


---

### From host machine (browser / local tools)

Use this endpoint when accessing MinIO from your local machine:
http://localhost:9000


---

## 🖥️ MinIO Console (Web UI)

MinIO provides a web-based administration console:
http://localhost:9001


### Login credentials

These are defined via environment variables:

- Username: `MINIO_ROOT_USER`
- Password: `MINIO_ROOT_PASSWORD`

---

## ⚙️ Required Environment Variables

The following environment variables must be defined in your `.env` file or system environment:

| Variable | Description |
|----------|-------------|
| `MINIO_ROOT_USER` | Root access key (username) |
| `MINIO_ROOT_PASSWORD` | Root secret key (password) |
| `MINIO_API_PORT` | S3 API port (default: 9000) |
| `MINIO_CONSOLE_PORT` | Web console port (default: 9001) |
| `MINIO_STAGING_BUCKET` | Default bucket created on startup |

---

## 🪣 Staging Bucket Convention

On startup, the system automatically creates a **staging bucket**:
local/${MINIO_STAGING_BUCKET}


### Purpose

The `staging` bucket is the **standard entry point for raw data ingestion** into the system.

All new pipelines (sensor data, transactional data, external feeds) should initially land in this bucket before being processed into downstream layers (cleaned, aggregated, or analytics-ready datasets).

### Behavior

- The bucket is created automatically by a one-shot init container.
- The process is **idempotent** (safe to run multiple times).
- If the bucket already exists, no action is taken.

---

## 🔁 Initialization Behavior

When running:

```bash
docker compose up