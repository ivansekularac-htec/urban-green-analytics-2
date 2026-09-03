# Testing Rules

These rules define the testing conventions for the UrbanGreen API.

## General

* Use `pytest` for Python tests.
* Tests must be deterministic, isolated, and repeatable.
* Prefer testing observable behavior and stable contracts over implementation details.
* Avoid assertions on exact prose or error-message wording unless the wording itself is part of the contract.
* Keep tests focused: one test should primarily verify one behavior.
* Add concise docstrings to tests and reusable fixtures where they clarify intent.

## Unit Tests

* Unit tests must not require Docker.
* Unit tests must not connect to a live PostgreSQL database or any external service.
* Mock external dependencies at the application boundary.
* Use `MagicMock(spec=Session)` when a synchronous SQLAlchemy `Session` is required.
* Prefer existing shared fixtures over creating duplicate local fixtures.
* Use the shared `client` fixture from `tests/conftest.py` for API-level unit tests unless a test requires intentionally different application setup.
* Override FastAPI dependencies rather than patching internal implementation details where practical.

## API Tests

* Exercise endpoints through the FastAPI test client.
* Verify HTTP status codes and response contracts.
* Verify authentication and authorization behavior where relevant.
* For public endpoints, explicitly verify that authentication is not required when that is part of the contract.
* When testing route-aware middleware or instrumentation, assert stable route templates or labels rather than internal middleware implementation details.
* Verify OpenAPI inclusion or exclusion when schema visibility is part of the endpoint contract.

## Database Mocking

* Do not create a real database engine for ordinary unit tests.
* Use mocked SQLAlchemy sessions and dependency overrides.
* Mock only the behavior required by the test.
* Use `spec` or `spec_set` when practical so mocks follow the real interface.
* Do not make tests depend on database state left by another test.

## Assertions

Prefer assertions on stable contracts such as:

* HTTP status codes
* response schema and required fields
* route paths and templates
* authentication behavior
* dependency interactions
* validation behavior
* emitted metrics and metric labels
* workflow ordering when ordering is part of the contract
* query counts when they are a deliberate performance or correctness constraint

Avoid brittle assertions on:

* exact logging prose
* exact exception text
* internal helper implementation
* incidental ordering of unrelated data
* formatting that is not part of the public contract

## Fixtures

* Put broadly reusable fixtures in `tests/conftest.py`.
* Keep feature-specific fixtures close to their tests when they are not reusable.
* Do not duplicate a shared fixture with the same responsibility.
* Fixtures must clean up dependency overrides or other global application state after use.

## Running Tests

Run a focused test while developing:

```bash
uv run pytest tests/path/to/test_file.py -v
```

Before considering a change complete, run the full API test suite:

```bash
uv run pytest
```

Run Ruff when the change affects Python code:

```bash
uv run ruff check .
```

## New Features

* Every new feature should include tests for its important behavior.
* For bug fixes, add or update a test that would fail without the fix whenever practical.
