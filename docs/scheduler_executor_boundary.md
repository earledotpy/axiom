# AXIOM Scheduler / Executor Boundary

## Current status

AXIOM currently supports a manual, test-only no-op execution cycle.

The current verified execution path is:

```text
pending manifest-bound task
-> Scheduler.run_once()
-> running task
-> complete_running_noop_task()
-> completed task
-> task_execution_audit verifies coherence
```

This path is intentionally manual and must not be connected automatically yet.

## Current safe state

The healthy fail-closed baseline is:

```text
foundation_passed: True
operational_mode: fail_closed_non_autonomous
autonomous_allowed: False
fail_closed_coherent: True
supervisor_health_ok
task_lifecycle_audit passed
task_execution_audit passed
running_count: 0
active_task_present: False
```

`autonomous_allowed: False` is not a failure.

`execution_readiness.ready: False` is also not a failure when the only reason is:

```text
no_pending_manifest_bound_task
```

That means the system is clean but no manifest-bound pending task is staged for a controlled manual execution test.

## Existing manual-only execution tools

The following tools are allowed only as explicit manual/test actions:

```text
tools/run_scheduler_loop.py
tools/scheduler_tick.py
tools/dispatch_next_task.py
tools/start_task.py
tools/execute_noop_task.py
tools/run_manual_noop_cycle.py
```

The following tools are read-only:

```text
tools/audit_task_lifecycle.py
tools/audit_task_execution.py
tools/supervisor_health_check.py
tools/execution_readiness_check.py
tools/verify_foundation.py
```

## Future integration preconditions

Automatic scheduler-to-executor integration must not be implemented until all of the following are true:

```text
foundation_passed: True
task_lifecycle_audit passed
task_execution_audit passed
supervisor_health_ok
execution_readiness.ready: True
running_task_count: 0
pending_manifest_bound_task_count >= 1
```

Additionally:

```text
tasks.manifest_id must be non-null before transition to running
one-running-task invariant must remain enforced
heartbeat ordering must be preserved around blocking operations
no model calls may be introduced
no network calls may be introduced
no sandbox process execution may be introduced
no Telegram/operator control plane may be introduced
no autonomous operation may be enabled
```

## Future allowed integration shape

The only future integration shape currently under consideration is:

```text
Scheduler.run_once()
-> dispatch exactly one pending manifest-bound no-op task to running
-> no-op executor completes that already-running no-op task
-> task_execution_audit validates result
-> supervisor_health_check validates idle clean state
```

The executor must operate only on a task already transitioned to `running` by scheduler logic.

The executor must not select its own pending task.

The executor must not bypass the scheduler.

The executor must not create child tasks.

The executor must not call gateways.

The executor must not perform filesystem, model, network, sandbox, memory, Telegram, or agent actions.

## Non-goals

This boundary does not authorize:

```text
autonomous operation
safe-pass enablement
model profile promotion
real model calls
real gateway execution
real network fetches
sandbox process execution
Telegram/operator control plane
agent layer
persistent scheduler service
automatic scheduler-to-executor integration
```

## Required next review before implementation

Before implementing automatic scheduler-to-executor integration, the operator must explicitly approve a bounded patch that names:

```text
exact files to edit
exact function entrypoint
exact task class and task_type allowed
exact no-op-only executor binding
exact test proving no gateway calls occur
exact audit verification commands
rollback plan
```
