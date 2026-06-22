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

## MinIO Storage Setup

The Urban Green Analytics Platform uses MinIO as an S3-compatible object storage service.

### 1. MinIO Endpoints

#### Docker Network Endpoint

Containers running inside the Docker Compose network should connect to MinIO using:

```text
http://urbangreen-minio:9000
```

#### Host Endpoint

Applications running on the host machine should connect using:

```text
http://localhost:9000
```

### 2. MinIO Web Console

The MinIO web console is available at:

```text
http://localhost:9001
```

Login credentials are configured through environment variables:

```env
MINIO_ROOT_USER
MINIO_ROOT_PASSWORD
```

### 3. Required Environment Variables

The following environment variables are required for the MinIO setup:

```env
MINIO_ROOT_USER
MINIO_ROOT_PASSWORD
MINIO_API_PORT
MINIO_CONSOLE_PORT
MINIO_STAGING_BUCKET
```

### 4. Staging Bucket

The platform uses a dedicated staging bucket for raw data ingestion.

Bucket name:

```text
staging
```

This bucket is configured through:

```env
MINIO_STAGING_BUCKET
```

All raw datasets, CSV files, JSON files, sensor exports, and other incoming data should be uploaded to the staging bucket before downstream processing and transformation.

### 5. Starting the Services

Build and start the infrastructure stack:

```bash
docker compose up -d --build
```

Verify that MinIO is running:

```bash
docker compose ps
```

Open the web console:

```text
http://localhost:9001
```

After startup, the staging bucket should be automatically created by the `urbangreen-minio-init` container.

