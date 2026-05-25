AXIOM Proposal v1.3.2 — Chief Architect Addendum

Resolution of v1.3.1 Coherence Notes N1–N3

0. Patch Status

Field	Value

Proposal version	v1.3.2
Type	Addendum to v1.3.1
Purpose	Resolve N1–N3 before synthesis / implementation planning
Architecture spine changed?	No
Recommended next step	Proceed to DeepSeek targeted F1–F5 re-check, with this addendum attached


Claude’s v1.3.1 review found that F1–F5 were cleanly resolved and recommended advancement to DeepSeek, while asking for three implementation-facing clarifications before Kimi receives the proposal. This addendum resolves those three items. 


---

1. Resolution Matrix

Issue	Panel concern	v1.3.2 decision

N1	Planning-specific statuses lack a clear owner	Planning progress states live on plan_artifacts, not task rows
N2	Scheduler-created verification tasks may bypass PolicyEngine	All tasks, including internal Scheduler-created tasks, traverse PolicyEngine
N3	Tool Executor write whitelist confused with global write surface	Write surfaces are role-scoped; the four-item whitelist applies only to Tool Executor



---

2. N1 — Locus of Planning-Specific Statuses

Decision

Planning-specific statuses are artifact statuses, not task statuses.

The following values belong to:

plan_artifacts.artifact_status

not:

tasks.status

Correct ownership

Status-like value	Correct owner	Reason

plan_artifact_created	tasks.status briefly, optional event only	Marks that the planning task produced an artifact
plan_injection_scan_pending	plan_artifacts.artifact_status	The scan is performed on the artifact
plan_injection_scan_passed	plan_artifacts.artifact_status	The artifact, not the planning task, passes the scan
plan_checkpoint_pending	plan_artifacts.artifact_status	The artifact awaits checkpoint verification
plan_checkpoint_passed	plan_artifacts.artifact_status	The artifact has passed checkpoint verification
child_tasks_committed	tasks.status for the parent planning task	The planning task’s output has been committed
subtask_checkpoint_pending	plan_artifacts.artifact_status	Same artifact lifecycle, but artifact type is subtask_plan
subtask_checkpoint_passed	plan_artifacts.artifact_status	Same artifact lifecycle, but artifact type is subtask_plan


Corrected task status space

The tasks.status field may contain only:

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
child_tasks_committed

Corrected artifact status space

The plan_artifacts.artifact_status field may contain:

proposed
injection_scan_pending
injection_scan_passed
injection_scan_failed
checkpoint_pending
checkpoint_passed
checkpoint_failed
committed
quarantined

Updated planning chain with entity ownership

Goal Planning Task
  tasks.status = created
↓
Scheduler → PolicyEngine
  tasks.policy_approved = 1
↓
Scheduler promotes task
  tasks.status = running
↓
GoalPlanner produces artifact
  plan_artifacts.artifact_status = proposed
↓
Scheduler invokes PlanInjectionScanner
  plan_artifacts.artifact_status = injection_scan_pending
↓
PlanInjectionScanner passes
  plan_artifacts.artifact_status = injection_scan_passed
↓
Scheduler creates checkpoint verification task
  verification task: tasks.status = created
↓
Verification task goes through PolicyEngine
  verification task: tasks.policy_approved = 1
↓
RoleExecutor invokes ResultVerifier
  verification_results row written
↓
Scheduler applies checkpoint result
  plan_artifacts.artifact_status = checkpoint_passed
↓
Scheduler invokes TaskCommitter
  child tasks inserted at tasks.status = created
↓
Artifact marked committed
  plan_artifacts.artifact_status = committed
↓
Parent planning task marked committed
  parent task: tasks.status = child_tasks_committed
↓
Scheduler completes parent task
  parent task: tasks.status = completed

Test implication

tests/test_state_machine_branches.py must assert:

planning task statuses are task-lifecycle states only
plan progress states are artifact-lifecycle states only
verification task statuses belong only to the verification task
child tasks do not exist before artifact_status = checkpoint_passed

This resolves the ambiguity Claude identified about whether planning checkpoint state lived on the planning task, the plan artifact, or the verification task. 


---

3. N2 — PolicyEngine Applies to Scheduler-Created Internal Tasks

Decision

The PolicyEngine gate is universal.

Every task traverses PolicyEngine before execution, including tasks created by the Scheduler itself.

No task is pre-approved merely because it was created by trusted deterministic code.

Universal invariant

No task enters running unless:
tasks.policy_approved = 1
AND
a policy_decisions row exists
AND
PolicyEngine decision = approved

This applies to:

goal_planning
task_planning
tool_execution
verification
operator_control

Corrected internal verification flow

Scheduler creates checkpoint verification task
  tasks.status = created
  task_class = verification
  role_owner = result_verifier
↓
ManifestBinder binds result_verifier manifest
↓
Scheduler calls PolicyEngine
↓
PolicyEngine checks:
  task_class
  role_owner
  manifest hash
  artifact reference
  verifier mode
  read scope
  write scope
  resource limits
↓
If approved:
  tasks.policy_approved = 1
  policy_decisions row written
↓
Scheduler promotes verification task
  tasks.status = running
↓
RoleExecutor invokes ResultVerifier

Why no privileged bypass

A privileged bypass would weaken the simple invariant and create a second execution path. The correct Phase 1 architecture is stricter:

trusted code may create tasks
but trusted code does not bypass the execution gate

Test implication

tests/test_policy_engine_gate.py must include:

Scheduler-created verification task cannot run without PolicyEngine approval
Scheduler-created operator_control task cannot run without PolicyEngine approval
Scheduler-created security_review task cannot run without PolicyEngine approval
internal task with missing manifest is blocked
internal task with invalid role_owner is blocked

This follows Claude’s recommendation to keep the PolicyEngine universal because verification tasks have manifests and the marginal cost is worth the cleaner invariant. 


---

4. N3 — Role-Scoped Write Surfaces

Decision

The four-item shared-state whitelist from v1.3.1 is not global.

It is the Tool Executor write surface only.

Other roles have separate role-scoped write surfaces defined in their own manifests.

Role write-surface table

Role	Allowed write surface

Goal Planner	plan_artifacts proposed artifact only
Task Planner	plan_artifacts proposed subtask artifact only
Tool Executor	Own result/error fields + Tool Executor shared-state whitelist
Result Verifier	verification_results row only
Telegram Gateway / Operator Control	Intent flags only: cancel_requested, pause_requested, shutdown_requested
Scheduler	Task status transitions, policy execution sequencing
PolicyEngine	policy_decisions, tasks.policy_approved*
PlanInjectionScanner	plan_artifacts.injection_scan_status, security_events
TaskCommitter	Child task creation after checkpoint pass
ManifestBinder	task_permissions creation during commit transaction
Memory Gateway	Approved semantic memory writes
Network Gateway	Sanitized fetch artifacts/results
Sandbox Gateway	Sandbox execution result records


Tool Executor-specific whitelist

Only Tool Executor uses this Phase 1 shared-state candidate set:

memory.write_candidate
artifact.create_reference
security_event.append
tool_invocation.append

A Tool Executor manifest may grant any subset of those four, but nothing outside them.

Result Verifier write surface

The Result Verifier manifest may write only:

verification_results.verification_id
verification_results.task_id
verification_results.verifier_mode
verification_results.verdict
verification_results.verdict_reason
verification_results.confidence
verification_results.security_labels
verification_results.recommended_next_state
verification_results.created_at

It may not write:

tasks.status
tasks.policy_approved
plan_artifacts.artifact_status
task_permissions.*
memory_items.*
memory_vectors.*

Test implication

tests/test_shared_state_write_subset.py applies only to Tool Executor manifests.

tests/test_verifier_write_scope.py applies only to Result Verifier manifests.

They are separate tests because they enforce different role-scoped write surfaces. Claude explicitly identified that Kimi could not reconcile those tests unless the whitelist was clarified as role-scoped rather than global. 


---

5. Minor Note — verified vs. completed

Decision

verified is a transient task status.

completed is the terminal success status.

Correct transition

awaiting_verification
↓
verified
↓
completed

Meaning

Status	Meaning

verified	Result Verifier accepted the output, but Scheduler has not yet closed the task
completed	Scheduler has closed the task and emitted final task event


Rule

A task should not remain in verified across scheduler ticks unless the Scheduler crashes between verification and completion. If found at startup:

verified → completed

unless there is a missing audit event, in which case:

verified → blocked

with recovery reason.


---

6. Minor Note — Shutdown Irrevocability

Decision

/shutdown_after_current is intentionally one-way for the current session.

Once:

sessions.shutdown_requested = true

the same session cannot clear it.

Rationale

Shutdown is a safety and lifecycle control. Allowing /resume to clear shutdown would blur pause/resume semantics with shutdown semantics.

Recovery from accidental shutdown

If the operator fat-fingers:

/shutdown_after_current

the recovery path is:

Let AXIOM stop after current task
↓
Restart session manually
↓
Startup watchdog runs
↓
Telegram receives recovery summary

Correct distinction

Command	Reversible in same session?	Notes

/pause_after_current	Yes	/resume sets pause_requested = false
/shutdown_after_current	No	Ends current session after safe boundary
/cancel_current_chain	No for that chain	New goal can be submitted afterward



---

7. Revised End-to-End Trust Chain

Human Telegram goal
↓
Command Parser
↓
Ingress Sanitizer
↓
Task inserted:
  tasks.task_class = goal_planning
  tasks.status = created
↓
Scheduler calls PolicyEngine
↓
PolicyEngine writes policy_decisions row
↓
Scheduler sets:
  tasks.policy_approved = 1
  tasks.status = running
↓
RoleExecutor invokes GoalPlanner
↓
GoalPlanner writes:
  plan_artifacts.artifact_status = proposed
↓
Scheduler invokes PlanInjectionScanner
↓
PlanInjectionScanner writes:
  plan_artifacts.artifact_status = injection_scan_passed
  security_events row
↓
Scheduler creates verification task:
  tasks.task_class = verification
  tasks.status = created
↓
Scheduler calls PolicyEngine for verification task
↓
PolicyEngine approves verification task
↓
Scheduler promotes verification task:
  tasks.status = running
↓
RoleExecutor invokes ResultVerifier in plan_checkpoint mode
↓
ResultVerifier writes verification_results row
↓
Scheduler interprets verdict through StateMachine
↓
Scheduler sets:
  plan_artifacts.artifact_status = checkpoint_passed
↓
Scheduler invokes TaskCommitter
↓
TaskCommitter validates artifact schema
↓
TaskCommitter invokes ManifestBinder
↓
ManifestBinder writes task_permissions rows
↓
TaskCommitter inserts child tasks:
  tasks.status = created
↓
Scheduler sets:
  plan_artifacts.artifact_status = committed
  parent task.status = child_tasks_committed
↓
Scheduler closes parent:
  parent task.status = completed


---

8. Revised Acceptance Tests

N1 tests

tests/test_plan_artifact_status_locus.py

Required assertions:

plan_injection_scan_passed is not a valid tasks.status
plan_injection_scan_passed is valid plan_artifacts.artifact_status
checkpoint_passed is valid plan_artifacts.artifact_status
child_tasks_committed is valid parent tasks.status
child tasks do not exist before artifact_status = checkpoint_passed

N2 tests

tests/test_internal_tasks_policy_gate.py

Required assertions:

Scheduler-created verification task starts at status = created
Scheduler-created verification task has policy_approved = 0 before PolicyEngine
RoleExecutor refuses verification task without policy_approved = 1
PolicyEngine writes policy_decision for internal verification task
Scheduler promotes internal verification task only after approval

N3 tests

tests/test_role_scoped_write_surfaces.py

Required assertions:

Tool Executor whitelist is not global
Result Verifier may write verification_results only
Goal Planner may write proposed plan artifact only
Task Planner may write proposed subtask artifact only
Operator Control may write intent flags only
ManifestBinder rejects cross-role write surfaces

Minor-note tests

tests/test_verified_to_completed_transition.py
tests/test_shutdown_irrevocability.py

Required assertions:

verified transitions to completed on next scheduler tick
startup recovery handles stale verified tasks
shutdown_requested cannot be cleared in same session
pause_requested can be cleared by /resume


---

9. Final v1.3.2 Architecture Position

AXIOM Phase 1 now has these added clarifications:

Planning progress states live on plan_artifacts, not on tasks.

Planning tasks carry ordinary task lifecycle status; artifacts carry plan lifecycle status.

Every task, including Scheduler-created internal verification tasks,
traverses PolicyEngine before execution.

The Tool Executor four-item shared-state whitelist is role-specific,
not a global write surface.

Each role has its own manifest-defined write surface.

verified is transient; completed is terminal.

shutdown_after_current is intentionally irreversible inside the current session.