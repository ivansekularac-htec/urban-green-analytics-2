---
paths:
  - "api/tests/**/*.py"
---

# API testing rules

These rules define the testing conventions for the Urban Green Analytics API.
Unit tests are the default and must remain fast, deterministic, and isolated.

## Test boundaries

- Do not require Docker, PostgreSQL, ClickHouse, Kafka, or another live service.
- Do not make network requests from unit tests.
- Replace infrastructure boundaries with in-memory fakes or mock objects.
- Name tests after observable behavior rather than implementation details.
- Ensure every test can pass alone and in any suite execution order.

## FastAPI endpoint tests

- Exercise routes through FastAPI's `TestClient`.
- Prefer an existing fixture from the nearest `conftest.py` when one applies.
- Patch lifespan database checks and user-seeding functions when creating a client.
- Remember that entering `TestClient` as a context manager runs the app lifespan.
- Assert status codes, response headers, and response bodies as public contracts.
- Explicitly omit authorization headers when verifying a public endpoint.
- Verify OpenAPI inclusion or exclusion when schema visibility is a requirement.

## Database isolation

- Never create a real database engine for an ordinary unit test.
- Use `MagicMock(spec=Session)` when code receives a synchronous SQLAlchemy session.
- A spec-bound mock should fail when a nonexistent `Session` method is used.
- Override `get_db` when the endpoint under test has a database dependency.
- Patch `SessionLocal` separately when application lifespan code can open a session.
- Mock only the query results and session behavior required by the test.

## Mocking guidelines

- Mock external boundaries, not the unit whose behavior is being tested.
- Prefer dependency overrides for FastAPI dependencies when practical.
- Use `patch` where the dependency is looked up, not where it was originally defined.
- Assert meaningful collaborator calls only when they are part of the behavior.
- Do not assert that a mock was merely configured by the test itself.

## Metrics and global state

- Prometheus registries and module-level singletons survive within a pytest process.
- Generate a real request before asserting that an HTTP metric was emitted.
- Assert stable metric names such as `http_requests_total`.
- Assert route labels when correct route-template resolution is required.
- Do not depend on exact counter values left behind by unrelated tests.
- Keep Docker-based scraping and manual `curl` checks outside the unit test suite.

## Verification commands

Run commands from the `api/` directory:

```bash
uv run pytest
uv run ruff check app tests
uv run ruff format --check app tests
```

```bash
uv run pytest tests/core/test_main.py -v
```
