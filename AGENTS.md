# Repository Guidelines

## Project Structure & Module Organization

`axiom/` contains the application code. Core orchestration lives in `axiom/core/`, persistence and schema logic in `axiom/persistence/`, security checks in `axiom/security/`, model and environment integrations in `axiom/gateways/`, and startup validation in `axiom/app/`. Policy schemas and security artifacts live under `axiom/policy/`.

`tests/` mirrors implementation areas with focused `test_*.py` modules. `tools/` contains maintenance scripts such as `register_manifests.py`, `config/axiom.yaml` stores runtime defaults, and `governance/` holds project governance and ratification material rather than executable code. Treat `axiom.db`, `logs/`, `.pytest_cache/`, and local virtual environments as runtime artifacts, not source files.

## AXIOM Governance Role

For AXIOM governance work, Codex serves as Implementation Specialist and Troubleshooter. Jeremy is the Operator and final authority. Before changing governance files, read `governance/02_cli_surfaces/codex/AGENTS.governance.md` and the active live spine in `governance/01_live_spine/`. Preserve `governance/06_archives/` and `governance/07_deprecated_legacy/` as historical or deprecated material unless Jeremy explicitly authorizes a migration.

## Build, Test, and Development Commands

- `python -m pip install -r requirements.txt` — install project dependencies.
- `python -c "from axiom.persistence.db import init_db; init_db()"` — initialize the SQLite schema.
- `python tools/register_manifests.py` — validate and register active policy artifacts after manifest or schema changes.
- `pytest` — run the full suite configured by `pytest.ini`.
- `pytest tests/test_policy_engine.py` — run one focused module while iterating.

There is no separate build system in this checkout; development is source-first Python.

## Coding Style & Naming Conventions

Use 4-space indentation, type hints where practical, and explicit imports from `axiom.*`. Existing code favors `snake_case` for functions and modules, `PascalCase` for classes, and descriptive exception names such as `BootVerificationError`. Keep modules small and domain-specific; for example, place policy behavior in `axiom/core/policy_engine.py` rather than mixing it into persistence code. No formatter or linter configuration is committed, so preserve the surrounding style when editing.

## Testing Guidelines

Tests use `pytest`. Name files `test_<area>.py` and functions `test_<behavior>()`, matching the current suite. Add regression coverage for policy, schema, and state-transition changes; many components enforce safety invariants, so cover both allowed and denied paths. Run `pytest` before submitting changes.

## Commit & Pull Request Guidelines

The visible Git history is too small to establish a repository-specific commit convention. Use concise, imperative subjects such as `Add bootstrap manifest validation`, and keep each commit scoped to one concern. Pull requests should include a short summary, rationale, test evidence, and any schema, manifest, or configuration impact. Add screenshots only for user-visible behavior changes.

## Security & Configuration Tips

This project encodes boot-time and policy safety checks. When changing `axiom/policy/`, schema files, or manifest fingerprints, rerun both `python tools/register_manifests.py` and `pytest`. Prefer environment overrides such as `AXIOM_DB_PATH` over hard-coded machine-specific paths.
