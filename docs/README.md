## Local FastAPI Development Setup

The FastAPI backend is located in the `api/` directory.

### 1. Navigate to the API directory

```bash
cd api
```

### 2. Create the virtual environment and install dependencies

```bash
uv sync --group dev
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
