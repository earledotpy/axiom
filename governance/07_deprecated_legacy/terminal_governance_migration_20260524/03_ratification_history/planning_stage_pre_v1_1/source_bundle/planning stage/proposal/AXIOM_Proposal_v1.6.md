AXIOM Proposal v1.6 — Chief Architect Revision

Resolution of v1.5 Evaluator Review Items 1–8

0. Status

Field	Value

Proposal version	v1.6
Type	Targeted revision to v1.5
Scope	Resolves all v1.5 approval blockers
Architecture spine changed?	No
Implementation-ready?	Not until panel accepts v1.6
Recommended next review	Targeted coherence review on v1.6 changes only


Claude’s v1.5 review found that the spine remains valid but that Core Values 3 and 5 still have unresolved conflicts around bootstrap validation, operator-control spoofing, and thread failure behavior. This revision resolves those blockers directly. 


---

1. Resolution Matrix

#	v1.5 issue	v1.6 resolution

1	Bootstrap mode has no executor when Scheduler is stopped	Add dedicated BootstrapValidationWorker thread
2	OperatorControlInserter spoof protection relies on string identity	Enforce by thread identity + structural import boundary
3	Core Value 5 position on bootstrap validation unclear	Bootstrap validation is deterministic pre-agent infrastructure, not inter-agent coordination
4	PlanInjectionScanner verdict schema/rules ambiguous	Remove redundant passed; add ordered decision rules and exact transitions
5	Telegram-thread crash unhandled	Telegram failure triggers safe-stop of Scheduler and session shutdown path
6	In-flight cloud call lifecycle unclear	Keep synchronous model calls on Scheduler thread with timeout-bound cooperative cancellation
7	policy_approved lifecycle after recovery unclear	Clear policy approval on every recovered non-terminal task
8	/enable_autonomous and operator-control manifest source underspecified	Add command to bootstrap table; define static per-command operator manifests



---

2. Item 1 — Bootstrap Validation Executor

Decision

Bootstrap classifier validation is executed by a dedicated worker thread:

BootstrapValidationWorker

It is not executed inline on the Telegram thread, and it is not executed by the normal Scheduler thread.

Thread model in v1.6

Mode	Telegram thread	Scheduler thread	BootstrapValidationWorker

Autonomous mode	Running	Running	Not running
Bootstrap validation mode	Running	Not running	Starts only when /run_classifier_validation is invoked
Safe disabled mode	Running	Not running	Not running
Recovery autonomous mode	Running	Running after recovery	Not running


Bootstrap validation flow

First boot or missing classifier validation
↓
autonomous_operation = disabled
bootstrap_validation_mode = enabled
↓
Telegram Gateway starts
↓
Operator sends /run_classifier_validation
↓
Telegram Gateway creates bootstrap validation request
↓
BootstrapValidationWorker starts
↓
Worker runs classifier_validation.py against injection_classifier_v1.jsonl
↓
Worker writes classifier_validation_runs row
↓
Telegram remains responsive for /status
↓
If validation passes: /enable_autonomous becomes available
↓
If validation fails: bootstrap mode remains active

Why not use the Scheduler?

The normal Scheduler is the autonomous execution engine. In bootstrap mode, autonomous operation is intentionally disabled. Starting a limited Scheduler would create a second scheduler mode and blur Phase 1 control logic.

The worker is acceptable because it does one deterministic infrastructure check, not agent coordination, planning, tool execution, or queue advancement.

Bootstrap worker permissions

Capability	Allowed?

Load local classifier model	Yes
Read validation test set	Yes
Write classifier_validation_runs	Yes
Write session_events	Yes
Read/write task queue	No
Execute agents	No
Call cloud models	No
Use network	No
Use sandbox	No
Write semantic memory	No


Bootstrap allowed commands

Command	Allowed in bootstrap mode?	Effect

/status	Yes	Returns validation/bootstrap status
/run_classifier_validation	Yes	Starts worker if not already running
/enable_autonomous	Yes, only after validation passes	Enables autonomous mode for current session or instructs restart
/shutdown_after_current	Yes	Ends session safely
Goal submission	No	Rejected until autonomous enabled


Duplicate validation request behavior

If /run_classifier_validation is sent while the worker is already running:

Validation already running. Current progress: X / 120 samples.

No second worker starts.


---

3. Item 2 — OperatorControlInserter Spoof Protection

Decision

OperatorControlInserter is protected by thread identity and structural import boundary, not by a string field.

The previous created_by_component = "telegram_gateway" check is retained as audit metadata only. It is not the security boundary.

Enforcement mechanism

3.1 Thread identity assertion

OperatorControlInserter.insert() must assert:

threading.current_thread().name == "telegram_gateway_thread"

If false:

reject insert
write security_events.operator_control_invalid_thread
do not create task

3.2 Capability token generated at boot

At session startup, SessionController creates an in-memory object:

OperatorControlCapability

Only the Telegram Gateway receives a reference to this object.

OperatorControlInserter.insert() requires this object by identity, not by string value:

if capability is not session.operator_control_capability:
    reject

This token is never serialized, never stored in SQLite, and never exposed to model output.

3.3 Structural import boundary

Only this module may import OperatorControlInserter:

app/telegram_gateway.py

Forbidden imports:

core/*
agents/*
gateways/*
security/*

Add static test:

tests/test_operator_control_import_boundary.py

Pass condition:

No non-Telegram module imports app.operator_control_inserter.

Resulting enforcement stack

Layer	Mechanism

Structural	Only Telegram module may import inserter
Runtime	Thread identity assertion
Capability	In-memory object identity check
Manifest	Operator-control manifest still limits allowed actions
Policy	PolicyEngine verifies task_class and creator metadata
Audit	created_by_component retained for logs only


Spoof attempt behavior

If a compromised Task Planner attempts to produce:

{
  "task_class": "operator_control"
}

then:

TaskCommitter rejects artifact
security_events.operator_control_spoof_attempt written
parent planning task → blocked

If any non-Telegram code calls the inserter:

insert rejected
security_events.operator_control_invalid_invocation written
no task row created

This resolves the Core Value 3 conflict: operator-control creation is now architecturally restricted, not conventionally labeled. 


---

4. Item 3 — Core Value 5 Position on Bootstrap Validation

Decision

Bootstrap validation is not inter-agent coordination.

It is a deterministic pre-agent infrastructure check run before autonomous agents are allowed to operate.

Rationale

Core Value 5 governs coordination between agents through the task queue. Bootstrap classifier validation happens before:

Goal Planner
Task Planner
Tool Executor
Result Verifier
Scheduler autonomous loop

are active.

Therefore:

Bootstrap validation does not bypass the task queue,
because no agent task is being coordinated.

Boundary rule

BootstrapValidationWorker may write only:

classifier_validation_runs
session_events
bootstrap_status

It may not write:

tasks
task_permissions
plan_artifacts
verification_results
memory_items
memory_vectors
provider_usage

Audit rule

Even though bootstrap validation is not queue-mediated, it is still logged:

session_events.event_type = bootstrap_classifier_validation_started
session_events.event_type = bootstrap_classifier_validation_completed
session_events.event_type = bootstrap_classifier_validation_failed

This preserves auditability without pretending that infrastructure validation is agent work.


---

5. Item 4 — PlanInjectionScanner Verdict Semantics

Decision

Remove the redundant passed boolean.

Canonical pass signal:

decision == "passed"

No other field may represent pass/fail state.

Revised verdict schema

{
  "scan_id": "uuid",
  "plan_artifact_id": "uuid",
  "decision": "passed | failed | quarantined | needs_human_input",
  "confidence": 0.0,
  "high_risk_flag": false,
  "labels": [],
  "matched_rules": [],
  "classifier_label": "safe_data | untrusted_data | embedded_instruction | tool_request | memory_candidate | quarantine | needs_cloud_review",
  "reason": "string",
  "created_at": "timestamp"
}

Ordered decision rules

Apply these rules in order. First match wins.

Order	Condition	Decision	Parent/artifact transition

1	Scanner exception, timeout, or malformed scanner result	No verdict	Parent task → blocked; artifact → blocked
2	Critical injection rule hit	quarantined	Parent task → quarantined; artifact → quarantined
3	Privileged task-class request, including operator_control	quarantined	Parent task → quarantined; artifact → quarantined
4	Network + sandbox requested in same chain	quarantined	Parent task → quarantined; artifact → quarantined
5	Rule hit + classifier label in embedded_instruction, tool_request, quarantine, or needs_cloud_review	quarantined	Parent task → quarantined; artifact → quarantined
6	High-risk artifact and classifier confidence < 0.90	quarantined	Parent task → quarantined; artifact → quarantined
7	Ordinary artifact and classifier confidence < 0.80	needs_human_input	Parent task → needs_human_input; artifact → checkpoint_blocked
8	Required schema field missing but artifact is not hostile	failed	Retry if attempt_count < max_attempts; otherwise parent → failed
9	Unsupported capability request format	failed	Parent → blocked if schema-invalid; retry if semantically incomplete and attempts remain
10	No rule hits + valid schema + classifier safe with sufficient confidence	passed	Artifact → injection_scan_passed
11	Any unclassified remainder	needs_human_input	Parent task → needs_human_input


Exact transition branches for formerly vague rows

Missing required field

Condition	Transition

attempt_count < max_attempts and missing field can be regenerated	Parent → retry_pending
attempt_count >= max_attempts	Parent → failed
Missing field is structural and cannot be regenerated from artifact	Parent → blocked


Unsupported capability request

Condition	Transition

Capability string malformed or outside allowed vocabulary	Parent → blocked
Capability request valid type but underspecified	Parent → retry_pending if attempts remain
Attempts exhausted	Parent → failed


High-risk rule interaction

A non-critical rule hit marks the artifact high-risk. It does not automatically quarantine unless later ordered rules do so.

Example:

non-critical rule hit
+ classifier safe
+ confidence 0.94
= allowed to continue if no earlier rule matched

Example:

non-critical rule hit
+ classifier safe
+ confidence 0.85
= quarantined under high-risk confidence rule

This resolves the precedence ambiguity identified in the review. 


---

6. Item 5 — Telegram Thread Crash Handling

Decision

If the Telegram thread crashes, AXIOM must stop autonomous operation.

It may attempt one Telegram thread restart. If restart fails, Scheduler is halted.

Failure policy

Event	Behavior

Telegram thread exception	Write session_events.telegram_thread_exception
First Telegram crash	Attempt one restart
Restart succeeds	Continue session; send recovery notice
Restart fails	Set sessions.operator_interface_status = unavailable; request Scheduler safe-stop
Telegram crashes twice in one session	Scheduler halts after current safe boundary
Full process dies	Startup recovery handles on next launch


Why halt Scheduler?

If Telegram is down while Scheduler continues, the operator loses:

/status
/cancel_current_chain
/shutdown_after_current

That violates the operational safety model. AXIOM may not continue autonomous execution without its control interface.

Safe-stop sequence

Telegram thread crash detected
↓
SessionController attempts one Telegram restart
↓
If restart fails:
    sessions.operator_interface_status = unavailable
    sessions.shutdown_requested = true
↓
Scheduler observes shutdown_requested
↓
Scheduler completes current safe boundary
↓
Scheduler stops selecting new tasks
↓
session_events.autonomous_halted_operator_interface_down

/status after Telegram restart

If restart succeeds:

Telegram interface recovered after crash.
Scheduler status: running / paused / stopped.
Last scheduler heartbeat: <timestamp>.


---

7. Item 6 — In-Flight Cloud Call Lifecycle

Decision

Model Gateway calls are synchronous on the Scheduler thread.

Cancellation is cooperative and timeout-bound. There is no background completion handler in Phase 1.

Lifecycle

Scheduler invokes ModelGateway.call()
↓
ModelGateway writes provider_usage row: status = started
↓
HTTP call runs with configured timeout
↓
Operator may send /cancel_current_chain from Telegram thread
↓
Telegram marks cancel_requested = true
↓
ModelGateway continues until response, timeout, or transport error
↓
ModelGateway writes final provider_usage row/status
↓
Control returns to Scheduler
↓
Scheduler observes cancel_requested
↓
Scheduler transitions active task/chain to cancelled

Why this does not defeat cancellation

Cancellation is not immediate preemption. It is a guarantee that no further state-machine steps occur after the current bounded operation resolves.

The maximum delay is bounded by:

current operation timeout

Default cloud timeout:

Provider type	Timeout

Cerebras primary	30 seconds
Other cloud fallback	45 seconds
Hard maximum	90 seconds


Provider usage statuses

Outcome	provider_usage.status

Completed normally	completed
Timeout	timeout
Transport failure	transport_error
Completed after cancel requested	completed_after_cancel_requested
Timeout after cancel requested	timeout_after_cancel_requested
Transport error after cancel requested	transport_error_after_cancel_requested


Budget accounting

If provider returns actual usage:

record actual_input_tokens
record actual_output_tokens

If provider does not return actual usage:

charged_input_estimate = estimated_input_tokens
charged_output_estimate = estimated_output_tokens
actuals_unavailable = true

Operator feedback

When cancellation is requested during a cloud call:

Cancel queued. Current cloud call is already in flight and may consume quota. It will stop at the next scheduler boundary, maximum wait: N seconds.

This matches the cooperative cancellation model previously accepted while making the response-handling path explicit. 


---

8. Item 7 — policy_approved Lifecycle During Recovery

Decision

On startup recovery, clear policy_approved for every non-terminal recovered task.

No task retains policy approval across a crashed session unless it is already terminal.

Terminal statuses

Policy approval may remain for audit only if status is:

completed
failed
failed_resource_limit
cancelled
quarantined
blocked

Non-terminal statuses requiring approval clear

If status is:

created
running
retry_pending
awaiting_verification
verified
needs_human_input

then startup recovery must set:

policy_approved = 0,
policy_approved_at = NULL,
policy_decision_id = NULL

before the task can run again.

Recovery action table

Recovered state	Status after recovery	Policy approval

running, retry allowed	retry_pending	Cleared
running, gateway response exists and verifier needed	awaiting_verification	Cleared
running, cancel requested	cancelled	Retained for audit only
running, quarantine flag	quarantined	Retained for audit only
policy_approved=1, created	created	Cleared
verified with complete audit	completed	Retained for audit only
verified with missing audit	blocked	Retained for audit only


Rule

Fresh session, fresh policy gate:

Any non-terminal task must pass PolicyEngine again before running.

This prevents stale approvals from being reused under changed runtime conditions.


---

9. Item 8 — /enable_autonomous and Operator-Control Manifest Source

9.1 /enable_autonomous added to bootstrap command table

Command	Bootstrap mode	Requirement	Effect

/status	Allowed	None	Reports bootstrap status
/run_classifier_validation	Allowed	Worker not already running	Starts validation worker
/enable_autonomous	Allowed	Latest validation passed; sandbox/network gates valid	Starts Scheduler thread for current session or instructs restart
/shutdown_after_current	Allowed	None	Ends session safely


/enable_autonomous behavior

If validation passed and safety gates pass:

sessions.autonomous_operation_enabled = true
start Scheduler thread
write session_events.autonomous_enabled
Telegram: "Autonomous mode enabled."

If validation failed or missing:

Telegram: "Autonomous mode cannot be enabled. Classifier validation has not passed."

If sandbox validation failed:

Autonomous mode may start with sandbox.execute disabled.

9.2 Operator-control manifest source

Operator-control manifests are static per-command templates, not one generic manifest.

Manifest files:

policy/role_manifests/operator_control_status.json
policy/role_manifests/operator_control_cancel_current_chain.json
policy/role_manifests/operator_control_pause_after_current.json
policy/role_manifests/operator_control_resume.json
policy/role_manifests/operator_control_shutdown_after_current.json
policy/role_manifests/operator_control_run_classifier_validation.json
policy/role_manifests/operator_control_enable_autonomous.json

Why per-command manifests

A generic operator-control manifest would grant too much authority to every control command. Per-command manifests keep the permission surface narrow.

Example command permissions

Command	Allowed writes

/status	None; read-only
/cancel_current_chain	tasks.cancel_requested, operator_commands
/pause_after_current	sessions.pause_requested = true
/resume	sessions.pause_requested = false
/shutdown_after_current	sessions.shutdown_requested = true
/run_classifier_validation	bootstrap_status.validation_requested = true
/enable_autonomous	sessions.autonomous_operation_enabled = true, only if gates passed


Manifest binding rule

ManifestBinder may bind an operator-control manifest only when:

caller_thread = telegram_gateway_thread
AND capability_token identity is valid
AND command is in allowed command table
AND manifest template matches command_type


---

10. Revised Boot and Thread Model

Boot sequence

1. Start session script
2. Load .env and config
3. Validate Telegram token and whitelisted operator ID
4. Create in-memory OperatorControlCapability
5. Open SQLite connections:
   - Telegram connection
   - Scheduler connection, if Scheduler starts
   - Bootstrap worker connection, if worker starts
6. Apply PRAGMA settings to every connection:
   journal_mode=WAL
   synchronous=FULL
   busy_timeout=5000
7. Run schema migration checks
8. Determine startup mode:
   - autonomous
   - bootstrap_validation
   - safe_disabled
   - recovery_autonomous
   - recovery_disabled
9. Start Telegram Gateway thread
10. If autonomous/recovery_autonomous: start Scheduler thread
11. If bootstrap_validation: Scheduler thread remains stopped
12. Telegram sends mode summary

Thread failure policy

Failure	Behavior

Scheduler thread crash	Telegram remains available; operator sees crash status
Telegram thread crash once	Attempt one restart
Telegram restart fails	Scheduler safe-stops after current boundary
Bootstrap worker crash	Bootstrap mode remains active; validation marked failed
Full process crash	Startup recovery handles next launch



---

11. Revised Acceptance Tests

Test	Required assertion

test_bootstrap_validation_worker.py	Validation runs in worker thread; Telegram remains responsive
test_bootstrap_cv5_boundary.py	Bootstrap worker cannot read/write task queue and is classified as pre-agent infrastructure
test_operator_control_thread_identity.py	Inserter rejects calls outside Telegram thread
test_operator_control_capability_token.py	Inserter rejects missing/wrong in-memory capability object
test_operator_control_import_boundary.py	Only telegram_gateway.py imports inserter
test_plan_injection_scanner_ordered_rules.py	First-match rule ordering produces deterministic verdict
test_plan_injection_scanner_no_passed_bool.py	Scanner verdict has no redundant passed boolean
test_scanner_transition_branches.py	Retry/block/fail branches follow exact conditions
test_telegram_thread_crash_policy.py	Telegram crash causes restart attempt, then Scheduler safe-stop
test_model_gateway_synchronous_cancellation.py	In-flight calls write provider usage and cancellation waits for timeout boundary
test_recovery_clears_policy_approval.py	Non-terminal recovered tasks lose stale policy approval
test_enable_autonomous_command.py	Command works only after validation passes
test_operator_control_per_command_manifests.py	Each operator command binds only its own manifest



---

12. Final v1.6 Architecture Position

AXIOM v1.6 preserves the established architecture:

sequential runtime
SQLite task queue
Scheduler-owned state transitions
PolicyEngine approval gate
manifest-scoped tool execution
Telegram control plane
sandbox/network separation
local classifier in sanitizer lane
cloud models for cognition

v1.6 closes the remaining approval blockers:

Bootstrap validation has a dedicated worker thread.

Bootstrap validation is explicitly pre-agent infrastructure,
not inter-agent coordination.

Operator-control creation is protected by thread identity,
an in-memory capability object, and import-boundary tests.

PlanInjectionScanner has one canonical decision field and ordered rules.

Telegram thread failure stops autonomous operation if recovery fails.

Cloud calls are synchronous, timeout-bound, and fully accounted after cancellation.

Recovered non-terminal tasks must pass PolicyEngine again.

Operator-control manifests are static per-command templates.