# Local Development Setup

## Prerequisites

* Python 3.10+
* uv

Verify the installation:

```bash
python --version
uv --version
```

## Create Virtual environment and Install Dependencies

Create Virtual environment and Install all project dependencies defined in `pyproject.toml`:

```bash
uv sync
```

For development dependencies:

```bash
uv sync --extra dev
```

## Verify Installed Packages

List installed packages:

```bash
uv pip list
```

Verify that the required packages are installed, including:

* fastapi
* uvicorn
* pytest
* ruff

## Run the Application

Start the FastAPI development server:

```bash
uv run uvicorn app.main:app --reload
```

The application should start successfully and be available at:

* API: http://localhost:8000
* Swagger UI: http://localhost:8000/docs
* ReDoc: http://localhost:8000/redoc

## Deactivate the Virtual Environment

When finished working:

```bash
deactivate
```
