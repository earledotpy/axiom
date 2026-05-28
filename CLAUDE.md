# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this codebase is

Axiom is a Python framework for orchestrating agentic workflows under deterministic, manifest-driven policy control. It is source-first (no build system) and runs against a local SQLite database with `sqlite-vec` and a local Ollama model. There is no entry-point binary in this checkout — all execution is via `python -c "..."`, the `tools/` scripts, or `pytest`.

The canonical baseline doc is `AXIOM_Implementation_v1.13.md` (note: the *schema* marker is `v1.11.4` — different versioning axes, both correct). `AGENTS.md` carries the full operator brief; this file is the working subset.

## AXIOM governance role

Claude Code serves as Governance Auditor and Specification Critic. Jeremy is the Operator and final authority. Before reviewing or changing governance files, read `governance/02_cli_surfaces/claude_code/CLAUDE.governance.md` and the active live spine in `governance/01_live_spine/`. Treat `governance/06_archives/` as historical evidence unless Jeremy explicitly authorizes a migration.

## Operational posture (this is the intended state — do not "fix" it)

Axiom is **local-first, fail-closed, and non-autonomous by design**. The healthy steady state is:

```
autonomous_allowed = False        # NOT a defect — the intended safe state
safe_pass_enabled  = False        # plan artifacts fail closed (see scanner pipeline below)
operational_mode   = fail_closed_non_autonomous
```

Do not weaken an invariant to make a test pass — patch code/tests toward the canonical schema and contracts, never the reverse. Every mismatch fails closed: SHA256, manifest, model fingerprint, operator-control cross-field.

**Prohibited without Jeremy's explicit authorization** (do not implement, enable, or even test-drive): autonomous operation; safe-pass enablement; model-profile promotion; classifier-calibration approval; real Ollama/cloud model calls; real `NetworkGateway` fetches; real `SandboxGateway` process execution; real `MemoryGateway` embedding writes/queries; the Telegram/operator control plane; the agent layer; a persistent scheduler service; automatic scheduler→executor integration. When unsure whether a step expands runtime authority, treat it as prohibited and ask.

**Model profile rule:** the configured `qwen3:4b` host cannot persist `PARAMETER think false`, so its profile stays `registration_status=candidate`, `is_current=0`. Never manually mark it current — `think=False` is enforced at runtime by `ModelGateway` instead (see the local-model gateway invariant below).

## Common commands

```powershell
python -m pip install -r requirements.txt
python -c "from axiom.persistence.db import init_db; init_db()"     # apply schema.sql, enforce PRAGMAs
python tools/register_manifests.py                                  # validate + (re)register policy artifacts
pytest                                                              # full suite (configured by pytest.ini)
pytest tests/test_policy_engine.py                                  # focused module
pytest tests/test_policy_engine.py::test_<name>                     # single test
```

`AXIOM_DB_PATH` overrides the SQLite path (default `C:\axiom\axiom.db`). **Tests never touch the dev DB:** the autouse `isolate_axiom_db` fixture in `tests/conftest.py` points `AXIOM_DB_PATH` at a fresh per-test `tmp_path`, reloads `axiom.persistence.db`, runs `init_db()`, and seeds the `tool_capability_map` fingerprint row that FK-bound test data needs. Use that fixture pattern for any test needing DB state — never write a test that mutates `C:\axiom\axiom.db`. Only set `AXIOM_DB_PATH` yourself for ad-hoc `python -c`/`tools/` iteration.

### Operational `tools/` scripts

The scheduler/execution pipeline is driven through CLI wrappers in `tools/` (each adds the repo root to `sys.path`, takes a `session_id`, and prints JSON):

```powershell
python tools/bootstrap_check.py                       # passive boot gate (BootstrapValidator)
python tools/autonomous_readiness_check.py            # autonomous_gate decision
python tools/execution_readiness_check.py             # re-run the tool-check battery
python tools/dispatch_next_task.py <session_id>       # start one eligible pending task
python tools/scheduler_tick.py <session_id>           # one gated tick (readiness -> dispatch -> audit)
python tools/run_scheduler_loop.py <session_id>       # bounded multi-tick loop
python tools/run_manual_noop_cycle.py <session_id>    # full dispatch -> start -> complete no-op cycle
python tools/stage_noop_task.py / start_task.py / complete_task.py / fail_task.py / cancel_task.py
python tools/status_check.py / supervisor_health_check.py / repair_session_state.py
```

Note: `tools/run_scheduer_loop.py` (typo) and `tools/run_scheduler_loop.py` both exist — use the correctly-spelled one.

### Verification battery (read-only — run before proposing/after integrating work)

These shell out read-only and print JSON; they are the canonical preflight and the bar for "is the tree healthy":

```powershell
python tools/verify_foundation.py        # foundation_passed + fail-closed coherence
python tools/audit_task_lifecycle.py     # lifecycle audit (also reports the latest session_id)
python tools/audit_task_execution.py     # execution audit
python tools/audit_policy_security.py    # policy/security audit
pytest tests -v                          # full regression
```

Healthy shape: `foundation_passed: True`, `operational_mode: fail_closed_non_autonomous`, `autonomous_allowed: False`, `safe_pass_enabled: False`, `fail_closed_coherent: True`, all three audits passed. Don't claim a check passed without current live output showing it; diagnose the first real failure, not downstream noise.

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

### Scheduler and task-execution pipeline
This is the active build area (the recent "manual scheduler-dispatched noop execution cycle" commits) and layers strictly on top of the policy/state-machine guarantees above:

- **Task lifecycle ops** are one module each, each returning a frozen result dataclass: `task_starter.py` (-> `running`, via `task_lifecycle_guard.transition_task_to_running`), `task_completer.py`, `task_failer.py`, `task_canceller.py`. `task_lifecycle_service.py` (`get_task_lifecycle_service()`) is the single facade that wraps all four plus `task_lifecycle_audit`. Call the service, not the individual ops.
- **Dispatch**: `scheduler_dispatcher.py::dispatch_next_task(session_id)` selects the next `pending` task (FIFO), refuses if the session already has a running task (the one-running invariant), and starts exactly one task through the lifecycle service.
- **Readiness gate**: `autonomous_gate.py::evaluate_autonomous_readiness()` builds an `AutonomousReadinessDecision` from `app/status_report.py`; `execution_readiness.py` shells out to the `tools/` check battery as a deeper pre-flight.
- **Tick**: `scheduler_tick.py::scheduler_tick()` is one gated step — evaluate readiness, repair session state if needed, dispatch, audit. `scheduler_loop.py` runs a bounded sequence of ticks, stopping on any `TERMINAL_TICK_STATUSES` (`blocked`/`idle`/`running`/`error`).
- **No-op execution path** (for harness/testing without a real model): `noop_task_executor.py` runs start->complete on a staged no-op task; `manual_noop_cycle.py::run_manual_noop_cycle()` ties scheduler tick + no-op execution + `task_execution_audit` into one end-to-end cycle. `noop_task_stager.py` creates the staged task.
- `scheduler.py` holds the low-level invariant helpers (`count_running_tasks`, `RunningTaskInvariant`); `resource_limits.py` records usage and can transition a task out on limit breach.

### Plan-artifact safety pipeline
`PlanArtifactScannerService.scan_artifact()` (in `axiom/security/`) runs `PlanInjectionScanner.scan()` over a stored plan artifact, persists the disposition via `update_plan_artifact_scan_result()`, and transitions the parent task accordingly. `PlanInjectionScanner` currently has stub deterministic and classifier scans (always pass), but the **disposition matrix is real** and load-bearing: with `safe_pass_enabled=False` (the default), high-risk artifacts go to `quarantined` and ordinary artifacts to `needs_human_input`. Don't flip `safe_pass_enabled=True` without also wiring fingerprint verification — the v1.10.2 note in `_blocked_result` explains why high-risk artifacts cannot rehabilitate in-session.

### Gateways
`axiom/gateways/` wraps every external interaction behind a policy-checked façade, each with its own deny exceptions: `model_gateway.py` (local Ollama), `memory_gateway.py` (sqlite-vec memory store, batch-limited), `network_gateway.py` (`NetworkPolicy` allowlist -> `NetworkAccessDeniedError`), `sandbox_gateway.py` (`SandboxPolicy` -> `SandboxExecutionDeniedError`). `ollama_prereq.py` checks the model is present before runs.

### Local-model gateway invariant
`axiom/gateways/model_gateway.py::prepare_local_ollama_payload()` enforces that every Ollama call goes out with `think=False`. Callers may not override this — passing `think=True` raises `PolicyDeniedError`. The `qwen3:4b` model in `config/axiom.yaml` is the configured target.

## Conventions

- 4-space indentation, `from __future__ import annotations`, type hints, explicit `from axiom.* import ...` (no relative imports).
- Domain-specific exception names (`PolicyDeniedError`, `BootVerificationError`, `InvalidTransitionError`, `TaskCommitError`, `SchedulerDispatchError`, etc.) — one per module is the norm.
- New behavior is a narrow module returning a frozen `@dataclass` result, composed by a higher-level service/facade. Keep policy logic in `core/policy_engine.py`, persistence in `persistence/`, never mix.
- Tests mirror `axiom/` layout under `tests/` as `test_<area>.py`. Cover **both allowed and denied paths** for any policy or state-transition change — the suite's value is in those negative tests.
- After touching anything in `axiom/policy/` (manifests, schemas, the tool-capability map), rerun `python tools/register_manifests.py` then `pytest`. The fingerprints in the DB will mismatch otherwise and `BootstrapValidator` will fail on next boot.

## Runtime artifacts (do not treat as source)

`axiom.db`, `axiom.db-wal`, `axiom.db-shm`, `logs/`, `.pytest_cache/`, `__pycache__/`, the `venv/` tree, and the `governance/` working tree (ratification history, handoffs, archives) are local state, not code. The repo also accumulates ad-hoc `inspect_*.py` scripts at the root for one-off DB inspection — not part of the framework.
