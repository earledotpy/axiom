# Repository Guidelines

## Project Structure & Module Organization

`axiom/` contains the application code. Core orchestration lives in `axiom/core/`, persistence and schema code in `axiom/persistence/`, security checks in `axiom/security/`, model integration in `axiom/gateways/`, and startup validation in `axiom/app/`. Policy schemas and security artifacts live under `axiom/policy/`.  
`tests/` mirrors the implementation with focused `test_*.py` modules. `tools/` contains maintenance scripts such as `register_manifests.py`; `config/axiom.yaml` stores runtime defaults. Treat `axiom.db`, `logs/`, and cache directories as local runtime artifacts rather than source files.

## Build, Test, and Development Commands

- `python -m pip install -r requirements.txt` — install project dependencies.
- `python -c "from axiom.persistence.db import init_db; init_db()"` — initialize the SQLite schema.
- `python tools/register_manifests.py` — validate and register active policy artifacts after schema or manifest changes.
- `pytest` — run the full test suite configured by `pytest.ini`.
- `pytest tests/test_policy_engine.py` — run one focused test module while iterating.

There is no separate build system in this checkout; development is source-first Python.

## Coding Style & Naming Conventions

Use 4-space indentation, type hints where practical, and explicit imports from `axiom.*`. Existing code favors `snake_case` for functions and modules, `PascalCase` for classes, and descriptive exception names such as `BootVerificationError`. Keep modules small and domain-specific; for example, add policy logic to `axiom/core/policy_engine.py` rather than mixing it into persistence code. No formatter or linter configuration is committed here, so preserve the surrounding style when editing.

## Testing Guidelines

Tests use `pytest`. Name files `test_<area>.py` and test functions `test_<behavior>()`, matching the current suite. Add regression tests for policy, schema, and state-transition changes; many components enforce safety invariants, so cover both allowed and denied paths. Run `pytest` before submitting changes.

## Commit & Pull Request Guidelines

Git history is unavailable in this checkout, so no repository-specific commit convention can be verified. Use concise, imperative subjects such as `Add bootstrap manifest validation` and keep each commit scoped to one concern. Pull requests should include a short summary, the reason for the change, test evidence, and any schema, manifest, or configuration impact. Include screenshots only when behavior is user-visible.

## Security & Configuration Tips

This project encodes boot-time and policy safety checks. When changing `axiom/policy/`, schema files, or manifest fingerprints, update registration artifacts deliberately and rerun both `python tools/register_manifests.py` and `pytest`. Prefer overriding local paths with environment variables such as `AXIOM_DB_PATH` instead of hard-coding machine-specific values.
