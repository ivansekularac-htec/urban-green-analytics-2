# Workflow Rules

These rules keep changes scoped, reproducible, and consistent across the
repository's independently packaged services.

## Dependency Changes

The manifest owned by a service is the source of truth for that service's
runtime. The top-level `pyproject.toml` is also maintained as a repository-wide
dependency manifest so automated dependency tooling can detect version drift.

When adding, removing, or changing a runtime dependency:

1. Update the owning manifest, such as `mcp/pyproject.toml`,
   `api/pyproject.toml`, or a service `requirements.txt`.
2. Mirror the same package and compatible version constraint in the top-level
   `pyproject.toml` under the comment block named for the owning path, for
   example `# mcp/`. Create the path block if it does not exist.
3. Keep package spelling and version intent aligned between the owning and
   top-level manifests. A service's stricter pin takes precedence when the
   top-level manifest would otherwise hide drift.
4. Regenerate every lockfile governed by a changed `pyproject.toml`. Run
   `uv lock` from the directory containing that manifest; do not edit lockfiles
   by hand.
5. Run `uv lock --check` for each changed lockfile before considering the
   dependency update complete.

Development-only dependencies stay in the owning development group unless a
task explicitly requires them in the repository-wide manifest. Dependencies
provided by a container base image remain excluded where the manifest documents
that exception.

## Verification

Run focused tests while developing, then the complete test suite for the
changed service. For Python changes, also run that service's Ruff lint and
format checks. Follow `.claude/rules/testing.md` for test isolation and testing
conventions.

For the MCP service, the completion checks are:

```bash
cd mcp
uv sync --frozen --group dev
uv run ruff check app tests
uv run ruff format --check app tests
uv run pytest
uv lock --check
```

After mirroring an MCP dependency into the repository manifest, also run from
the repository root:

```bash
uv lock --check
```
