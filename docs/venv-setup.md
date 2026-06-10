# Backend Local Development Setup

## Prerequisites

Before starting, ensure the following software is installed:

* Python 3.12+ (or the project-required version)
* UV package manager

Verify installation:

```bash
python --version
uv --version
```

---

## Navigate to the Backend Directory

From the repository root:

```bash
cd api
```

All remaining commands should be executed from the `api` directory.

---

## Create a Virtual Environment

Create a local virtual environment:

```bash
uv venv
```

---

## Activate the Virtual Environment

### Windows (PowerShell)

```powershell
.venv\Scripts\Activate.ps1
```

### Windows (Command Prompt)

```cmd
.venv\Scripts\activate.bat
```

### Linux / macOS

```bash
source .venv/bin/activate
```

After activation, the terminal prompt should display:

```text
(.venv)
```

---

## Install Dependencies

Install all project dependencies defined in `pyproject.toml`:

```bash
uv sync
```

Verify installation:

```bash
uv pip list
```

The command should display the installed project packages.

---

## Run the FastAPI Application

Start the development server:

```bash
uv run uvicorn app.main:app --reload
```

Expected output:

```text
INFO: Uvicorn running on http://127.0.0.1:8000
```

---

## Verify the Application

Open the Swagger UI documentation:

```text
http://localhost:8000/docs
```

You should see the FastAPI interactive API documentation page.

Optionally verify the OpenAPI schema:

```text
http://localhost:8000/openapi.json
```

---

## Deactivate the Virtual Environment

When finished:

```bash
deactivate
```

---

## Git Ignore Configuration

Ensure the virtual environment directory is excluded from source control.

Add the following entry to `.gitignore`:

```gitignore
api/.venv/
```

If the `.gitignore` file is located inside the `api` directory, use:

```gitignore
.venv/
```

---

## Troubleshooting

### Dependencies fail to install

```bash
uv self update
uv sync
```

### FastAPI application fails to start

Verify that:

* You are executing commands from the `api` directory.
* The virtual environment is activated.
* Dependencies were installed successfully.
* The application entry point exists:

```text
api/app/main.py
```

* The file contains a FastAPI application instance:

```python
from fastapi import FastAPI

app = FastAPI()
```

### Port 8000 is already in use

Run on a different port:

```bash
uv run uvicorn app.main:app --reload --port 8001
```
