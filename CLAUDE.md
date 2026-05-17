# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this codebase is

Axiom is a Python framework for orchestrating agentic workflows under deterministic, manifest-driven policy control. It is source-first (no build system) and runs against a local SQLite database with `sqlite-vec` and a local Ollama model. There is no entry-point binary in this checkout — all execution is via `python -c "..."`, the `tools/` scripts, or `pytest`.

## Common commands

```powershell
python -m pip install -r requirements.txt
python -c "from axiom.persistence.db import init_db; init_db()"     # apply schema.sql, enforce PRAGMAs
python tools/register_manifests.py                                  # validate + (re)register policy artifacts
pytest                                                              # full suite (configured by pytest.ini)
pytest tests/test_policy_engine.py                                  # focused module
pytest tests/test_policy_engine.py::test_<name>                     # single test
```

`AXIOM_DB_PATH` overrides the SQLite path (default `C:\axiom\axiom.db`). Tests that touch persistence will use whatever this resolves to — point it at a temp file when iterating to avoid mutating the dev DB.

## Architecture: how the parts fit together

The system is layered around a single guarantee: **no tool runs unless a signed, schema-validated manifest authorizes it.** Reading any one module in isolation is misleading; the boot sequence and the policy-evaluation chain are what hold the design together.

### Boot chain (read this first)
1. `axiom/persistence/db.py::init_db()` refuses to run unless `schema.sql` contains the literal markers `v1.11.4` and `tool_capability_map`. It then applies pragmas (`WAL`, `synchronous=FULL`, `busy_timeout=5000`, `foreign_keys=ON`, `cache_size=-32768`) and verifies them post-script.
2. `tools/register_manifests.py` walks `axiom/policy/{role_manifests,operator_control_manifests}/`, validates each via `ManifestBinder`, and upserts SHA256 fingerprints into `manifest_fingerprints`. **It uses UPDATE-then-INSERT, not `INSERT OR REPLACE`** — REPLACE would cascade-delete rows in `tasks`, `task_permissions`, and `plan_artifacts` that FK-reference `manifest_id`.
3. `axiom/app/bootstrap_validation.py::BootstrapValidator.run()` is the passive gate: it checks pragmas, schema version (`v1.11.4`), the `memory_item_embeddings` vec table, the loaded tool-capability map, and re-verifies every active manifest fingerprint via `boot_verifier.verify_boot_manifests()`. **It starts nothing** — no scheduler, no Telegram, no model calls.

### Policy evaluation (the seven-step authorization chain)
`axiom/core/policy_engine.py::PolicyEngine.authorize_tool_use()` enforces, in order: (1) tool_id is in the cached capability map, (2) `manifest_type` matches what the tool requires, (3) tool is in `allowed_tools`, (4) tool is not in `forbidden_tools`, (5) the capability source path resolves to a permitting value, (6) `session_controller.*` tools require an `operator_control` manifest *and* a matching `operator_command.command_name`, (7) any `additional_checks` pass. The `_run_additional_check` method is currently a permissive placeholder — gateway-specific checks (filesystem roots, network allowlists, sandbox limits) are deferred to later phases.

### Manifest types and their structural rules
There are exactly two manifest types — `role` and `operator_control` — enforced by `ManifestBinder.validate_operator_control_binding()`:
- `role` manifests **must** have `allowed_capabilities.operator_control.allowed_commands == []`.
- `operator_control` manifests **must** have `allowed_commands == [operator_command.command_name]` (exactly one, and it must match).

The eight `session_controller.*` tools have hardcoded `required_command` mappings in `manifest_binder.py::SESSION_CONTROLLER_TOOL_COMMANDS` — the binder validates the tool-capability map matches these on load.

### State machine and the "running" gate
`axiom/core/state_machine.py` defines the eight task statuses and their allowed transitions; terminal states (`completed`, `failed`, `quarantined`, `cancelled`) have empty transition sets. **Two write paths exist** in `repositories.py`:
- `update_task_status()` — raw write, no validation. Used by `TaskCommitter` after it has run its own checks.
- `transition_task_status()` — StateMachine-validated. For `next_status == "running"` it delegates to `TaskCommitter.commit_status()`, which additionally requires a non-empty `manifest_id`, calls `check_one_running_task_invariant()` (only one task per session may be running), and writes a scheduler heartbeat both before and after the update.

When changing status logic, prefer `transition_task_status()`. The raw `update_task_status()` exists for the committer's own use and for cases that have already passed validation.

### Plan-artifact safety pipeline
`PlanArtifactScannerService.scan_artifact()` (in `axiom/security/`) runs `PlanInjectionScanner.scan()` over a stored plan artifact, persists the disposition via `update_plan_artifact_scan_result()`, and transitions the parent task accordingly. `PlanInjectionScanner` currently has stub deterministic and classifier scans (always pass), but the **disposition matrix is real** and load-bearing: with `safe_pass_enabled=False` (the default), high-risk artifacts go to `quarantined` and ordinary artifacts to `needs_human_input`. Don't flip `safe_pass_enabled=True` without also wiring fingerprint verification — the v1.10.2 note in `_blocked_result` explains why high-risk artifacts cannot rehabilitate in-session.

### Local-model gateway invariant
`axiom/gateways/model_gateway.py::prepare_local_ollama_payload()` enforces that every Ollama call goes out with `think=False`. Callers may not override this — passing `think=True` raises `PolicyDeniedError`. The `qwen3:4b` model in `config/axiom.yaml` is the configured target.

## Conventions

- 4-space indentation, `from __future__ import annotations`, type hints, explicit `from axiom.* import ...` (no relative imports).
- Domain-specific exception names (`PolicyDeniedError`, `BootVerificationError`, `InvalidTransitionError`, `TaskCommitError`).
- Keep modules narrow: policy logic in `core/policy_engine.py`, persistence in `persistence/`, never mix.
- Tests mirror `axiom/` layout under `tests/` as `test_<area>.py`. Cover **both allowed and denied paths** for any policy or state-transition change — the suite's value is in those negative tests.
- After touching anything in `axiom/policy/` (manifests, schemas, the tool-capability map), rerun `python tools/register_manifests.py` then `pytest`. The fingerprints in the DB will mismatch otherwise and `BootstrapValidator` will fail on next boot.

## Runtime artifacts (do not treat as source)

`axiom.db`, `axiom.db-wal`, `axiom.db-shm`, `logs/`, `.pytest_cache/`, `__pycache__/`, and the `governance/` working tree (ratification history, handoffs, archives) are local state, not code.
