# Virtual Environment

## Environment Setup

The virtual environment is managed using the **uv** package manager. It is created and synchronized with the project dependencies by running:

```bash
uv sync
```

This command:

* Creates a local virtual environment (`.venv`)
* Installs all dependencies defined in `pyproject.toml`
* Updates the lock file (`uv.lock`) when necessary
* Ensures that all required Python packages are available for development and execution of the project

After the synchronization is complete, the development environment is fully prepared and work on the project can continue.

## Running the Application

To start the FastAPI application, use:

```bash
uv run uvicorn app.main:app --reload
```

Using `uv run` ensures that the command is executed within the project's virtual environment without requiring manual activation.
