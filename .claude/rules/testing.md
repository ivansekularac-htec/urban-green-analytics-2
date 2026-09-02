# Testing rules

Conventions for the `api/` test suite. They describe what the suite already
does; a new test follows them so the suite stays fast, isolated, and readable.

## General

- Tests run under `pytest` and must be deterministic, isolated, and repeatable -
  no ordering dependencies, no shared mutable state between tests.
- Test observable behaviour and stable contracts, not implementation details.
  Assert what cannot be reworded - status codes, the identifiers and fields in a
  response, which dependency was called with what - rather than the exact prose
  of a message, unless the wording itself is the contract.
- One test verifies one behaviour. A focused failure names the thing that broke.
- A short docstring earns its place when it says why the test exists; the
  assertions say what.

## Unit and API tests

- No test requires Docker or connects to a live Postgres or any external
  service. The database boundary is mocked.
- A synchronous SQLAlchemy `Session` is stubbed with `MagicMock(spec=Session)`,
  so a test that touches a repository or service passes a double rather than a
  real connection.
- API-level tests use the shared `client` fixture (FastAPI's `TestClient` with
  the startup hooks patched) rather than building a client per test. Prefer the
  existing shared fixtures over duplicating a local one.
- Override a FastAPI dependency with `app.dependency_overrides` rather than
  patching the function that provides it, where the dependency is the seam the
  test needs. Reserve `patch` for module-level side effects like the startup
  hooks that would otherwise reach a real database.

## Layout

- One subject per file: `tests/core/test_config.py` tests configuration and does
  not reach into the entry point to assert something about the app.
- The tree under `tests/` mirrors the package under `app/`, so a reader finds the
  test for a module where the module lives.
