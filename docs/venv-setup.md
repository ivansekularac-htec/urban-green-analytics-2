# Urban Green API

## Overview

The Urban Green API is a FastAPI backend application for the Urban Green Farms project.

The project uses FastAPI for building REST APIs and uv for dependency management and virtual environment creation.

---

## Local Development Setup

### Prerequisites

Required tools:

* Python 3.10 or newer
* uv package manager

### Install Dependencies

Install all project dependencies:

```bash
uv sync
```

This command creates a local virtual environment (`.venv`) if it doesn't already exist and installs all dependencies defined in `pyproject.toml`.

### Running the Application

Start the server:

```bash
uv run uvicorn app.main:app --reload
```

The application will be available at:

* API: http://localhost:8000
* Swagger UI: http://localhost:8000/docs

---

## Project Structure

```text
api/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   └── routers/
├── tests/
├── .env.example
└── pyproject.toml
```

---

## Dependencies

Project dependencies are managed through `pyproject.toml`.

Current core dependencies:

* FastAPI
* Uvicorn

Development tools:

* Pytest
* Ruff