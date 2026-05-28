# Phase 9 Handoff: Automatic Scheduler→Executor Integration Draft Plan

**From**: Antigravity (Chief Architect)  
**To**: Codex (Implementation Specialist)  
**Date**: 2026-05-28  
**ADR-0006 Step**: 1 — Antigravity produces the written task plan  

---

## 1. Goal and Scope

Implement automatic scheduler→executor integration for `manual_noop` tasks in the scheduler loop. When the loop dispatches a `manual_noop` task, it must automatically invoke the no-op task executor to run and complete the task in the same tick. This removes the need for subsequent manual invocation of the executor while preserving AXIOM's local-first, fail-closed, non-autonomous posture.

---

## 2. Affected Files

The implementation is strictly limited to the following files:
1. [axiom/core/scheduler_loop.py](file:///C:/axiom/axiom/core/scheduler_loop.py) — Call the no-op executor after task dispatch and record the execution result.
2. [tools/run_scheduler_loop.py](file:///C:/axiom/tools/run_scheduler_loop.py) — Update the CLI stdout format to surface the execution result.
3. [tests/test_scheduler_loop.py](file:///C:/axiom/tests/test_scheduler_loop.py) — Add unit tests validating automatic completion, sequential task safety, gateway isolation, and audit correctness.

---

## 3. Proposed Approach & Key Decisions

### Exact Function Entrypoint for Executor Call
The executor must be called via:
* `axiom.core.noop_task_executor.complete_running_noop_task(task_id: int)`

### Exact No-op-Only Executor Binding
In [axiom/core/scheduler_loop.py](file:///C:/axiom/axiom/core/scheduler_loop.py), inside `run_scheduler_loop()`, after `scheduler.run_once()` successfully dispatches a task (where `result.dispatched_task_id` is not `None`):
1. Import `complete_running_noop_task` and `_get_task` from `axiom.core.noop_task_executor`.
2. Retrieve the task details using `_get_task(result.dispatched_task_id)`.
3. Check the `task_type` value:
   * If `task["task_type"] == "manual_noop"`, invoke `complete_running_noop_task(result.dispatched_task_id)` and store the returned `NoopTaskExecutionResult.to_dict()` in `SchedulerLoopResult.execution_result`.
   * If the task is of any other type, raise a `NoopTaskExecutionError("Automatic execution only authorized for manual_noop tasks")`. This ensures strict non-autonomous boundaries for other task types.
4. Update `SchedulerLoopResult` and its `to_dict()` method to include:
   * `execution_result: dict[str, Any] | None = None`

### Gateway Isolation Verification in Tests
To prove that no gateway calls occur, the test suite in [tests/test_scheduler_loop.py](file:///C:/axiom/tests/test_scheduler_loop.py) will patch the following gateway classes using `unittest.mock.patch` and assert they are never instantiated or called during the scheduler loop execution:
* `axiom.gateways.model_gateway.ModelGateway`
* `axiom.gateways.network_gateway.NetworkGateway`
* `axiom.gateways.sandbox_gateway.SandboxGateway`
* `axiom.gateways.memory_gateway.MemoryGateway`
* `axiom.gateways.telegram_gateway.TelegramGateway`

---

## 4. Verification Steps

To verify the changes, the following local verification battery must pass.

### Execution Audit Verification Commands
Run the following verification sequence:
```powershell
# 1. Run the foundation verification to confirm the base state is intact and clean
python tools/verify_foundation.py

# 2. Run the full test suite to verify no regressions in other areas
pytest tests -v

# 3. Specifically run the scheduler loop tests, including our new validations
pytest tests/test_scheduler_loop.py -v

# 4. Verify task execution audit passes for the session
python tools/audit_task_execution.py
```

---

## 5. Rollback Plan

If the changes introduce regressions or fail review:
1. Revert modifications in `axiom/core/scheduler_loop.py`, `tools/run_scheduler_loop.py`, and `tests/test_scheduler_loop.py` to their clean git states:
   ```powershell
   git checkout HEAD -- axiom/core/scheduler_loop.py tools/run_scheduler_loop.py tests/test_scheduler_loop.py
   ```
2. Verify that the test suite passes under the original configuration:
   ```powershell
   pytest tests/test_scheduler_loop.py
   ```

---

## 6. Risks and Constraints

* **Fail-Closed State**: We must not bypass the `allow_when_autonomous_blocked` flag when initiating a scheduler tick. The scheduler tick itself decides whether to block; our automatic execution must only fire *after* a successful dispatch occurs.
* **One-Running Invariant**: We must guarantee that tasks are executed strictly sequentially. Since the loop runs synchronously and ticks are processed in order, a dispatched task will be run to completion before the next tick starts.
* **Protected Files**: No changes may be made to protected files, including `axiom/persistence/schema.sql`, `axiom/core/state_machine.py`, or `axiom/core/policy_engine.py`.
