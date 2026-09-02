# Testing conventions — `api/`

Testing conventions already in use in `api/tests/`, documented so new
tests follow existing patterns instead of introducing new ones. No test
touches Docker or a live database — everything runs against mocks or
in-memory objects, so `uv run pytest` works offline.

## 1. Pure logic (functions taking a `Session`/repository directly)

Mock the one collaborator with `MagicMock(spec=<Collaborator>)` and call
the function directly. `spec=` matters — it raises `AttributeError` on a
typo'd method call that a bare `MagicMock()` would silently swallow.

```python
db = MagicMock(spec=Session)
db.scalars.side_effect = [...]

ensure_demo_users(db, settings)

db.add.assert_called_once()
```

See `tests/security/test_demo_users.py`. Same principle one layer up:
service tests mock the repository they depend on
(`MagicMock(spec=BaseRepository)`), repository tests mock the `Session`
(`tests/services/test_base.py`, `tests/repositories/test_base.py`).

## 2. Router / endpoint tests (through the real `app`)

Use the `client` fixture from `tests/routers/conftest.py` — real `app`
wrapped in `TestClient`, with the four lifespan hooks patched out.
Scoped to `tests/routers/` only; not visible elsewhere.

Requests go through real routing and dependency resolution; only the
**service** layer is mocked, via `app.dependency_overrides`. Auth
defaults to Admin via the autouse `_admin_auth_override` fixture —
override `get_current_user` for a specific role.

```python
def test_list_crops(client, service):
    app.dependency_overrides[get_crop_service] = lambda: service
    service.list.return_value = [...]

    response = client.get("/api/v1/crops")

    assert response.status_code == 200
```

Role/permission matrix tests live separately in
`tests/routers/test_authorization.py`, same fixture.

## 3. App-entrypoint tests (`main.py` — routes not under any router)

For `/`, `/health`, `/metrics` — routes defined directly on `app`. No
shared fixture; build `TestClient(app)` inline each time, wrapped in the
same four patches:

```python
with (
    patch("app.main.verify_database_connection"),
    patch("app.main.SessionLocal"),
    patch("app.main.ensure_superuser"),
    patch("app.main.ensure_demo_users"),
):
    client = TestClient(app)
    response = client.get("/metrics")
```

To observe lifespan behaviour itself, enter `TestClient(app)` as a
context manager alongside the patches instead. Lives in
`tests/core/test_main.py`.

## 4. Models & schemas

Plain unit tests in `tests/models/` and `tests/schemas/` — construct the
object directly, assert on fields or validation. No mocking, no client,
no database.

## Environment variables

`tests/conftest.py` sets required env vars with
`os.environ.setdefault(...)` before any app module is imported, so
`Settings()` builds without a real `.env`. Extend this file for new
required settings rather than setting them elsewhere.

## House style

- Module-level docstring per test file, stating what it covers.
- Test names: `test_<subject>_<expected_behaviour>`.
- `tests/<area>/test_<module>.py` mirrors `app/<area>/<module>.py`.
- Match an existing tier's pattern before introducing a new one.