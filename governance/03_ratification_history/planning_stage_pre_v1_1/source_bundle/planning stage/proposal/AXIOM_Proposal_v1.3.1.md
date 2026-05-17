AXIOM Proposal v1.3.1 — Chief Architect Patch

Resolution of v1.3 Coherence Return

0. Patch Status

Field	Value

Proposal version	v1.3.1
Type	Patch to v1.3
Scope	Resolves F1–F5 plus minor coherence notes
Architecture spine changed?	No
Recommended next step	Return to Claude for confirmation, then targeted DeepSeek re-check


Claude’s v1.3 evaluation found that the architecture was mostly sound but could not proceed because of one hard contradiction and four implementation-blocking ambiguities. This patch resolves those points directly. 


---

1. Resolution Matrix

Issue	Panel concern	v1.3.1 decision

F1	operator_control could directly mutate tasks.status	Remove direct status writes; operator writes request flags only; Scheduler mutates state
F2	Policy Engine referenced but absent from module map	Add explicit core/policy_engine.py
F3	approved_for_execution unclear as task state	Retire as status; implement as tasks.policy_approved boolean + policy decision record
F4	“plus one of” shared-state writes ambiguous	Replace with “any explicitly granted subset” of Phase 1 write candidates
F5	Deterministic chain has no orchestrator	Scheduler is the orchestrator of deterministic chain transitions



---

2. F1 — Scheduler-Only State Mutation Restored

Decision

operator_control tasks may not write tasks.status.

The Scheduler remains the only component that mutates task state.

Claude correctly identified that v1.3 contradicted itself by saying “Scheduler alone mutates task state” while granting operator_control permission to set tasks.status = cancelled. That violated the zero-trust and queue-sequencing model. 

Revised rule

Operator-control tasks write intent flags.
Scheduler observes intent flags.
Scheduler applies state transitions.

Revised operator_control.json

{
  "manifest_name": "operator_control",
  "task_class": "operator_control",
  "role_owner": "telegram_gateway",
  "priority": "interrupt",
  "allowed_tools": [],
  "allowed_read_scopes": [
    "session.current_status",
    "task.active_chain_summary",
    "provider.status_summary"
  ],
  "allowed_write_fields": [
    "tasks.cancel_requested",
    "sessions.pause_requested",
    "sessions.shutdown_requested",
    "task_events"
  ],
  "write_constraints": {
    "tasks.cancel_requested": {
      "allowed_values": [true],
      "scope": ["active_task", "unstarted_descendants"]
    },
    "sessions.pause_requested": {
      "allowed_values": [true, false]
    },
    "sessions.shutdown_requested": {
      "allowed_values": [true]
    }
  },
  "forbidden_writes": [
    "tasks.status",
    "tasks.input_payload",
    "tasks.output_payload",
    "tasks.acceptance_criteria",
    "tasks.manifest_id",
    "task_permissions",
    "memory_items",
    "memory_vectors",
    "plan_artifacts",
    "plan_checkpoints",
    "config_snapshots"
  ],
  "network_policy": {
    "allow_network": false
  },
  "sandbox_policy": {
    "allow_sandbox": false
  },
  "memory_policy": {
    "allow_memory_read": false,
    "allow_memory_write_candidate": false
  }
}

Cancellation flow

/cancel_current_chain
↓
operator_control task created with priority interrupt
↓
operator_control sets tasks.cancel_requested = true
↓
Scheduler observes cancel_requested at next tick or timeout boundary
↓
Scheduler sets active task status = cancelled
↓
Scheduler sets unstarted descendants status = cancelled
↓
Telegram Gateway reports cancellation summary

Corrected meaning of interrupt

interrupt = prioritized request handling at the next Scheduler tick

It does not mean mid-flight preemption. Phase 1 cancellation remains cooperative.


---

3. /resume Semantics Clarified

Decision

/resume sets:

sessions.pause_requested = false

No separate sessions.resume_requested flag is required.

Operator commands

Command	Write action	Scheduler behavior

/pause_after_current	sessions.pause_requested = true	Stops selecting new non-control tasks after current task ends
/resume	sessions.pause_requested = false	Scheduler resumes normal selection
/shutdown_after_current	sessions.shutdown_requested = true	Stops after current task and sends shutdown summary
/cancel_current_chain	tasks.cancel_requested = true	Scheduler cancels active chain at next tick/timeout



---

4. F2 — Policy Engine Added to Module Map

Decision

Add a real module:

core/policy_engine.py

This avoids ambiguity. The Policy Engine is not merely a logical label for permissions.py or state_machine.py.

Responsibilities

Component	Responsibility

policy_engine.py	Decides whether a task may run
permissions.py	Enforces manifest capability rules
state_machine.py	Defines legal task status transitions
scheduler.py	Calls Policy Engine, applies state transitions
role_executor.py	Invokes role modules only after Scheduler approval


Policy Engine checks

task_class validity
sanitization_status
quarantine_flag
classifier_validation_status
parent task state
acceptance criteria presence
manifest presence
manifest hash validity
permission check result
resource limits
provider budget
sandbox/network preconditions
cancel_requested flag
session pause/shutdown state

Module map update

core/
  scheduler.py
  state_machine.py
  policy_engine.py
  permissions.py
  context_builder.py
  manifest_binder.py
  task_committer.py
  role_executor.py
  watchdog.py
  cancellation.py
  resource_limits.py

Why this is worth one more module

The Policy Engine is load-bearing. It is the execution gate that prevents a task from becoming active. Folding it invisibly into two other modules would make Kimi’s implementation plan less precise.


---

5. F3 — approved_for_execution Reconciled

Decision

approved_for_execution is not a task status.

It is replaced by explicit approval fields:

tasks.policy_approved
tasks.policy_approved_at
tasks.policy_decision_id

Schema patch

ALTER TABLE tasks ADD COLUMN policy_approved INTEGER NOT NULL DEFAULT 0;
ALTER TABLE tasks ADD COLUMN policy_approved_at TEXT;
ALTER TABLE tasks ADD COLUMN policy_decision_id TEXT;

Add:

policy_decisions

table:

policy_decision_id
task_id
decision = approved | blocked | needs_human_input | quarantined
reason
checked_by = PolicyEngine
created_at

Corrected task promotion flow

task.status = created
↓
Scheduler selects eligible task candidate
↓
PolicyEngine evaluates task
↓
If approved:
    write policy_decisions row
    set tasks.policy_approved = 1
    set tasks.policy_approved_at
    set tasks.policy_decision_id
    set tasks.status = running
↓
RoleExecutor runs assigned role

Corrected status space

Allowed Phase 1 task statuses:

created
running
awaiting_verification
verified
completed
retry_pending
blocked
failed
needs_human_input
quarantined
cancelled

Planning-specific statuses remain valid only for planning tasks:

plan_artifact_created
plan_injection_scan_pending
plan_injection_scan_passed
plan_checkpoint_pending
plan_checkpoint_passed
child_tasks_committed
subtask_plan_created
subtask_checkpoint_pending
subtask_checkpoint_passed

Removed term

The phrase:

approved_for_execution

should no longer appear as a task lifecycle state.

Permitted replacement wording:

policy-approved for execution

meaning:

tasks.policy_approved = 1


---

6. F4 — Shared-State Write Scope Clarified

Decision

Replace “plus one of” with:

Tool Executor may write its own result/error fields,
plus any explicitly granted subset of the Phase 1 shared-state write candidates.

Phase 1 shared-state write candidates

Allowed candidate set:

memory.write_candidate
artifact.create_reference
security_event.append
tool_invocation.append

Rule

A Tool Executor manifest may include:

zero or more

of the allowed shared-state write candidates.

But it may include only candidates from the Phase 1 whitelist.

Examples

Valid network fetch manifest

{
  "allowed_write_fields": [
    "tasks.output_payload",
    "tasks.error_payload"
  ],
  "shared_state_writes": [
    "artifact.create_reference",
    "tool_invocation.append",
    "security_event.append"
  ]
}

Valid memory candidate manifest

{
  "allowed_write_fields": [
    "tasks.output_payload",
    "tasks.error_payload"
  ],
  "shared_state_writes": [
    "memory.write_candidate",
    "tool_invocation.append"
  ]
}

Invalid manifest

{
  "shared_state_writes": [
    "tasks.status",
    "task_permissions.update",
    "plan_artifacts.modify"
  ]
}

Enforcement ceiling

Even if a plan artifact requests broader write access, ManifestBinder must reject it.

This maintains the Core Value 3 boundary that an execution role cannot write task-structure fields it does not own. 


---

7. F5 — Deterministic Chain Orchestrator Named

Decision

The Scheduler is the orchestrator of deterministic chain transitions.

Do not add core/orchestrator.py in Phase 1.

Reason: adding a separate orchestrator would duplicate Scheduler responsibility and weaken the clear “Scheduler owns sequencing” rule.

Scheduler orchestration responsibility

The Scheduler advances artifacts and tasks through deterministic transitions by invoking deterministic components in order.

Integrated deterministic chain

Planner role produces proposed artifact
↓
Scheduler records artifact status = proposed
↓
Scheduler invokes PlanInjectionScanner
↓
PlanInjectionScanner writes scan verdict
↓
Scheduler checks injection_scan_status
↓
If passed: Scheduler creates verification task
↓
RoleExecutor invokes ResultVerifier in checkpoint mode
↓
ResultVerifier writes verification_results row
↓
Scheduler maps verifier verdict through StateMachine
↓
If checkpoint passed: Scheduler invokes TaskCommitter
↓
TaskCommitter validates artifact schema
↓
TaskCommitter invokes ManifestBinder
↓
ManifestBinder binds task manifests
↓
TaskCommitter inserts child tasks at status = created
↓
Scheduler marks parent planning task = child_tasks_committed

Ownership table

Step	Owner

Detect proposed artifact ready	Scheduler
Run injection scan	Scheduler calls PlanInjectionScanner
Create checkpoint verification task	Scheduler
Invoke Result Verifier role	RoleExecutor, called by Scheduler
Interpret verifier result	Scheduler + StateMachine
Commit verified child tasks	Scheduler calls TaskCommitter
Bind manifests	TaskCommitter calls ManifestBinder
Apply task status transitions	Scheduler only


RoleExecutor boundary

role_executor.py remains the only component that invokes role modules:

goal_planner.py
task_planner.py
tool_executor.py
result_verifier.py

But deterministic components are not role modules:

PlanInjectionScanner
TaskCommitter
ManifestBinder
PolicyEngine
PermissionEngine

The Scheduler may call deterministic components directly.


---

8. Runtime “Dispatch Guard” Reframed

Correction

v1.3 overstated the runtime guard.

Correct framing:

The static import-graph test is the enforcement.
The role_executor structure makes the enforcement meaningful.

Python cannot absolutely prevent a deliberately misbehaving module from importing a sibling at runtime. Therefore the enforceable Phase 1 rule is:

CI/test failure if agents/*.py imports another agents/*.py module.

Required test

tests/test_no_direct_role_imports.py

Pass condition:

No file under agents/ imports another file under agents/.

This is still sufficient for Phase 1 because the operator executes tests before accepting the build, and AXIOM is not yet defending against malicious source-code edits by its own operator.


---

9. Consolidated End-to-End Trust Chain

Full Phase 1 plan-to-execution chain

Human Telegram goal
↓
Command Parser
↓
Ingress Sanitizer
↓
Task inserted: task_class = goal_planning, status = created
↓
Scheduler calls PolicyEngine
↓
PolicyEngine approves task by writing policy_decision
↓
Scheduler sets status = running
↓
RoleExecutor invokes GoalPlanner
↓
GoalPlanner writes proposed plan artifact
↓
Scheduler invokes PlanInjectionScanner
↓
PlanInjectionScanner writes scan verdict
↓
Scheduler creates checkpoint verification task
↓
RoleExecutor invokes ResultVerifier in plan_checkpoint mode
↓
ResultVerifier writes verification_results row
↓
Scheduler validates checkpoint result through StateMachine
↓
Scheduler calls TaskCommitter
↓
TaskCommitter validates plan schema
↓
TaskCommitter calls ManifestBinder
↓
ManifestBinder binds task-specific manifests
↓
TaskCommitter inserts child tasks with status = created
↓
Scheduler continues sequential task loop

Why this resolves the ambiguity

This single chain identifies:

Question	Answer

Who drives the chain?	Scheduler
Who invokes role modules?	RoleExecutor
Who invokes deterministic components?	Scheduler
Who creates child tasks?	TaskCommitter
Who creates manifests?	ManifestBinder
Who mutates task status?	Scheduler
Who writes verifier evidence?	ResultVerifier
Who applies verifier evidence?	Scheduler



---

10. Revised Acceptance Tests

Add or update these tests.

F1 tests

tests/test_operator_control_manifest.py
tests/test_scheduler_only_state_mutation.py

Required assertions:

operator_control manifest does not include tasks.status
operator_control can set tasks.cancel_requested = true
Scheduler, not operator_control, transitions cancelled tasks
operator_control cannot write task payloads, manifests, memory, or plan artifacts

F2 tests

tests/test_policy_engine_exists.py
tests/test_policy_engine_gate.py

Required assertions:

core/policy_engine.py exists
PolicyEngine blocks task without manifest
PolicyEngine blocks quarantined task
PolicyEngine blocks invalid task_class
PolicyEngine writes policy_decisions row

F3 tests

tests/test_policy_approved_flag.py

Required assertions:

approved_for_execution is not a valid task.status
PolicyEngine approval sets policy_approved = 1
Scheduler promotes only policy-approved task
blocked decision does not promote task

F4 tests

tests/test_shared_state_write_subset.py

Required assertions:

manifest can grant any subset of allowed shared-state candidates
manifest cannot grant task-structure writes
manifest cannot grant task_permissions writes
ManifestBinder rejects unlisted shared-state write candidates

F5 tests

tests/test_scheduler_deterministic_chain.py

Required assertions:

Scheduler calls PlanInjectionScanner before checkpoint task
Scheduler does not create checkpoint task if scan fails
Scheduler calls TaskCommitter only after checkpoint pass
TaskCommitter calls ManifestBinder before task insert
Child tasks are inserted only at status = created


---

11. Revised Module Map

axiom/
  app/
    telegram_gateway.py
    session_controller.py
    command_parser.py

  core/
    scheduler.py
    state_machine.py
    policy_engine.py
    permissions.py
    context_builder.py
    manifest_binder.py
    task_committer.py
    role_executor.py
    watchdog.py
    cancellation.py
    resource_limits.py

  agents/
    goal_planner.py
    task_planner.py
    tool_executor.py
    result_verifier.py

  gateways/
    model_gateway.py
    memory_gateway.py
    network_gateway.py
    sandbox_gateway.py

  security/
    sanitizer.py
    classifier_validation.py
    audit.py

  persistence/
    db.py
    schema.sql
    repositories.py

  policy/
    role_manifests/
      goal_planner.json
      task_planner.json
      tool_executor_network_fetch.json
      tool_executor_sandbox_execute.json
      tool_executor_file_limited.json
      result_verifier.json
      operator_control.json
      internal_plan_injection_scan.json

  tests/
    test_state_machine_branches.py
    test_task_class_assignment.py
    test_policy_engine_exists.py
    test_policy_engine_gate.py
    test_policy_approved_flag.py
    test_permissions.py
    test_read_boundaries.py
    test_write_boundaries.py
    test_sandbox_no_network.py
    test_watchdog_startup.py
    test_cancellation.py
    test_plan_checkpoint.py
    test_classifier_injection_set.py
    test_resource_limits.py
    test_plan_injection_scan_owner.py
    test_manifest_binder.py
    test_verifier_write_scope.py
    test_no_direct_role_imports.py
    test_shared_state_write_ceiling.py
    test_shared_state_write_subset.py
    test_operator_control_manifest.py
    test_scheduler_only_state_mutation.py
    test_task_committer.py
    test_single_running_task_invariant.py
    test_memory_dedup_threshold.py
    test_boot_sequence.py
    test_startup_recovery_rules.py
    test_classifier_validation_runtime_contract.py
    test_scheduler_deterministic_chain.py


---

12. Final v1.3.1 Architecture Position

AXIOM Phase 1 now has these corrected invariants:

Scheduler alone mutates task status.

Operator-control tasks request cancellation, pause, resume, or shutdown;
they do not directly transition task state.

Policy Engine is a concrete module.

approved_for_execution is not a task status;
execution approval is recorded through policy_approved and policy_decisions.

Tool Executor may receive any manifest-granted subset of the Phase 1
shared-state write candidates, but no task-structure writes.

Scheduler orchestrates the deterministic chain:
Scanner → checkpoint verification → Committer → Binder → child task insert.

Static import-graph tests enforce no direct role-to-role calls.