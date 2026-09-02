# Testing

Unit tests are the default. They must be fast, deterministic, and free of
infrastructure. A test that needs Docker, Postgres, ClickHouse, Kafka, or a
network round-trip is not a unit test.

## F.I.R.S.T.

- **Fast** — milliseconds. The suite is run on every change.
- **Independent** — no shared mutable state, no order dependence. A test that
  passes alone and fails in the suite is a bug in the test.
- **Repeatable** — same result on every machine. No clocks, random seeds, or
  live services unless they are injected fakes.
- **Self-validating** — pass or fail via assertions. No manual log reading.
- **Timely** — written with the code, not after the PR.

## What a unit test is allowed to touch

- The function, class, or HTTP route under test.
- In-memory fakes and `unittest.mock` doubles at *process boundaries*
  (DB session, HTTP client, filesystem, message bus).
- The FastAPI / FastMCP app via `TestClient` (or the library's test harness)
  with those boundaries stubbed.

A unit test must not:

- start containers or wait on healthchecks
- connect to a real database or warehouse
- scrape a live `/metrics` port as its only proof (that is a manual check)
- assert on private helpers when a public behaviour already covers them

## Arrange, act, assert

One behaviour per test. Name the test after the behaviour, not the method.
Assert on the observable result (status code, body, raised exception, call to
a collaborator). Do not assert that a mock was configured; assert that the
code used it.

## Doubles

Mock the boundary, not the unit under test.

- SQLAlchemy: `MagicMock(spec=Session)` when the code under test receives a
  session. Spec-bound mocks fail loudly on typos.
- FastAPI `TestClient` always runs `lifespan`. Patch startup hooks
  (`verify_database_connection`, `SessionLocal`, seed functions) *in addition*
  to any `get_db` override. Overriding `get_db` alone still opens Postgres.
- Prefer an existing fixture from the nearest `conftest.py` over a new client
  constructed in the test file, unless the test needs to inspect the mocks
  (as the lifespan tests in `api/tests/core/test_main.py` do).

## Global process state

Prometheus registries, lru caches, and module-level singletons survive across
tests in one pytest process. If a test records a counter or histogram, an
autouse fixture must reset that registry so siblings cannot see leftover
samples. Do not add this until a test actually needs it.

## Out of scope for unit tests

Compose-level sanity (`curl localhost/metrics`, ClickHouse port 9363, Spark
servlet URLs) belongs in the ticket's manual check, not in `pytest`.