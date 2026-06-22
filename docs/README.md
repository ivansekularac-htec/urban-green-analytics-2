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

---

## MinIO Storage Setup

MinIO is used in this project as local S3-compatible storage. It provides a development-friendly replacement for cloud
object storage and is mainly used for storing raw input files before they are processed by the platform.

### 1. Service URLs

MinIO can be reached through different URLs depending on where the client is running.

Use the Docker network URL when another container needs to communicate with MinIO:

```text
http://urbangreen-minio:9000
```

Use the localhost URL when accessing MinIO from your host machine, for example from the browser or a locally running
script:

```text
http://localhost:9000
```

### 2. Web Console

The MinIO browser console is exposed on:

```text
http://localhost:9001
```

Use the root credentials defined in the environment file to log in:

```env
MINIO_ROOT_USER
MINIO_ROOT_PASSWORD
```

### 3. Environment Configuration

The MinIO setup depends on the following environment variables:

```env
MINIO_ROOT_USER
MINIO_ROOT_PASSWORD
MINIO_API_PORT
MINIO_CONSOLE_PORT
MINIO_STAGING_BUCKET
```

These values are usually defined in the root `.env` file and mirrored in `.env.example` with safe placeholder values.

### 4. Staging Bucket

Raw files are uploaded to a dedicated staging bucket before any ingestion or transformation step runs.

The default bucket name is:

```text
staging
```

The bucket name is controlled through:

```env
MINIO_STAGING_BUCKET
```

This bucket is intended for incoming files such as CSV exports, JSON files, sensor data exports, and other raw datasets
that still need to be validated or transformed.

### 5. Starting MinIO

Start the full local infrastructure stack from the project root:

```bash
docker compose up -d --build
```

Then confirm that the MinIO services are running:

```bash
docker compose ps
```

After the services start, open the console:

```text
http://localhost:9001
```

The `urbangreen-minio-init` container is responsible for creating the staging bucket automatically during startup.
