# AXIOM Implementation Source — Chat Session Addendum

Generated: 2026-05-20  
Project root: `C:\axiom`  
Canonical baseline: `AXIOM_Implementation_v1.13.md`  
Scope: implementation work completed in this chat after the v1.13 foundation was already in progress.

This file records what was implemented, repaired, verified, and left intentionally deferred during this chat. It is not a replacement for `AXIOM_Implementation_v1.13.md`; it is a source/handoff addendum for the live repository state produced during this session.

---

## 1. Final verified operating state

AXIOM is currently in:

```text
operational_mode = fail_closed_non_autonomous
foundation_passed = True
autonomous_allowed = False
fail_closed_coherent = True
```

Expected `tools\verify_foundation.py` shape at the end of this chat:

```text
AXIOM foundation verification
============================
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

blocking_reasons:
- no_current_trusted_model_profile
- safe_pass_disabled
- autonomous_operation_disabled
```

This is the correct state. It means the foundation is healthy, but autonomous operation is intentionally unavailable.

---

## 2. Real local model profile state

The real `qwen3:4b` profile was registered as a candidate/non-current profile:

```text
model_name = qwen3:4b
ollama_host = http://localhost:11434
quantization = Q4_K_M
parameter_size = 4.0B
model_family = qwen3
model_format = gguf
thinking_mode = unknown
thinking_mode_rule_version = gateway_required_v1
calibration_run_id = pending_calibration
is_current = 0
registration_status = candidate
```

Important implementation adaptation:

The v1.13 artifact required rejection when `thinking_mode != disabled`, but the live host could not persist `PARAMETER think false` at the Ollama profile level. The implementation therefore records `thinking_mode='unknown'` only as:

```text
is_current = 0
registration_status = candidate
thinking_mode_rule_version = gateway_required_v1
```

Runtime enforcement remains in `ModelGateway`, which rejects caller `think=True` and injects `think=False`.

Do not manually mark this profile current.

---

## 3. Major files implemented or materially changed

### 3.1 Model fingerprint registration

File:

```text
tools/register_model_fingerprint.py
```

Final behavior:

- Queries Ollama model profile.
- Records profile fingerprints.
- Allows `thinking_mode='unknown'` only as `candidate/non-current`.
- Uses `gateway_required_v1` when runtime `think=False` enforcement is required.
- Is idempotent for duplicate `selected_profile_sha256`.
- Does not demote a current profile when inserting unknown/candidate rows.
- Rejects unreachable Ollama, missing quantization, and invalid registration status.

Validation completed:

```text
tests/test_register_model_fingerprint.py passed twice
full regression passed afterward
```

---

### 3.2 Operator/foundation observability tools

Implemented:

```text
axiom/app/status_report.py
tools/status_check.py
tools/repair_session_state.py
tools/autonomous_readiness_check.py
tools/verify_foundation.py
tools/snapshot_project_state.py
tools/generate_handoff.py
tools/operator_command_index.py
tools/generate_handoff_bundle.py
tools/test_inventory.py
```

Purpose:

- Make fail-closed state operator-visible.
- Repair/latest session safe-pass flags into a coherent fail-closed state.
- Expose autonomous readiness as a reusable gate.
- Create JSON snapshots and Markdown handoffs.
- Generate a bundle manifest with snapshot, handoff, and command index artifacts.
- Avoid stale manual test-count assumptions by collecting pytest inventory.

Key behavior:

```text
verify_foundation.py exits 0 when foundation is healthy, even if autonomous mode is blocked.
autonomous_readiness_check.py exits 2 when autonomous mode is blocked.
bootstrap_check.py exits 0 when foundation passes, even if operational_mode is fail_closed_non_autonomous.
```

---

### 3.3 Bootstrap validation integration

Files:

```text
axiom/app/bootstrap_validation.py
tools/bootstrap_check.py
```

Implemented:

- `BootstrapValidationResult.to_dict()`
- `autonomous_readiness`
- `operational_mode`
- CLI text/JSON exposure of operational mode and readiness.

Required distinction preserved:

```text
foundation failed != autonomous blocked
```

Healthy foundation with autonomous unavailable reports:

```text
passed = True
operational_mode = fail_closed_non_autonomous
```

---

## 4. Task lifecycle implementation

This chat substantially implemented the `StateMachine / Scheduler / TaskCommitter / SupervisorMonitor` block from v1.13.

### 4.1 Lifecycle audit

Files:

```text
axiom/core/task_lifecycle_audit.py
tools/audit_task_lifecycle.py
```

Audit checks:

```text
multiple_running_tasks
running_task_missing_manifest
heartbeat_active_task_coherence
```

Important correction made:

The audit checks only the latest heartbeat per session for active-task coherence. Historical heartbeats are an event trail and may legitimately point to tasks that later completed/failed/cancelled.

CLI behavior:

```powershell
python tools\audit_task_lifecycle.py
```

Defaults to latest session.

Explicit historical audit:

```powershell
python tools\audit_task_lifecycle.py --all-sessions
```

Historical audit may reveal deliberate test-created invalid rows. That does not mean the current operational session is bad.

Expected current/latest result:

```text
passed: True
scope: latest_session
violations: none
```

---

### 4.2 Running transition guard

File:

```text
axiom/core/task_lifecycle_guard.py
```

Implemented:

```text
evaluate_task_running_transition(task_id)
require_task_running_transition_allowed(task_id)
transition_task_to_running(task_id)
```

Enforces:

```text
task exists
status == pending
manifest_id is non-null/non-empty
no other task in the same session is running
```

---

### 4.3 Task start

Files:

```text
axiom/core/task_starter.py
tools/start_task.py
```

Behavior:

```text
pending -> running
started_at set
scheduler heartbeat written
active_task_id set
active_chain_id set
scheduler_state = running
last_action = task_started
last_blocking_operation_type = task_execution
```

Validated manually and by tests.

---

### 4.4 Task completion

Files:

```text
axiom/core/task_completer.py
tools/complete_task.py
```

Behavior:

```text
running -> completed
completed_at set
optional result_text/result_json stored
scheduler heartbeat written
active_task_id cleared
active_chain_id cleared
scheduler_state = ready
last_action = task_completed
```

PowerShell note for JSON arguments:

```powershell
python tools\complete_task.py 2030 --result-text "manual completion verified" --result-json '{"ok": true}'
```

or omit JSON:

```powershell
python tools\complete_task.py 2030 --result-text "manual completion verified"
```

---

### 4.5 Task failure

Files:

```text
axiom/core/task_failer.py
tools/fail_task.py
```

Behavior:

```text
running -> failed
completed_at set
error_info JSON stored
scheduler heartbeat written
active_task_id cleared
scheduler_state = ready
last_action = task_failed
```

---

### 4.6 Task cancellation

Files:

```text
axiom/core/task_canceller.py
tools/cancel_task.py
```

Behavior:

```text
pending -> cancelled
running -> cancelled
```

For pending cancellation:

```text
status = cancelled
cancel_requested = 1
completed_at set
error_info records cancellation
no heartbeat required
```

For running cancellation:

```text
status = cancelled
cancel_requested = 1
completed_at set
error_info records cancellation
heartbeat clears active_task_id
last_action = task_cancelled
```

Validated manually:

```text
created task_id=2389
start heartbeat_id=1231
cancel heartbeat_id=1232
status=cancelled
latest lifecycle audit passed
```

---

### 4.7 Task lifecycle service facade

File:

```text
axiom/core/task_lifecycle_service.py
```

Provides stable integration surface:

```python
TaskLifecycleService.start(task_id)
TaskLifecycleService.complete(task_id, result_text=None, result_json=None)
TaskLifecycleService.fail(task_id, error_type="execution_error", message="Task execution failed.", details=None)
TaskLifecycleService.cancel(task_id, reason="operator_cancelled", details=None)
TaskLifecycleService.audit(session_id=None, latest_session=False)
```

Default accessor:

```python
get_task_lifecycle_service()
```

Purpose:

Scheduler, StateMachine, and TaskCommitter should depend on this service instead of importing individual primitives.

---

## 5. TaskCommitter wiring

File:

```text
axiom/core/task_committer.py
```

Rewired so lifecycle-sensitive transitions use `TaskLifecycleService`.

Supported targets:

```text
running
completed
failed
cancelled
```

Compatibility preserved:

```text
CommitResult.heartbeat_before_id
CommitResult.heartbeat_after_id
legacy missing-manifest error phrase containing "manifest_id is required"
```

Why compatibility was required:

Existing `test_task_committer.py` expected both heartbeat IDs and specific prose in the missing-manifest error. The final implementation preserves those while delegating real lifecycle state changes to the lifecycle service.

---

## 6. Scheduler implementation

### 6.1 Scheduler dispatcher

Files:

```text
axiom/core/scheduler_dispatcher.py
tools/dispatch_next_task.py
```

Behavior:

- Selects one eligible pending task for a session.
- Requires:
  - `status='pending'`
  - `cancel_requested=0`
  - `manifest_id IS NOT NULL`
  - `trim(manifest_id) != ''`
- Orders by:
  - priority descending
  - created_at ascending
  - task_id ascending
- Blocks if another task is already running.
- Starts via lifecycle service.

Manual pattern:

```powershell
python tools\dispatch_next_task.py 3475
python tools\audit_task_lifecycle.py --session-id 3475
```

Do not type `<SESSION_ID>` literally in PowerShell.

---

### 6.2 Scheduler tick

Files:

```text
axiom/core/scheduler_tick.py
tools/scheduler_tick.py
```

One conservative scheduler tick does:

```text
repair session state
evaluate autonomous readiness
audit task lifecycle
block if lifecycle audit fails
block if autonomous is not ready, unless manual/test override is passed
dispatch one eligible task only when allowed
```

Default current behavior:

```text
tick_status = blocked
reason = autonomous_not_ready
```

Manual/test override:

```powershell
python tools\scheduler_tick.py <actual_session_id> --allow-when-autonomous-blocked
```

This override is only for local/test lifecycle verification. It is not autonomous operation.

---

### 6.3 Scheduler.run_once()

File:

```text
axiom/core/scheduler.py
```

Added:

```python
class Scheduler:
    def run_once(
        self,
        session_id: int,
        profile_label: str = "default",
        allow_when_autonomous_blocked: bool = False,
    ):
        from axiom.core.scheduler_tick import run_scheduler_tick

        return run_scheduler_tick(
            session_id=session_id,
            profile_label=profile_label,
            allow_when_autonomous_blocked=allow_when_autonomous_blocked,
        )
```

This is intentionally single-step only.

No scheduler loop, background thread, or autonomous loop exists yet.

---

## 7. SupervisorMonitor implementation

File:

```text
axiom/core/supervisor_monitor.py
```

Added active-task heartbeat coherence.

Supervisor now checks:

```text
scheduler heartbeat fresh/stale/missing
one-running-task invariant
latest heartbeat active_task_id exists
active_task_id points to a task
active task status is running if active_task_id is present
```

Health fields include:

```text
healthy
session_id
scheduler_stale
running_task_invariant_valid
running_count
reason
latest_heartbeat
active_task_present
active_task_status
details
```

Healthy idle state:

```text
reason = supervisor_health_ok
running_count = 0
active_task_present = False
active_task_status = None
```

Healthy active-task state:

```text
reason = supervisor_health_ok_active_task_running
running_count = 1
active_task_present = True
active_task_status = running
```

Unhealthy states include:

```text
scheduler_heartbeat_stale_or_missing
multiple_running_tasks_detected
heartbeat_active_task_missing
heartbeat_active_task_not_running
```

CLI added:

```text
tools/supervisor_health_check.py
```

Manual expected active-task output:

```text
healthy: True
scheduler_stale: False
running_task_invariant_valid: True
running_count: 1
active_task_present: True
active_task_status: running
reason: supervisor_health_ok_active_task_running
```

---

## 8. Supervisor health integrated into verification and handoff artifacts

Files patched:

```text
tools/verify_foundation.py
tools/snapshot_project_state.py
tools/generate_handoff.py
tests/test_verify_foundation.py
tests/test_snapshot_project_state.py
tests/test_generate_handoff.py
```

`verify_foundation.py` is now versioned:

```text
verify_foundation.v2
```

Snapshot now includes top-level:

```text
supervisor_health
```

Handoff Markdown now includes:

```markdown
## Supervisor Health

- Checked: `True`
- Reason: `supervisor_health_ok`
- Healthy: `True`
- Scheduler stale: `False`
- Running count: `0`
- Active task present: `False`
- Active task status: `None`
```

This section is inserted between:

```text
## Blocking Reasons
```

and:

```text
## Latest Model Profile
```

---

## 9. Command index / handoff bundle

Operator command index was expanded and exportable.

Files:

```text
tools/operator_command_index.py
tools/generate_handoff_bundle.py
```

Handoff bundle includes:

```text
project_state_snapshot
operator_command_index_json
operator_command_index_markdown
handoff_markdown
bundle_manifest
```

Commands:

```powershell
python tools\operator_command_index.py
python tools\operator_command_index.py --json
python tools\operator_command_index.py --markdown
python tools\operator_command_index.py --write

python tools\generate_handoff_bundle.py
python tools\generate_handoff_bundle.py --json
```

---

## 10. Verification commands to run in new chat

Use AXIOM Terminal if available.

```powershell
Set-Location C:\axiom
.\venv\Scripts\Activate.ps1

python tools\verify_foundation.py
python tools\audit_task_lifecycle.py
python tools\supervisor_health_check.py <latest_session_id>
pytest tests -v
```

To get latest session id:

```powershell
@'
from axiom.persistence.db import get_connection

with get_connection() as conn:
    row = conn.execute(
        """
        SELECT session_id
        FROM sessions
        ORDER BY session_id DESC
        LIMIT 1
        """
    ).fetchone()

    print(row["session_id"] if row else "no session")
'@ | python
```

Generate fresh artifacts:

```powershell
python tools\snapshot_project_state.py
python tools\generate_handoff.py
python tools\generate_handoff_bundle.py
```

---

## 11. Things intentionally not implemented yet

Do not proceed to these without explicit approval and prerequisite verification:

```text
autonomous operation
safe-pass enablement
model profile promotion to current
classifier calibration workflow
real model/cloud calls
real network fetches
sandbox process execution
Telegram/operator control plane
agent layer
automatic scheduler-to-executor integration
persistent scheduler loop
```

---

## 12. Recommended next implementation task

The safest next step is:

```text
Scheduler loop skeleton in disabled/manual mode only.
```

Constraints for that task:

```text
no background thread by default
no autonomous bypass
uses Scheduler.run_once()
bounded max_ticks
exits on blocked/idle/running according to explicit rules
manual/test override must be clearly named
does not execute task bodies
does not call model/network/sandbox
```

Alternative next task:

```text
Add no-op task execution harness using lifecycle service:
start -> deterministic no-op result -> complete
```

But do this only after the scheduler loop skeleton is bounded and non-autonomous.

---

## 13. Current conceptual status against AXIOM v1.13

Canonical v1.13 says Phase 2 includes:

```text
StateMachine
Scheduler
SupervisorMonitor
TaskCommitter
ContextBuilder
TokenEstimator
one-running-task enforcement
manifest_id required before running
heartbeat write ordering
```

This chat completed or substantially advanced:

```text
StateMachine-adjacent lifecycle enforcement
Scheduler.run_once
Scheduler tick primitive
Scheduler dispatch primitive
SupervisorMonitor heartbeat coherence
TaskCommitter lifecycle-service wiring
one-running-task enforcement
manifest_id-before-running enforcement
heartbeat set/clear around task lifecycle transitions
```

Still not done from Phase 2:

```text
ContextBuilder
TokenEstimator
persistent scheduler loop
no-op task execution harness
task body execution integration
```

End of source addendum.
