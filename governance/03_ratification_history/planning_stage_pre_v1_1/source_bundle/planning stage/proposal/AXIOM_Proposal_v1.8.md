AXIOM Proposal v1.8 — Chief Architect Revision

Resolution of v1.7 Panel Synthesis

0. Status

Field	Value

Proposal version	v1.8
Type	Targeted revision to v1.7
Scope	Resolves blocking objections A–H, specification touch-ups I′–L, and Qwen binding conditions
Architecture spine changed?	No
Recommended next review	Targeted coherence + DeepSeek re-check on v1.8 deltas only


The v1.7 panel synthesis says the architecture spine is sound, but it cannot proceed because several security-critical concepts remained underspecified: artifact risk class, privileged task classes, call timeouts, heartbeat liveness, operator-control capability re-establishment, TaskCommitter atomicity, memory verification, and classifier calibration. 


---

1. Resolution Matrix

Item	v1.8 resolution

A	Defines deterministic artifact risk classification: high_risk vs ordinary
B	Enumerates closed privileged task-class list
C	Specifies per-provider-call timeout ceiling and timeout behavior
D	Defines heartbeat liveness threshold and supervisor action
E	Defines OperatorControlCapability re-establishment on Telegram restart
F	Specifies TaskCommitter atomic transaction boundary
G	Routes Memory Gateway responses through Result Verifier
H	Adds classifier calibration acceptance criterion
I′	Adds PlanInjectionScanner to module map
L	Specifies resource_limits.py runtime enforcement
K	Delegates remaining recovery mechanics to Kimi with architectural boundaries
Touch-up	Broadens orphan provider_usage recovery to all non-current sessions
Touch-up	Handles confident embedded_instruction with no rule hit
Qwen	Restates binding runtime constraints



---

2. Binding Runtime Conditions

These conditions are binding in v1.8.

Constraint	Required behavior

Execution model	Strict sequential execution
Thread cap	Maximum 4 threads: main supervisor, Telegram, Scheduler, BootstrapValidationWorker
Local model	qwen3:4b, Q4 quantized, memory-mapped through Ollama
Context bundle	Hard cap: 500 KB serialized
Sandbox RAM	Hard cap: 256 MB via Windows Job Object
Vector search	sqlite-vec maximum 100 vectors per query/batch
Token budget	2× safety margin in budget_policy before cloud dispatch
Web search	Brave Search API or panel-approved free-tier alternative must be confirmed before web search is enabled


These are carried forward because the target remains a Celeron N4500 / 8 GB RAM / Windows 11 system with near-zero API budget. The Constraints Register identifies the hardware and budget limits as hard constraints and warns against unaccounted parallel execution on the available runtime headroom. 


---

3. A — Artifact Risk Class Defined

Decision

Artifact risk class is computed deterministically by PlanInjectionScanner.

The Goal Planner may not assign or override its own artifact risk class.

Schema addition

Add to plan_artifacts:

risk_class TEXT CHECK(risk_class IN ('ordinary', 'high_risk'))
risk_reasons JSON
risk_classified_at TEXT
risk_classified_by TEXT DEFAULT 'PlanInjectionScanner'

Risk classification rule

risk_class = 'high_risk' if ANY high-risk trigger is true.
risk_class = 'ordinary' only if NO high-risk triggers are true.

High-risk triggers

A plan artifact is high_risk if it contains or implies any of the following:

Trigger	Detection source

Any child task requests sandbox.execute	Plan task capability request
Any child task requests network.fetch	Plan task capability request
Any child task requests memory.write_candidate	Plan task capability request
Any child task requests filesystem write access	Plan task capability request
Any child task requests shared-state write candidates	Manifest/capability request
Any child task requests privileged task class	Task-class scan
Any chain combines network and sandbox anywhere in the same parent chain	Plan graph scan
Any injection rule matches, including non-critical rule hits	Rule scanner
Encoded or obfuscated content is detected	Rule scanner
Artifact source includes external fetched content	Artifact metadata
Proposed child task count exceeds 8	Plan schema
Proposed chain depth exceeds 3	Plan schema
Any task lacks testable acceptance criteria	Schema scan
Any task requests capability outside known vocabulary	Capability scan


Everything else is ordinary.

Scanner rule references

Rules 6, 7, 10, and 11 now refer to:

plan_artifacts.risk_class

not to prose labels.

Revised scanner rules using risk class

Rule	Condition	Decision

6	risk_class = high_risk and classifier confidence < 0.90	quarantined
7	risk_class = ordinary and classifier confidence < 0.80	needs_human_input
10	risk_class = high_risk + valid schema + classifier label safe/untrusted + confidence ≥0.90	passed
11	risk_class = ordinary + valid schema + classifier label safe/untrusted + confidence ≥0.80	passed


Important consequence

A non-critical rule hit makes the artifact high_risk, but it does not automatically quarantine it. It passes only if the classifier returns a safe/untrusted label with confidence ≥0.90 and no earlier quarantine rule fires.

This closes the “high-risk vs ordinary” undefined variable identified by the panel. 


---

4. B — Privileged Task Classes Enumerated

Decision

The privileged task-class set is closed.

PRIVILEGED_TASK_CLASSES = {
  "operator_control",
  "bootstrap_validation"
}

No other task class is privileged in Phase 1.

Rule 3 replacement

Replace:

Privileged task-class request, including operator_control

with:

Task artifact requests task_class in {'operator_control', 'bootstrap_validation'}

Valid creators

Privileged task class	Only allowed creator

operator_control	Telegram Gateway via OperatorControlInserter
bootstrap_validation	Telegram Gateway via bootstrap command path, executed by BootstrapValidationWorker


Scanner action

If a Goal Planner or Task Planner artifact proposes either privileged class:

PlanInjectionScanner decision = quarantined
security_events.privileged_task_class_spoof_attempt
parent task → quarantined
child tasks → not created

This makes the security rule closed and implementable. The panel explicitly flagged the open wording “including operator_control” as ambiguous. 


---

5. C — Cloud-Call Maximum Duration

Decision

All cloud model calls are synchronous, timeout-bound, and capped per provider call, not per cascade chain.

Timeout values

Provider-call type	Timeout

Primary provider call	30 seconds
Fallback provider call	45 seconds
Large-context provider call	60 seconds
Absolute hard ceiling	90 seconds


No provider call may exceed 90 seconds in Phase 1.

Timeout enforcement

ModelGateway applies timeout at the HTTP/client layer for each individual provider call.

timeout applies to each provider call
not to the whole cascade

Timeout behavior

Event	Behavior

Primary timeout	Mark provider call timeout; try fallback if manifest budget allows
Fallback timeout	Mark provider call timeout; no second fallback unless manifest explicitly permits
Hard ceiling reached	Task → retry_pending if attempts remain; otherwise needs_human_input or failed
Cancel requested during call	Call continues until timeout/response; Scheduler cancels at next boundary
Timeout after cancel	provider_usage.status = timeout_after_cancel_requested


Cascade limit

A single task may make at most:

1 primary call + 1 fallback call

unless the task manifest explicitly grants more. Default maximum cloud calls per task:

max_model_calls = 2

This sets the operator responsiveness bound that the panel said was missing: /cancel_current_chain can be delayed only until the current provider call returns or hits its configured timeout. 


---

6. D — Scheduler Heartbeat Liveness Threshold and Dead-Scheduler Action

Decision

Heartbeat liveness is derived from the maximum provider-call hard ceiling.

Heartbeat update rule

Scheduler writes scheduler_heartbeat:

1. At the start of every scheduler tick


2. Immediately before any blocking provider call


3. Immediately after any blocking provider call returns or times out


4. Immediately before sandbox execution


5. Immediately after sandbox execution returns or times out



Heartbeat fields

session_id
last_tick_at
last_blocking_operation_started_at
last_blocking_operation_type
active_task_id
active_chain_id
last_action
scheduler_state
tick_count

Liveness threshold

scheduler_stale_threshold_seconds = 120

Derivation:

90s max provider-call hard ceiling + 30s margin = 120s

Stale scheduler definition

Scheduler is stale when:

now - scheduler_heartbeat.last_tick_at > 120 seconds
AND
scheduler_state NOT IN ('clean_shutdown', 'paused')

Supervisor action on stale scheduler

Phase 1 action is fail closed and human-escalate, not automatic kill/restart.

Main supervisor detects stale Scheduler
↓
sessions.scheduler_status = stale
↓
sessions.autonomous_operation_enabled = false
↓
sessions.shutdown_requested = true
↓
Telegram receives alert if available
↓
No new tasks are promoted
↓
Operator must restart AXIOM manually

Why no automatic restart

Automatic in-process restart after unknown scheduler staleness risks double-running or corrupting queue state. Manual restart triggers startup recovery and preserves auditability.

Telegram message

Scheduler heartbeat stale for >120 seconds. Autonomous execution has been halted. Restart AXIOM from the laptop to run startup recovery.

This resolves the missing liveness threshold and action, and it avoids false positives during legitimate 90-second calls by using a threshold above the hard ceiling. 


---

7. E — OperatorControlCapability Re-Established on Telegram Restart

Decision

SessionController owns the OperatorControlCapability object for the full session lifetime.

Telegram Gateway receives it on construction and on restart.

Capability lifecycle

SessionController boot
↓
create OperatorControlCapability object
↓
store only in SessionController memory
↓
pass object reference to TelegramGateway instance
↓
TelegramGateway passes object to OperatorControlInserter when needed

Restart flow

Telegram thread crash
↓
SessionController stops old TelegramGateway instance
↓
SessionController creates new TelegramGateway instance
↓
SessionController passes same OperatorControlCapability object
↓
New Telegram thread starts
↓
OperatorControlInserter validates object identity against SessionController-held token

Fail-closed rule

If the capability cannot be re-passed or validated:

Telegram restart fails
operator_control disabled
sessions.operator_interface_status = unavailable
sessions.shutdown_requested = true
Scheduler safe-stops at next boundary

There is no degraded Telegram Gateway without operator-control capability.

Security invariant

No OperatorControlCapability object = no operator_control task creation.

This preserves the object-identity security model across Telegram restart, which the panel identified as the missing security-critical part of restart behavior. 


---

8. F — TaskCommitter Transactional Boundary

Decision

All child tasks produced from a verified plan artifact commit atomically in one SQLite transaction.

Partial commits are not allowed.

Atomic commit sequence

BEGIN IMMEDIATE;

1. Verify plan_artifacts.artifact_status = checkpoint_passed
2. Verify plan_artifacts.commit_status = not_started
3. Validate full plan artifact schema
4. Validate every child task before inserting any child task
5. Validate creator allowlist for every child task
6. Invoke ManifestBinder for every child task and stage manifests in memory
7. Generate commit_batch_id
8. Insert all child task rows with commit_batch_id
9. Insert all task_permissions rows
10. Insert all task_events rows
11. Set plan_artifacts.commit_status = committed
12. Set parent task.status = child_tasks_committed

COMMIT;

Rollback rule

If any step fails:

ROLLBACK;
no child task is visible to Scheduler
plan_artifacts.commit_status = not_started or failed
parent task → blocked
task_events.commit_failed written after rollback

Scheduler selection guard

Scheduler may only select child tasks where:

tasks.status = 'created'
AND tasks.commit_batch_id IS NOT NULL
AND EXISTS (
  SELECT 1 FROM task_permissions
  WHERE task_permissions.task_id = tasks.task_id
)

Crash recovery

On startup, detect:

plan_artifacts.artifact_status = checkpoint_passed
AND commit_status != committed

Recovery action:

Condition	Action

No child tasks visible	Resume TaskCommitter
Some child tasks visible but commit not marked committed	Mark all children in batch blocked; parent → blocked; write security_events.partial_commit_detected
Child tasks visible without task_permissions	Mark children blocked; parent → blocked


Architectural stance

Primary guarantee is atomic transaction. Partial-commit recovery is a corruption fallback, not the normal path.

This closes the mid-chain failure gap where a crash after 3 of 5 child-task inserts could leave runnable orphan work. 


---

9. G — Memory Verification Loop Closed

Decision

memory.write_candidate tasks are not exempt from verification.

Memory Gateway responses are routed to Result Verifier exactly like other tool outputs.

Gateway response storage

Memory Gateway writes:

gateway_responses

with:

gateway_response_id
task_id
gateway_name = memory_gateway
operation_type = memory.write_candidate
status
dedup_status
duplicate_of_memory_id
write_status
sanitization_status
embedding_status
summary
created_at

Required statuses

Field	Values

status	success, blocked, quarantined, failed
dedup_status	new_inserted, duplicate_linked, skipped_duplicate, not_evaluated
write_status	inserted, skipped_duplicate, quarantined, blocked, failed


Verification context

For memory tasks, Context Builder must include:

task.input_payload
task.output_payload
gateway_responses for task_id
memory candidate text/hash
dedup_status
duplicate_of_memory_id
write_status
sanitization_status
acceptance_criteria

Verifier interpretation

Memory Gateway result	Result Verifier interpretation

new_inserted + acceptance criteria require new storage	Pass
duplicate_linked + criteria allow dedup/linking	Pass
skipped_duplicate + criteria required new unique storage	Fail or needs_human_input
quarantined	Fail security review
blocked	Fail or needs_human_input
failed	Fail


State transition

Tool Executor produces memory.write_candidate
↓
Memory Gateway processes candidate
↓
Memory Gateway writes gateway_response
↓
Task enters awaiting_verification
↓
Result Verifier reviews gateway_response
↓
Scheduler applies verifier verdict

This removes the inconsistent treatment of memory writes and closes the verification loop the panel identified. 


---

10. H — Classifier Calibration Acceptance Criterion

Decision

Classifier validation has two gates:

1. Accuracy gate


2. Confidence calibration gate



Both must pass before the local classifier can act as a scanner/sanitizer security boundary.

Calibration test set

Use the existing 120-sample validation set plus confidence buckets.

Composition remains:

Category	Samples

Malicious / injection samples	90
Benign controls	30
Critical malicious samples	40 of the 90 malicious samples


Attack-vector coverage must include:

instruction override
role escalation
queue manipulation
manifest manipulation
sandbox/network bypass
memory poisoning
secret extraction
encoded instructions
web-content injection
benign controls

Required accuracy thresholds

Metric	Pass condition

Critical malicious samples caught	40 / 40
Overall malicious recall	≥95%
Benign false-positive rate	≤15%


Required calibration thresholds

For the two confidence cutoffs used by PlanInjectionScanner:

Cutoff	Required empirical behavior

0.90 high-risk safe-pass threshold	At least 95% precision on samples classified safe/untrusted above 0.90
0.80 ordinary safe-pass threshold	At least 90% precision on samples classified safe/untrusted above 0.80
Critical samples above either safe-pass threshold	0 critical misses


Calibration failure behavior

Failure	Behavior

Critical miss	Autonomous operation disabled
High-risk precision below 95%	Raise high-risk threshold to 0.95 and rerun calibration
Ordinary precision below 90%	Raise ordinary threshold to 0.90 and rerun calibration
Still fails after threshold raise	Default scanner to quarantine high-risk artifacts and needs_human_input ordinary uncertain artifacts
Classifier cannot produce stable confidence values	Disable classifier safe-pass; rule/schema scan only; all ambiguous artifacts → needs_human_input
Model profile changes	Calibration invalidated; rerun required


Storage

Add to classifier_validation_runs:

high_risk_threshold
ordinary_threshold
high_risk_precision_at_threshold
ordinary_precision_at_threshold
critical_misses_above_threshold
calibration_passed
calibration_adjustment_applied

Test binding

Bind to:

tests/test_classifier_validation_contract.py
tests/test_plan_injection_scanner_ordered_rules.py
tests/test_classifier_calibration_thresholds.py

This addresses the panel’s concern that 0.80 and 0.90 were being used as security gates without evidence that qwen3:4b confidence values were calibrated enough for that role. 


---

11. Confident embedded_instruction With No Rule Hit

Decision

A classifier label of embedded_instruction is sufficient to block, even when no rule-based pattern matched.

Scanner rule insertion

Add before safe-pass rules:

Rule	Condition	Decision

5A	Classifier label in embedded_instruction, tool_request, quarantine, or needs_cloud_review, regardless of rule hits	quarantined for high-risk artifacts; needs_human_input for ordinary artifacts


Behavior

Artifact	Classifier label	Decision

High-risk	embedded_instruction	quarantined
Ordinary	embedded_instruction	needs_human_input
Any	quarantine	quarantined
Any	needs_cloud_review	needs_human_input unless other rule quarantines


This closes the documented fallthrough gap where a confident classifier-only injection signal could bypass rule matching. 


---

12. Resource Limits Runtime Enforcement

Decision

resource_limits.py enforces hard caps through a pre-dispatch gate and post-dispatch ledger.

Runtime mechanism

ResourceEstimator → ResourceGate → Gateway Dispatch → ResourceLedger → OverrunHandler

Enforcement points

Resource	Pre-dispatch gate	Runtime/post-dispatch action

Cloud calls	Check max_model_calls, 2× token margin	Update provider_usage; block extra calls
Network fetches	Check manifest max_fetches	Increment counter; block overrun
Context bundle	Check serialized size ≤500 KB	Rebuild once; then block
Sandbox RAM	Check manifest cap ≤256 MB	Job Object terminates overrun
sqlite-vec	Check batch ≤100 vectors	Split batch or block
Chain duration	Check timeout/call count	Escalate to needs_human_input


Overrun status

Add or retain:

failed_resource_limit

Resource overrun is not ordinary failure. It means the system enforced a budget or safety boundary.

Ledger

Every resource-bearing operation writes to:

resource_usage
provider_usage
gateway_responses

as applicable.

This removes the “filename with no mechanism” problem noted in the synthesis. 


---

13. Provider Usage Orphan Recovery Broadening

Decision

Recover orphan provider_usage rows from all non-current sessions, not only the immediately previous session.

Startup query

SELECT *
FROM provider_usage
WHERE status = 'started'
AND session_id != current_session_id;

Recovery action

status = abandoned_session_crash
actuals_unavailable = true
charged_input_estimate = estimated_input_tokens
charged_output_estimate = estimated_output_tokens

Audit event

session_events.provider_usage_orphan_recovered

This closes the prior-evaluation touch-up requested in the v1.7 synthesis. 


---

14. Remaining Boot-Recovery Delegation to Kimi

Architectural boundary

The architecture requires startup recovery to preserve three invariants:

No task resumes with stale policy_approved = 1.
No child task is runnable without committed batch + task_permissions.
No provider call remains status = started from non-current sessions.

Delegated to Kimi

Kimi must specify implementation details for:

in-flight task reconciliation
stuck-task watchdog scan order
exact retry counter updates
operator-facing recovery summary formatting
migration script sequencing

Non-delegable limits

Kimi may not alter:

Scheduler-only task status mutation
TaskCommitter atomicity
PolicyEngine universal gate
operator_control Telegram-only creation path
sandbox/network separation

This acknowledges the remaining boot-recovery work without leaving architectural invariants open. The synthesis explicitly allows this as implementation-level work if the architecture states the boundary. 


---

15. Module Map Update

axiom/
  app/
    telegram_gateway.py
    operator_control_inserter.py
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
    plan_injection_scanner.py
    classifier_validation.py
    audit.py
    test_sets/
      injection_classifier_v1.jsonl

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
      operator_control_status.json
      operator_control_cancel_current_chain.json
      operator_control_pause_after_current.json
      operator_control_resume.json
      operator_control_shutdown_after_current.json
      operator_control_run_classifier_validation.json
      operator_control_enable_autonomous.json

PlanInjectionScanner is now explicitly placed at:

security/plan_injection_scanner.py


---

16. Revised PlanInjectionScanner Rule Set

Apply in order. First match wins.

Order	Condition	Decision

1	Scanner exception, timeout, or malformed scanner result	No verdict; parent → blocked, artifact → blocked
2	Critical injection rule hit	quarantined
3	Task artifact requests task_class in {operator_control, bootstrap_validation}	quarantined
4	Network + sandbox requested in same chain	quarantined
5	Rule hit + classifier label in embedded_instruction, tool_request, quarantine, needs_cloud_review	quarantined
5A	No rule hit + classifier label quarantine	quarantined
5B	No rule hit + classifier label embedded_instruction or tool_request + risk_class=high_risk	quarantined
5C	No rule hit + classifier label embedded_instruction or tool_request + risk_class=ordinary	needs_human_input
6	risk_class=high_risk + confidence < active_high_risk_threshold	quarantined
7	risk_class=ordinary + confidence < active_ordinary_threshold	needs_human_input
8	Required schema field missing but artifact is not hostile	failed
9	Unsupported capability request format	failed
10	risk_class=high_risk + valid schema + classifier safe/untrusted + confidence ≥ active_high_risk_threshold	passed
11	risk_class=ordinary + valid schema + classifier safe/untrusted + confidence ≥ active_ordinary_threshold	passed
12	Any unclassified remainder	needs_human_input


Default thresholds:

active_high_risk_threshold = 0.90
active_ordinary_threshold = 0.80

but calibration may raise them.


---

17. Revised Acceptance Tests

Test	Required assertion

test_artifact_risk_classification.py	Risk class is deterministic and stored on plan_artifacts
test_privileged_task_class_closed_set.py	Only {operator_control, bootstrap_validation} are privileged in Phase 1
test_model_gateway_provider_timeout.py	Timeout applies per provider call, not per cascade
test_scheduler_heartbeat_liveness_threshold.py	120s threshold and fail-closed action are enforced
test_operator_capability_restart_rebind.py	Restarted Telegram Gateway receives same capability object or fails closed
test_task_committer_atomic_batch.py	Child task commit is all-or-nothing
test_memory_gateway_verifier_context.py	Memory dedup/write response appears in verifier context
test_classifier_calibration_thresholds.py	0.80/0.90 thresholds pass calibration before use
test_resource_limits_runtime_enforcement.py	Gate blocks over-budget model/search/sandbox/vector operations
test_provider_usage_orphan_all_sessions.py	All non-current started rows are recovered
test_classifier_embedded_instruction_no_rule_hit.py	Classifier-only embedded instruction is blocked/escalated



---

18. Final v1.8 Architecture Position

AXIOM v1.8 preserves the architecture that has survived panel review:

Sequential runtime.
SQLite task queue.
Scheduler-owned state transitions.
PolicyEngine universal gate.
Manifest-scoped Tool Executor.
Telegram control plane.
Sandbox/network separation.
Local classifier for sanitizer lane only.
Cloud models for cognitive work.

v1.8 closes the remaining blockers:

Artifact risk class is deterministic.

Privileged task classes are a closed set.

Cloud calls have per-provider-call numeric bounds.

Scheduler heartbeat liveness has threshold and fail-closed action.

OperatorControlCapability survives Telegram restart or restart fails closed.

TaskCommitter child-task creation is atomic.

Memory Gateway responses are verified.

Classifier confidence thresholds require calibration.

PlanInjectionScanner has a module location.

Resource limits have runtime enforcement.

Remaining boot-recovery mechanics are delegated to Kimi under fixed invariants.