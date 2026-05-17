AXIOM Proposal v1.3 — Chief Architect Revision Delta

Resolution of v1.2 Coherence Return

0. Status

Field	Value

Proposal version	v1.3
Type	Revision delta to v1.2
Purpose	Resolve 8 blocking coherence issues + secondary coherence gaps
Architecture spine changed?	No
Implementation-ready?	Not until panel accepts this revision
Next review	Claude coherence confirmation → DeepSeek targeted re-check


v1.3 preserves the v1.2 architecture: sequential runtime, queue-only coordination, SQLite persistence, Telegram control plane, explicit permission manifests, bounded context bundles, and sandbox/network separation. The changes below make the enforcement points concrete enough for implementation planning.


---

1. Blocking Issue Resolution Matrix

#	Issue	v1.3 resolution

1	plan_injection_scan has no owner	Assign to security/sanitizer.py::PlanInjectionScanner; verdict stored in plan_artifacts, security_events, and checkpoint evidence
2	Manifest creation/binding undefined	Add deterministic ManifestBinder; LLMs request capabilities, but deterministic code creates manifests
3	Verifier write scope conflict	Define verification_results record; Verifier writes verdict object only, never task status
4	No mechanical no-direct-role-call verification	Add static import-graph test and runtime role-dispatch guard
5	Shared-state write scope too open	Add hard Phase 1 ceiling for manifest-granted shared-state writes
6	operator_control manifest undefined	Define exact allowed operator-control capabilities
7	Plan/Subtask Committer missing from module map	Add deterministic core/task_committer.py
8	“At most one running task” not enforced	Add DB-level partial unique index + scheduler watchdog assertion



---

2. Issue 1 — Plan Injection Scan Owner

Decision

The plan-injection scan is owned by:

security/sanitizer.py::PlanInjectionScanner

It is not performed by the Goal Planner, Task Planner, or Result Verifier.

Placement

Goal Planner / Task Planner produces proposed plan artifact
↓
PlanInjectionScanner runs
↓
Plan artifact marked injection_scan_passed / failed / quarantined
↓
Result Verifier runs checkpoint mode only if scan passed
↓
Child tasks committed only after checkpoint passes

Manifest used by scanner

The scan runs under a fixed internal security manifest:

{
  "manifest_name": "internal_plan_injection_scan",
  "role_owner": "system_security",
  "allowed_read_scopes": [
    "plan_artifact.self",
    "constraints.summary",
    "core_values.summary"
  ],
  "allowed_write_fields": [
    "plan_artifacts.injection_scan_status",
    "plan_artifacts.security_labels",
    "security_events"
  ],
  "forbidden_tools": [
    "network.fetch",
    "sandbox.execute",
    "memory.write_candidate",
    "task.create"
  ]
}

Verdict storage

Location	Stored fields

plan_artifacts	injection_scan_status, security_labels, scan_completed_at
security_events	scan event, labels, reason, source artifact
plan_checkpoints	references scan result as required checkpoint evidence


Required schema fields

plan_artifacts.injection_scan_status
  allowed: not_scanned | passed | failed | quarantined

plan_artifacts.security_labels
  JSON array

plan_artifacts.scan_completed_at
  timestamp

Rule

A plan artifact cannot enter checkpoint verification unless:

plan_artifacts.injection_scan_status = 'passed'

This satisfies the Core Value requirement that security boundaries exist before the protected component operates. 


---

3. Issue 2 — Manifest Creation and Binding Flow

Decision

Agents never create their own manifests.

They may emit capability requests. A deterministic component creates and binds manifests.

New component

core/manifest_binder.py

Classes:

ManifestBinder
ManifestTemplateLoader
ManifestHasher

Manifest creation flow

Plan or subtask artifact proposes task
↓
TaskCommitter validates task_class + capability_request
↓
ManifestBinder loads matching template
↓
ManifestBinder parameterizes safe fields only
↓
Manifest hash is computed
↓
Task row and task_permissions row are inserted in same DB transaction
↓
Policy Engine verifies manifest before approved_for_execution

What the LLM may output

Allowed:

{
  "task_title": "Fetch source page",
  "task_class": "tool_execution",
  "capability_request": "network.fetch",
  "requested_domains": ["example.com"],
  "acceptance_criteria": "Fetch succeeds and content is stored as untrusted artifact"
}

Forbidden:

{
  "allowed_tools": ["network.fetch", "memory.write", "sandbox.execute"],
  "allowed_write_fields": ["tasks.status"]
}

The second form is rejected because it attempts to author its own permissions.

Manifest binding fields

Every task_permissions row includes:

manifest_id
task_id
template_name
template_version
template_hash
bound_manifest_hash
created_by_component = 'ManifestBinder'
created_from_artifact_id
created_at
immutable = true

Manifest immutability rule

Once bound, a task manifest is immutable.

If permissions need to change:

old task → blocked
new task → new manifest

No in-place manifest expansion is allowed.

Trust boundary

The trusted author of a manifest is deterministic AXIOM code, not model output. This is required for zero-trust enforcement under Core Value 3. 


---

4. Issue 3 — Result Verifier Write Scope

Decision

The Result Verifier writes a verdict object, not task state.

Corrected write scope

Role	May write

Result Verifier	verification_results row only
Scheduler	Task status transitions
Policy Engine	Approval decision record
Result Verifier	No direct task mutation


verification_results schema

verification_id
task_id
verifier_mode
verdict
verdict_reason
confidence
security_labels
recommended_next_state
created_at

Important clarification

recommended_next_state is advisory.

The Result Verifier may say:

recommended_next_state = 'completed'

but only the Scheduler can apply:

tasks.status = 'completed'

Scheduler rule

The Scheduler must map verifier output through policy:

Verifier verdict
↓
Scheduler transition policy
↓
Allowed state transition or escalation

So the Verifier influences state transitions as evidence, but does not control them.


---

5. Issue 4 — Mechanical Verification of No Direct Role-to-Role Calls

Decision

Add both static and runtime enforcement.

Static import-graph test

New test:

tests/test_no_direct_role_imports.py

Rule:

agents/*.py may not import another agents/*.py module

Allowed:

agents/goal_planner.py → core.schemas
agents/tool_executor.py → core.schemas
agents/result_verifier.py → core.schemas

Forbidden:

agents/goal_planner.py → agents/task_planner.py
agents/task_planner.py → agents/tool_executor.py
agents/tool_executor.py → agents/result_verifier.py

Runtime dispatch guard

Only this component may instantiate or call role modules:

core/role_executor.py

Role modules receive:

context_bundle
manifest_view

They do not receive references to other roles.

Acceptance criterion

The build fails if:

pytest tests/test_no_direct_role_imports.py

detects a role-to-role import.

This makes Core Value 5 mechanically testable instead of merely stated. 


---

6. Issue 5 — Maximum Shared-State Write Scope

Decision

Phase 1 manifests may grant only four shared-state write candidates.

Allowed shared-state write candidates

memory.write_candidate
artifact.create_reference
security_event.append
tool_invocation.append

Forbidden for Tool Executor in Phase 1

A Tool Executor manifest may never grant writes to:

tasks.status
tasks.parent_task_id
tasks.task_class
tasks.role_owner
tasks.input_payload
tasks.acceptance_criteria
tasks.manifest_id
task_permissions.*
plan_artifacts.*
plan_checkpoints.*
sessions.*
config_snapshots.*

Corrected rule

Tool Executor may write its own result/error fields,
plus one of the explicitly whitelisted shared-state write candidates,
only if granted by the bound manifest.

Memory write clarification

memory.write_candidate is not a memory write.

It creates a candidate record that must pass:

sanitization
deduplication
source attribution
embedding
Memory Gateway approval

before entering semantic memory.

This preserves Core Value 3 by preventing a Tool Executor from mutating task structure or trusted memory directly. 


---

7. Issue 6 — operator_control Manifest

Decision

Define operator_control.json as a narrow high-priority control manifest.

It has priority interrupt, but not broad system authority.

Allowed operator-control commands

/status
/cancel_current_chain
/cancel
/stop_current
/pause_after_current
/resume
/shutdown_after_current

operator_control.json

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
    "tasks.status",
    "sessions.pause_requested",
    "sessions.shutdown_requested",
    "task_events"
  ],
  "write_constraints": {
    "tasks.status": [
      "cancelled"
    ],
    "scope": [
      "active_task",
      "unstarted_descendants"
    ]
  },
  "forbidden_writes": [
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

Operator-control limitation

Operator-control can cancel or pause execution. It cannot edit tasks, rewrite goals, alter manifests, write memory, or approve unsafe work.

This keeps Telegram as the control plane without turning it into a privileged backdoor.


---

8. Issue 7 — Plan Committer and Subtask Committer

Decision

Add a deterministic module:

core/task_committer.py

Classes:

PlanCommitter
SubtaskCommitter

Responsibility

Committers turn verified artifacts into queue records.

They do not reason.
They do not call models.
They do not alter plan content.
They only validate and commit.

Flow

plan_artifact checkpoint passed
↓
PlanCommitter reads plan artifact
↓
PlanCommitter validates schema
↓
PlanCommitter assigns task_class
↓
ManifestBinder binds manifests
↓
Child tasks inserted at status = created

For Task Planner subtasks:

subtask_artifact checkpoint passed
↓
SubtaskCommitter reads subtask artifact
↓
SubtaskCommitter validates schema
↓
SubtaskCommitter assigns task_class
↓
ManifestBinder binds manifests
↓
Child tasks inserted at status = created

Module map update

core/
  scheduler.py
  state_machine.py
  context_builder.py
  permissions.py
  manifest_binder.py
  task_committer.py
  role_executor.py
  watchdog.py
  cancellation.py
  resource_limits.py


---

9. Issue 8 — Enforce “At Most One Running Task”

Decision

Enforce sequential execution at three layers:

1. Database constraint


2. Scheduler transaction


3. Watchdog assertion



SQLite partial unique index

CREATE UNIQUE INDEX IF NOT EXISTS idx_only_one_running_task
ON tasks(status)
WHERE status = 'running';

Because every running task has the same status value, this prevents more than one row from entering running.

Scheduler transaction rule

BEGIN IMMEDIATE;
SELECT COUNT(*) FROM tasks WHERE status = 'running';
if count = 0:
    promote next eligible task to running
else:
    do not promote
COMMIT;

Watchdog assertion

Scheduler-loop watchdog runs:

SELECT COUNT(*) AS running_count
FROM tasks
WHERE status = 'running';

If:

running_count > 1

then AXIOM enters:

system_error

and stops autonomous execution.

Test

tests/test_single_running_task_invariant.py

Required assertions:

cannot insert two running tasks
scheduler does not promote if one task is running
watchdog detects corrupted multi-running state

This pins the central sequential-runtime invariant to something testable.


---

10. Secondary Issue — Memory Dedup Threshold

Decision

Adopt the legacy default threshold as Phase 1 default:

cosine_similarity >= 0.92 → duplicate candidate

Memory Gateway behavior

Condition	Action

similarity < 0.92	Insert as new memory
similarity ≥ 0.92	Reject as duplicate or link to existing memory
same source hash	Reject duplicate
low sanitizer confidence	Quarantine candidate
embedding model mismatch	Block until migration/re-embedding policy exists


Schema fields

memory_items.source_hash
memory_items.dedup_status
memory_items.duplicate_of_memory_id
memory_vectors.embed_model
memory_vectors.embed_dim

The Legacy Reference records pre-rebuild consensus around a ~0.92 cosine threshold for sqlite-vec deduplication, so v1.3 adopts it as the Phase 1 default rather than leaving it implicit. 


---

11. Secondary Issue — Boot Sequence

Decision

Define startup order explicitly.

AXIOM Phase 1 boot sequence

1. Load environment/config
2. Validate required secrets and Telegram whitelist
3. Open SQLite database
4. Apply schema migrations
5. Verify SQLite settings: WAL + busy_timeout
6. Load config snapshot into sessions table
7. Validate local model profile availability
8. Validate classifier profile and test-suite status
9. Check Brave/Search provider config if network tools enabled
10. Check sandbox isolation status if sandbox tools enabled
11. Run startup watchdog
12. Recover stale tasks according to recovery rules
13. Start Telegram Gateway
14. Start Sequential Scheduler
15. Send Telegram “AXIOM ready” status summary

Important boot rule

If classifier validation has not passed:

autonomous operation = disabled

If sandbox no-network validation has not passed:

sandbox.execute = disabled

If Telegram whitelist is missing:

startup aborts


---

12. Secondary Issue — Recovery Semantics

Decision

Make stale-task recovery deterministic.

Startup recovery rules

For each task with:

status = running

apply this order:

Condition	Recovery action

cancel_requested = true	cancelled
quarantine_flag = true	quarantined
task was in sandbox execution	failed, unless manifest allows retry
task had completed tool output but no verification	awaiting_verification
attempt_count >= max_attempts	failed
lease expired and retry allowed	retry_pending
lease expired and retry not allowed	failed
unknown state	blocked


Audit requirement

Every recovery mutation writes:

task_events.event_type = 'startup_recovery'

with:

previous_status
new_status
reason
session_id
timestamp


---

13. Secondary Issue — classifier_validation.py vs sanitizer.py

Decision

Separate runtime enforcement from validation harness.

Module	Responsibility

security/sanitizer.py	Runtime sanitization, injection scanning, quarantine decisions
security/classifier_validation.py	Test harness proving current classifier profile is acceptable before autonomous operation
classifier_tests table	Stores test suite version, model profile, pass/fail, timestamp


Runtime path

Input payload
↓
sanitizer.py
↓
local classifier call
↓
confidence threshold check
↓
safe label / quarantine
↓
queue write or block

Validation path

startup
↓
classifier_validation.py checks last passed test
↓
if model profile matches and tests passed: enable sanitizer classifier mode
↓
if not: block autonomous operation or run validation suite

Classifier profile key

model_name
quantization
thinking_mode
prompt_version
test_suite_version

If any of these change, validation expires.


---

14. Updated Acceptance Tests

Add the following tests to v1.3.

tests/test_plan_injection_scan_owner.py
tests/test_manifest_binder.py
tests/test_verifier_write_scope.py
tests/test_no_direct_role_imports.py
tests/test_shared_state_write_ceiling.py
tests/test_operator_control_manifest.py
tests/test_task_committer.py
tests/test_single_running_task_invariant.py
tests/test_memory_dedup_threshold.py
tests/test_boot_sequence.py
tests/test_startup_recovery_rules.py
tests/test_classifier_validation_runtime_contract.py

Required pass conditions

Test	Required result

Plan injection scan	Child tasks cannot commit unless scan passed
Manifest binder	LLM-authored permissions are rejected
Verifier write scope	Verifier cannot mutate tasks.status
No direct role imports	Role module cannot import another role module
Shared write ceiling	Tool Executor cannot receive task-structure write permission
Operator control	/cancel cannot edit task payloads/manifests/memory
Task committer	Only checkpoint-passed artifacts become tasks
Single running task	DB and scheduler prevent multiple running tasks
Memory dedup	≥0.92 cosine candidate links/rejects duplicate
Boot sequence	Startup aborts or disables unsafe capability when preconditions fail
Recovery rules	Stale running tasks deterministically recover
Classifier contract	Runtime sanitizer refuses unvalidated classifier profile



---

15. Revised Module Map

axiom/
  app/
    telegram_gateway.py
    session_controller.py
    command_parser.py

  core/
    scheduler.py
    state_machine.py
    context_builder.py
    permissions.py
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
    test_operator_control_manifest.py
    test_task_committer.py
    test_single_running_task_invariant.py
    test_memory_dedup_threshold.py
    test_boot_sequence.py
    test_startup_recovery_rules.py
    test_classifier_validation_runtime_contract.py


---

16. v1.3 Final Architecture Position

AXIOM Phase 1 now has explicit owners and tests for the formerly implicit enforcement points:

Plan injection scanning is owned by PlanInjectionScanner.

Manifests are created only by deterministic ManifestBinder code.

Verified plan artifacts are committed only by deterministic TaskCommitter code.

Result Verifier writes verdict records only.

Scheduler alone mutates task state.

Tool Executor shared-state writes are capped to a Phase 1 whitelist.

Operator-control tasks are high priority but narrowly permissioned.

No direct role-to-role calls are enforced by import-graph testing.

Sequential execution is enforced by DB constraint, scheduler transaction, and watchdog assertion.

Classifier validation gates runtime sanitizer use.

Startup and recovery behavior are deterministic.