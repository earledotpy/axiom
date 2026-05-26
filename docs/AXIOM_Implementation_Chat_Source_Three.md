# AXIOM Implementation Source File — Chat Session Addendum

Date: 2026-05-17  
Project root: `C:\axiom`  
Canonical base: `AXIOM_Implementation_v1.13`  
Session scope: Stabilization patches, manual scheduler/no-op execution harness, execution audit, and command-index alignment.

This file records what was implemented during this chat session. It is not a replacement for `AXIOM_Implementation_v1.13`; it is a source addendum describing the code changes completed on top of the current AXIOM repository.

---

## Final verified state

The final state at the end of this chat was verified by full regression and operational checks.

Expected verified shape:

```text
full regression tests: passed

foundation_passed: True
operational_mode: fail_closed_non_autonomous
session_repair_completed: True
autonomous_allowed: False
fail_closed_coherent: True

supervisor_health:
checked: True
reason: supervisor_health_ok
healthy: True
scheduler_stale: False
running_count: 0
active_task_present: False
active_task_status: None

task_lifecycle_audit:
passed: True
scope: latest_session
violations: none

task_execution_audit:
passed: True

blocking_reasons:
- no_current_trusted_model_profile
- safe_pass_disabled
- autonomous_operation_disabled
```

The system remains intentionally fail-closed and non-autonomous.

---

## Commands used for final verification

```powershell
Set-Location C:\axiom
.\venv\Scripts\Activate.ps1

pytest tests -v
python tools\verify_foundation.py
python tools\audit_task_lifecycle.py
python tools\audit_task_execution.py
python tools\supervisor_health_check.py <SESSION_ID>
```

If the latest session changes, obtain it with:

```powershell
python tools\audit_task_lifecycle.py
```

Then run:

```powershell
python tools\supervisor_health_check.py <SESSION_ID>
```

---

# 1. Test DB Isolation

## Problem

Tests were contaminating the real operational database:

```text
C:\axiom\axiom.db
```

Observed contamination included:

```text
- fake sessions
- fake current model profiles
- safe_pass_enabled = 1
- autonomous_operation_enabled = 1
- many historical running test tasks
```

This made supervisor health, snapshot, handoff, and model-profile reporting unreliable.

## Files changed

```text
tests/conftest.py
tests/test_test_db_isolation.py
```

## Implemented behavior

Pytest now runs against an isolated temporary database by setting `AXIOM_DB_PATH` per test.

The fixture:

```text
- sets AXIOM_DB_PATH to tmp_path / axiom_test.db
- reloads axiom.persistence.db after setting the environment variable
- initializes the canonical schema
- seeds security.tool_capability_map.v1 into manifest_fingerprints
- computes the real SHA256 of axiom/policy/security_artifacts/tool_capability_map.json
```

## Important implementation shape

```python
from __future__ import annotations

import hashlib
import importlib
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
TOOL_CAPABILITY_MAP = (
    ROOT / "axiom" / "policy" / "security_artifacts" / "tool_capability_map.json"
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def seed_tool_capability_map_manifest(db_module) -> None:
    with db_module.get_connection() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO manifest_fingerprints
            (manifest_id, manifest_type, relative_path, sha256, schema_version,
             manifest_version, role_name, command_name, approved_by_panel_version,
             active, registered_by_tool_version)
            VALUES (?, ?, ?, ?, ?, ?, NULL, NULL, ?, 1, ?)
            """,
            (
                "security.tool_capability_map.v1",
                "tool_capability_map",
                "policy/security_artifacts/tool_capability_map.json",
                sha256_file(TOOL_CAPABILITY_MAP),
                "axiom.tool_capability_map.v1",
                "1.0.0",
                "test",
                "test_fixture",
            ),
        )


@pytest.fixture(autouse=True)
def isolate_axiom_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    test_db = tmp_path / "axiom_test.db"
    monkeypatch.setenv("AXIOM_DB_PATH", str(test_db))

    import axiom.persistence.db as db

    importlib.reload(db)
    db.init_db()
    seed_tool_capability_map_manifest(db)

    yield

    importlib.reload(db)
```

## Regression test

Added test to ensure tests are not using the operational DB.

```python
from __future__ import annotations

import os
from pathlib import Path

from axiom.persistence import db


def test_tests_do_not_use_operational_database():
    operational_db = Path(r"C:\axiom\axiom.db").resolve()
    active_db = Path(os.environ["AXIOM_DB_PATH"]).resolve()

    assert active_db != operational_db
    assert db.DB_PATH.resolve() != operational_db
```

---

# 2. Idle Supervisor Heartbeat Repair

## Problem

After stale running task repair, latest session could be clean and idle but supervisor health still reported:

```text
reason: scheduler_heartbeat_stale_or_missing
healthy: False
scheduler_stale: True
running_count: 0
active_task_present: False
```

The session was lifecycle-clean, but the idle scheduler heartbeat was stale.

## Files changed

```text
axiom/core/scheduler.py
tools/repair_session_state.py
tests/test_repair_session_state.py
tests/test_scheduler_foundation.py
```

## Implemented behavior

`repair_session_state.py` now writes a fresh ready heartbeat when the latest session has no running task.

## `scheduler.py` heartbeat helper expansion

`write_scheduler_heartbeat()` was expanded to support richer heartbeat fields while preserving backward-compatible default:

```python
def write_scheduler_heartbeat(
    session_id: int,
    scheduler_state: str = "running",
    last_action: str = "heartbeat",
    active_task_id: int | None = None,
    active_chain_id: str | None = None,
    blocking_operation_type: str | None = None,
    tick_completed: bool = True,
    blocking_operation_completed: bool = True,
) -> int:
    ...
```

Important compatibility fix:

```text
default last_action remains "heartbeat"
```

## `repair_session_state.py` helper

```python
from axiom.core.scheduler import write_scheduler_heartbeat


def refresh_ready_heartbeat_if_idle(session_id: int | None) -> int | None:
    if session_id is None:
        return None

    with get_connection() as conn:
        running = conn.execute(
            """
            SELECT task_id
            FROM tasks
            WHERE session_id = ? AND status = 'running'
            LIMIT 1
            """,
            (session_id,),
        ).fetchone()

    if running is not None:
        return None

    return write_scheduler_heartbeat(
        session_id=session_id,
        scheduler_state="ready",
        last_action="session_repaired",
        active_task_id=None,
        active_chain_id=None,
        blocking_operation_type="session_repair",
        tick_completed=True,
        blocking_operation_completed=True,
    )
```

## Repair flow change

At the end of `repair_session_state()`:

```python
heartbeat_id = refresh_ready_heartbeat_if_idle(session_id)

return {
    "tool_version": TOOL_VERSION,
    "profile_label": profile_label,
    "current_trusted_profile_present": has_current_profile,
    "latest_profile": latest_profile,
    "changes": changes,
    "session": repaired_session,
    "heartbeat_id": heartbeat_id,
}
```

Important semantic decision:

```text
Refreshing the heartbeat is not appended to changes.
```

Reason: `changes` remains session-state repair changes only. Heartbeat refresh is operational maintenance.

---

# 3. Model-Profile Trust Boundary

## Problem

`tools/register_model_fingerprint.py` could silently promote profiles too aggressively, including default candidate registrations becoming current.

Unsafe behavior found:

```python
if requested_registration_status == "candidate":
    return 1, "current"
```

## Files changed

```text
tools/register_model_fingerprint.py
tests/test_register_model_fingerprint.py
```

## Implemented behavior

Registration rules now enforce:

```text
candidate stays candidate
current requires explicit registration_status="current"
current requires thinking_mode="disabled"
current requires existing passed calibration run
pending_calibration is rejected for trusted/current registration
missing calibration is rejected
failed calibration is rejected
unknown thinking mode cannot become current
```

## Replacement registration-state logic

```python
def resolve_registration_state(
    profile_thinking_mode: str,
    requested_registration_status: str,
) -> tuple[int, str]:
    """
    Resolve model-profile registration state without silently promoting
    candidate profiles.

    Rules:
    - thinking_mode='unknown' can only be candidate/non-current.
    - requested candidate remains candidate/non-current.
    - requested current requires thinking_mode='disabled'.
    - superseded/rejected are always non-current.
    """
    if requested_registration_status == "candidate":
        return 0, "candidate"

    if requested_registration_status in {"superseded", "rejected"}:
        return 0, requested_registration_status

    if requested_registration_status == "current":
        if profile_thinking_mode != "disabled":
            return 0, "candidate"
        return 1, "current"

    return 0, "candidate"
```

## Strict calibration requirement

`ensure_classifier_calibration_run()` now requires an existing passed calibration row and does not synthesize calibration records.

```python
def ensure_classifier_calibration_run(
    calibration_run_id: str,
    model: str,
    host: str,
) -> None:
    if calibration_run_id == "pending_calibration":
        raise ModelFingerprintRegistrationError(
            "Calibration run is pending; refusing trusted model registration."
        )

    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT calibration_run_id, model_name, ollama_host, passed
            FROM classifier_calibration_runs
            WHERE calibration_run_id = ?
            """,
            (calibration_run_id,),
        ).fetchone()

    if row is None:
        raise ModelFingerprintRegistrationError(
            f"Calibration run not found: {calibration_run_id}"
        )

    if row["model_name"] != model:
        raise ModelFingerprintRegistrationError(
            "Calibration run model mismatch: "
            f"expected {model}, got {row['model_name']}"
        )

    if row["ollama_host"] != host:
        raise ModelFingerprintRegistrationError(
            "Calibration run host mismatch: "
            f"expected {host}, got {row['ollama_host']}"
        )

    if int(row["passed"]) != 1:
        raise ModelFingerprintRegistrationError(
            f"Calibration run has not passed: {calibration_run_id}"
        )
```

---

# 4. Snapshot / Handoff Profile Scoping

## Problem

Snapshot/handoff model-profile reporting was global. A default snapshot could report unrelated test profiles.

## Files changed

```text
tools/snapshot_project_state.py
tools/generate_handoff.py
tests/test_snapshot_project_state.py
tests/test_generate_handoff.py
```

## Snapshot fix

`_latest_model_profiles()` now filters by `profile_label`.

```python
def _latest_model_profiles(
    profile_label: str = "default",
    limit: int = 5,
) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT profile_id, profile_label, model_name, ollama_host,
                   ollama_model_tag, ollama_model_digest, quantization,
                   parameter_size, model_family, model_format, thinking_mode,
                   thinking_mode_rule_version, calibration_run_id,
                   is_current, registration_status, registered_at
            FROM model_profile_fingerprints
            WHERE profile_label = ?
            ORDER BY profile_id DESC
            LIMIT ?
            """,
            (profile_label, limit),
        ).fetchall()

    return [dict(row) for row in rows]
```

`build_project_state_snapshot()` now calls:

```python
"latest_model_profiles": _latest_model_profiles(profile_label=profile_label),
```

## Handoff robustness fix

```python
def _latest_model_profile(snapshot: dict[str, Any]) -> dict[str, Any] | None:
    profile_label = snapshot.get("profile_label", "default")
    profiles = (
        snapshot.get("database_state", {})
        .get("latest_model_profiles", [])
    )

    for profile in profiles:
        if profile.get("profile_label") == profile_label:
            return profile

    return None
```

---

# 5. Direct Lifecycle CLI Gates

## Problem

Direct CLI tools could advance lifecycle state while autonomous readiness was blocked.

## Files changed

```text
tools/start_task.py
tools/dispatch_next_task.py
tests/test_task_starter.py
tests/test_scheduler_dispatcher.py
```

## Implemented behavior

The direct CLIs now require explicit override while autonomous readiness is unavailable:

```powershell
python tools\start_task.py <TASK_ID> --manual-test-override
python tools\dispatch_next_task.py <SESSION_ID> --manual-test-override
```

Without the flag, they block and return exit code `1`.

## Pattern added

```python
from axiom.core.autonomous_gate import evaluate_autonomous_readiness

decision = evaluate_autonomous_readiness()

if not decision.allowed and not args.manual_test_override:
    reasons = ", ".join(decision.blocking_reasons) or "unknown"
    ...
    return 1
```

`start_task.py` uses `--manual-test-override`.

`dispatch_next_task.py` uses `--manual-test-override`.

---

# 6. Bounded Scheduler Loop Skeleton

## Files added

```text
axiom/core/scheduler_loop.py
tools/run_scheduler_loop.py
tests/test_scheduler_loop.py
```

## Purpose

Add a bounded foreground-only scheduler loop wrapper around `Scheduler.run_once()`.

This does not create a background service or autonomous runtime.

## Behavior

```text
- foreground only
- bounded by max_ticks
- stops on blocked / idle / running / error
- blocks by default when autonomous readiness is unavailable
- allows explicit manual/test override only with --allow-when-autonomous-blocked
```

## Core implementation

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from axiom.core.scheduler import Scheduler


TERMINAL_TICK_STATUSES = {
    "blocked",
    "idle",
    "running",
    "error",
}


@dataclass(frozen=True)
class SchedulerLoopResult:
    session_id: int
    profile_label: str
    ticks_requested: int
    ticks_run: int
    stopped_reason: str
    final_tick_status: str | None
    tick_results: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "profile_label": self.profile_label,
            "ticks_requested": self.ticks_requested,
            "ticks_run": self.ticks_run,
            "stopped_reason": self.stopped_reason,
            "final_tick_status": self.final_tick_status,
            "tick_results": self.tick_results,
        }


def run_scheduler_loop(
    session_id: int,
    profile_label: str = "default",
    max_ticks: int = 1,
    allow_when_autonomous_blocked: bool = False,
) -> SchedulerLoopResult:
    if max_ticks < 1:
        raise ValueError("max_ticks must be >= 1")

    scheduler = Scheduler()
    tick_results: list[dict[str, Any]] = []
    final_tick_status: str | None = None
    stopped_reason = "max_ticks_reached"

    for _ in range(max_ticks):
        result = scheduler.run_once(
            session_id=session_id,
            profile_label=profile_label,
            allow_when_autonomous_blocked=allow_when_autonomous_blocked,
        )

        payload = result.to_dict()
        tick_results.append(payload)

        final_tick_status = payload.get("tick_status") or payload.get("status")

        if final_tick_status in TERMINAL_TICK_STATUSES:
            stopped_reason = final_tick_status
            break

    return SchedulerLoopResult(
        session_id=session_id,
        profile_label=profile_label,
        ticks_requested=max_ticks,
        ticks_run=len(tick_results),
        stopped_reason=stopped_reason,
        final_tick_status=final_tick_status,
        tick_results=tick_results,
    )
```

## CLI

```powershell
python tools\run_scheduler_loop.py <SESSION_ID> --max-ticks 3
python tools\run_scheduler_loop.py <SESSION_ID> --max-ticks 3 --allow-when-autonomous-blocked
```

---

# 7. No-op Task Executor

## Files added

```text
axiom/core/noop_task_executor.py
tools/execute_noop_task.py
tests/test_noop_task_executor.py
```

## Purpose

Manually validate controlled lifecycle execution without tools, models, network, sandbox, agents, or Telegram.

## Direct path

```text
pending → running → completed
```

## Scheduler-dispatched path

```text
running → completed
```

## Main functions

```python
execute_noop_task(task_id: int) -> NoopTaskExecutionResult
complete_running_noop_task(task_id: int) -> NoopTaskExecutionResult
```

## Direct executor

`execute_noop_task()` requires the task to be:

```text
status = pending
manifest_id is not null
```

It starts the task via lifecycle start logic and completes it with deterministic no-op result data.

## Running-task completer

`complete_running_noop_task()` requires the task to be:

```text
status = running
manifest_id is not null
```

It completes the task only, because scheduler dispatch already performed the start transition.

## Deterministic no-op result JSON

```json
{
  "executor": "noop_task_executor",
  "executed": true,
  "side_effects": "none",
  "tools_used": [],
  "model_calls": [],
  "network_calls": [],
  "sandbox_calls": []
}
```

## CLI

```powershell
python tools\execute_noop_task.py <TASK_ID> --manual-test-override
```

The CLI blocks without `--manual-test-override` when autonomous readiness is unavailable.

---

# 8. Task Execution Audit

## Files added

```text
axiom/core/task_execution_audit.py
tools/audit_task_execution.py
tests/test_task_execution_audit.py
```

## Purpose

Read-only audit of no-op execution records.

## Checks

```text
- completed no-op tasks have result_text
- completed no-op tasks have valid result_json
- executor == noop_task_executor
- side_effects == none
- tools_used == []
- model_calls == []
- network_calls == []
- sandbox_calls == []
- running no-op tasks are flagged
- malformed result_json is flagged
```

## Scope

Default:

```text
latest_session
```

Optional:

```powershell
python tools\audit_task_execution.py --all-sessions
```

## CLI output

```powershell
python tools\audit_task_execution.py
```

Expected healthy shape:

```text
AXIOM task execution audit
==========================
passed: True
scope: latest_session
session_id: <SESSION_ID>
checked_task_count: <N>

violations:
- none
```

---

# 9. Task Execution Audit Integration into Reports

## Files changed

```text
tools/verify_foundation.py
tools/snapshot_project_state.py
tools/generate_handoff.py
tests/test_verify_foundation.py
tests/test_snapshot_project_state.py
tests/test_generate_handoff.py
```

## Verification integration

`verify_foundation.py` now includes:

```text
task_execution_audit:
checked: True
passed: True
scope: latest_session
session_id: <SESSION_ID>
checked_task_count: <N>
violation_count: 0
```

Execution audit failure now fails foundation verification.

## Core helper added

```python
from axiom.core.task_execution_audit import audit_task_execution


def _task_execution_audit_payload() -> dict[str, Any]:
    result = audit_task_execution(all_sessions=False)
    payload = result.to_dict()

    return {
        "checked": True,
        "passed": result.passed,
        "scope": result.scope,
        "session_id": result.session_id,
        "checked_task_count": result.checked_task_count,
        "violation_count": len(result.violations),
        "audit": payload,
    }
```

Foundation pass condition changed to include task execution audit:

```python
foundation_passed = bootstrap_result.passed and task_execution_audit["passed"]
```

## Snapshot integration

```python
"task_execution_audit": foundation.get("task_execution_audit"),
"foundation_verification": foundation,
```

## Handoff section added

```markdown
## Task Execution Audit

- Checked: `True`
- Passed: `True`
- Scope: `latest_session`
- Session ID: `<SESSION_ID>`
- Checked task count: `<N>`
- Violation count: `0`
```

---

# 10. Manual Scheduler-Dispatched No-op Execution Cycle

## Files added

```text
axiom/core/manual_noop_cycle.py
tools/run_manual_noop_cycle.py
tests/test_manual_noop_cycle.py
```

## Purpose

Manual/test-only bridge from scheduler dispatch to no-op completion.

## Cycle

```text
pending manifest-bound task
→ Scheduler.run_once()
→ task becomes running
→ complete_running_noop_task()
→ task becomes completed
→ audit_task_execution()
```

## Critical rule

This remains manual/test-only. It is not automatic scheduler-to-executor integration.

## CLI

```powershell
python tools\run_manual_noop_cycle.py <SESSION_ID> --allow-when-autonomous-blocked
```

Without `--allow-when-autonomous-blocked`, it blocks.

## Core behavior

```python
def run_manual_noop_cycle(
    session_id: int,
    profile_label: str = "default",
    allow_when_autonomous_blocked: bool = False,
) -> ManualNoopCycleResult:
    if not allow_when_autonomous_blocked:
        raise ManualNoopCycleError(
            "Manual no-op cycle requires explicit allow_when_autonomous_blocked=True "
            "while AXIOM remains fail-closed non-autonomous."
        )

    tick = Scheduler().run_once(
        session_id=session_id,
        profile_label=profile_label,
        allow_when_autonomous_blocked=allow_when_autonomous_blocked,
    )

    ...
    execution = complete_running_noop_task(task_id)
    audit = audit_task_execution(all_sessions=False).to_dict()
```

---

# 11. Operator Command Index Update

## Files changed

```text
tools/operator_command_index.py
tests/test_operator_command_index.py
```

## Added tools

```text
tools/run_scheduler_loop.py
tools/execute_noop_task.py
tools/audit_task_execution.py
tools/run_manual_noop_cycle.py
```

## Purpose

Ensure the command index documents the current implementation surface.

## Required safety descriptions

```text
run_scheduler_loop.py
- bounded foreground scheduler loop
- blocks by default
- manual/test override via --allow-when-autonomous-blocked

execute_noop_task.py
- deterministic no-op executor
- direct execution CLI requires --manual-test-override

audit_task_execution.py
- read-only execution audit
- no mutation

run_manual_noop_cycle.py
- manual scheduler-dispatched no-op cycle
- requires --allow-when-autonomous-blocked
```

---

# 12. Log Folder Cleanup Script Provided

## Context

The `logs` directory had hundreds of timestamped outputs from repeated report generation.

## Recommendation

Archive older generated logs, do not delete them.

## Manual PowerShell script provided

```powershell
Set-Location C:\axiom

$archiveDir = Join-Path (Get-Location) "logs\archive"
New-Item -ItemType Directory -Force $archiveDir | Out-Null

$logFiles = Get-ChildItem .\logs -File

if (-not $logFiles -or $logFiles.Count -eq 0) {
    Write-Host "No log files found in .\logs"
    exit 0
}

$newestBundle = Get-ChildItem .\logs -File -Filter "handoff_bundle_manifest_*.json" |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

$keepNames = New-Object System.Collections.Generic.HashSet[string]

if ($newestBundle) {
    $timestamp = $newestBundle.Name `
        -replace "^handoff_bundle_manifest_", "" `
        -replace "\.json$", ""

    Write-Host "Newest bundle timestamp detected: $timestamp"

    $bundlePatterns = @(
        "project_state_snapshot_$timestamp.json",
        "operator_command_index_$timestamp.json",
        "operator_command_index_$timestamp.md",
        "axiom_handoff_$timestamp.md",
        "handoff_bundle_manifest_$timestamp.json"
    )

    foreach ($pattern in $bundlePatterns) {
        $match = Get-ChildItem .\logs -File -Filter $pattern -ErrorAction SilentlyContinue
        foreach ($file in $match) {
            [void]$keepNames.Add($file.Name)
        }
    }
}
else {
    Write-Host "No handoff bundle manifest found. Keeping newest 25 files only."
}

$newestSafetyFiles = $logFiles |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 25

foreach ($file in $newestSafetyFiles) {
    [void]$keepNames.Add($file.Name)
}

$moved = 0
$kept = 0

foreach ($file in $logFiles) {
    if ($keepNames.Contains($file.Name)) {
        $kept++
        continue
    }

    $destination = Join-Path $archiveDir $file.Name

    if (Test-Path $destination) {
        $base = [System.IO.Path]::GetFileNameWithoutExtension($file.Name)
        $ext = [System.IO.Path]::GetExtension($file.Name)
        $uniqueName = "{0}_{1}{2}" -f $base, (Get-Date -Format "yyyyMMddHHmmss"), $ext
        $destination = Join-Path $archiveDir $uniqueName
    }

    Move-Item -Path $file.FullName -Destination $destination
    $moved++
}

Write-Host ""
Write-Host "AXIOM log archive complete"
Write-Host "=========================="
Write-Host "Kept in logs: $kept"
Write-Host "Moved to archive: $moved"
Write-Host "Archive folder: $archiveDir"

Write-Host ""
Write-Host "Current files kept in logs:"
Get-ChildItem .\logs -File |
    Sort-Object LastWriteTime -Descending |
    Select-Object Name, LastWriteTime |
    Format-Table -AutoSize
```

---

# Files Added in This Chat

```text
axiom/core/scheduler_loop.py
tools/run_scheduler_loop.py
tests/test_scheduler_loop.py

axiom/core/noop_task_executor.py
tools/execute_noop_task.py
tests/test_noop_task_executor.py

axiom/core/task_execution_audit.py
tools/audit_task_execution.py
tests/test_task_execution_audit.py

axiom/core/manual_noop_cycle.py
tools/run_manual_noop_cycle.py
tests/test_manual_noop_cycle.py

tests/test_test_db_isolation.py
```

---

# Files Modified in This Chat

```text
tests/conftest.py

axiom/core/scheduler.py
tools/repair_session_state.py
tests/test_repair_session_state.py
tests/test_scheduler_foundation.py

tools/register_model_fingerprint.py
tests/test_register_model_fingerprint.py

tools/snapshot_project_state.py
tools/generate_handoff.py
tests/test_snapshot_project_state.py
tests/test_generate_handoff.py

tools/start_task.py
tools/dispatch_next_task.py
tests/test_task_starter.py
tests/test_scheduler_dispatcher.py

tools/verify_foundation.py
tests/test_verify_foundation.py

tools/operator_command_index.py
tests/test_operator_command_index.py
```

---

# Current Implementation Boundary

The system is still in the current Phase 2 implementation area:

```text
StateMachine / Scheduler / TaskCommitter / SupervisorMonitor / Manual No-op Execution Harness
```

Completed in this chat:

```text
- DB isolation for tests
- idle heartbeat repair
- model-profile trust hardening
- snapshot/handoff profile scoping
- manual/test override gates for direct lifecycle CLIs
- bounded scheduler loop skeleton
- no-op task executor
- task execution audit
- execution audit integration into verification/snapshot/handoff
- manual scheduler-dispatched no-op cycle
- operator command index update
```

Not completed:

```text
- automatic scheduler-to-executor integration
- persistent scheduler service
- real task body execution
- real gateway execution
- classifier calibration workflow
- safe-pass enablement
- current trusted model profile activation
- autonomous operation
- Telegram/operator control plane
- agent layer
```

---

# Recommended Next Task

Recommended next task in a new chat:

```text
Execution readiness check
```

Purpose:

Before any scheduler/executor integration, add a read-only readiness check that reports:

```text
- lifecycle audit passed
- execution audit passed
- supervisor health healthy
- no running tasks
- pending manifest-bound task count
- autonomous readiness remains blocked unless explicitly expected
```

Possible files:

```text
axiom/core/execution_readiness.py
tools/execution_readiness_check.py
tests/test_execution_readiness.py
```

This should remain read-only.

Do not implement automatic scheduler-to-executor integration yet.

---

# Hard Stop Warnings

Do not proceed to:

```text
- autonomous operation
- safe-pass enablement
- model profile promotion
- real model calls
- cloud calls
- network gateway fetches
- sandbox execution
- Telegram/operator control plane
- agent layer
- automatic scheduler-to-executor integration
```

without explicit approval and verified prerequisites.
