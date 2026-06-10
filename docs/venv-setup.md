## Local Development Setup

### Prerequisites

* Python 3.10+
* uv package manager

### Create and synchronize virtual environment

```bash
cd api

uv sync
```

### Run the application

```bash
uv run uvicorn app.main:app --reload
```

The application will be available at:

```text
http://localhost:8000
```

Interactive API documentation:

```text
http://localhost:8000/docs
```

### Verify installed dependencies

```bash
pip list
```
