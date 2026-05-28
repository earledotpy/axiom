# Phase 9 Planning Brief: Automatic Scheduler→Executor Integration

**From**: Claude Code (Governance Auditor)
**To**: Antigravity (Chief Architect)
**Date**: 2026-05-28
**ADR-0006 Step**: 1 — Antigravity produces the written task plan

---

## Operator Authorization

Jeremy has explicitly authorized Phase 9: automatic scheduler→executor integration for no-op tasks. This is the only expansion of runtime authority authorized for this slice.

---

## Current Code Shape

`axiom/core/manual_noop_cycle.py::run_manual_noop_cycle()` already performs the full cycle — scheduler tick → dispatch → `complete_running_noop_task()` → execution audit. It is gated by a required `allow_when_autonomous_blocked=True` argument and classified as manual/test-only.

`axiom/core/scheduler_tick.py::run_scheduler_tick()` dispatches a task to `running` but stops there — it does not call the executor.

`axiom/core/scheduler_loop.py::run_scheduler_loop()` runs bounded ticks but also stops at dispatch with no executor call.

`axiom/core/noop_task_executor.py::complete_running_noop_task(task_id)` completes an already-running no-op task deterministically. It does not select its own task; it requires a `task_id` supplied by the caller.

---

## What "Automatic" Means Here

Remove the requirement for a human to separately call the executor after the scheduler dispatches. The scheduler loop should, after successfully transitioning a no-op task to `running`, automatically call `complete_running_noop_task()` and validate the result — without the `allow_when_autonomous_blocked` manual override and without operator intervention between dispatch and completion.

This is still **non-autonomous**: the loop is only triggered by explicit operator invocation. No background threads, no persistent service, no self-scheduling.

---

## Invariants That Must Not Change

- One running task at a time — the executor must only operate on the task the scheduler just dispatched; it must never select its own pending task
- `tasks.manifest_id` must be non-null before transition to `running` (already enforced by `TaskCommitter`)
- Heartbeat ordering preserved around lifecycle transitions
- No model calls, network calls, sandbox execution, gateway calls, or Telegram/operator control introduced
- `fail_closed_non_autonomous` operational mode must remain intact
- `allow_when_autonomous_blocked=True` must not appear in the automatic path
- `task_execution_audit` must pass after every cycle
- `verify_foundation` must continue to report `foundation_passed: True`, `fail_closed_coherent: True`

---

## Exact Implementation Scope

Antigravity's plan must name changes to exactly these locations:

| File | Required change |
|---|---|
| `axiom/core/scheduler_loop.py` | After a successful dispatch, call `complete_running_noop_task(task_id)` and include the execution result in the loop result dataclass |
| `tools/run_scheduler_loop.py` | Update CLI output to surface the execution result |
| `tests/test_scheduler_loop.py` (new or existing) | Prove: executor is called after dispatch; no gateway calls occur; execution audit passes; one-running invariant holds throughout |

`axiom/core/manual_noop_cycle.py` must remain untouched — it stays as the explicit test-override path.

If Antigravity judges the executor call belongs in `scheduler_tick.py` rather than `scheduler_loop.py`, that is an acceptable architectural call — but the plan must name the exact function and explain the reasoning.

---

## Non-Goals for This Slice

- No autonomous operation
- No persistent scheduler service or background thread
- No real model calls
- No gateway activation (network, sandbox, memory, Telegram)
- No agent layer
- Task type remains `manual_noop` — this slice does not authorize general task execution
- No changes to `manual_noop_cycle.py`

---

## Verification Bar

After Codex implements and before Claude Code reviews:

```powershell
python tools/verify_foundation.py        # foundation_passed: True, fail_closed_coherent: True
python tools/audit_task_execution.py     # passed after a full loop run
pytest tests -v                          # all tests pass
```

---

## Plan Format Required

Per ADR-0006 and `GEMINI.governance.md`, the plan must:

- Name every file to be created or modified
- Name the exact function entrypoint for the executor call
- Describe the exact no-op-only executor binding
- Describe the exact test proving no gateway calls occur
- Include the audit verification commands
- Include a rollback plan
