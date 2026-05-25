AXIOM Proposal v1.7 — Chief Architect Revision

Resolution of v1.6 Evaluation Items 1–4

0. Status

Field	Value

Proposal version	v1.7
Type	Targeted revision to v1.6
Scope	Resolves the one blocking contradiction and three remaining specification gaps
Architecture spine changed?	No
Recommended next review	Targeted coherence confirmation, then next panel stage


The v1.6 review found that Core Values 3 and 5 are now satisfied, but one contradiction remains in the PlanInjectionScanner ordered rules, plus three implementation-facing specifications: SessionController thread locus, provider_usage row semantics, and operator-control thread identity strength.  


---

1. Resolution Matrix

#	v1.6 issue	v1.7 resolution

1	Scanner rules contradict worked examples	Add explicit high-risk safe-pass rule before fallback
2	SessionController has no thread locus	Place SessionController on the main supervisor thread
3	provider_usage row semantics unclear	Use one row per provider call, inserted as started, updated to final status
4	Thread-name check is weak	Replace thread-name check with thread object identity



---

2. Item 1 — PlanInjectionScanner Ordered Rules Corrected

Decision

Adopt the evaluator’s recommended option 2:

Insert a rule:
High-risk artifact + classifier safe label + confidence ≥ 0.90 → passed.

The worked examples remain valid. The rules now produce the same result as the prose.

Canonical verdict field

Still retained from v1.6:

{
  "decision": "passed | failed | quarantined | needs_human_input"
}

No separate passed: true/false field exists.

Revised ordered decision rules

Apply in order. First match wins.

Order	Condition	Decision	Parent/artifact transition

1	Scanner exception, timeout, or malformed scanner result	No verdict	Parent task → blocked; artifact → blocked
2	Critical injection rule hit	quarantined	Parent task → quarantined; artifact → quarantined
3	Privileged task-class request, including operator_control	quarantined	Parent task → quarantined; artifact → quarantined
4	Network + sandbox requested in same chain	quarantined	Parent task → quarantined; artifact → quarantined
5	Rule hit + classifier label in embedded_instruction, tool_request, quarantine, or needs_cloud_review	quarantined	Parent task → quarantined; artifact → quarantined
6	High-risk artifact + classifier confidence < 0.90	quarantined	Parent task → quarantined; artifact → quarantined
7	Ordinary artifact + classifier confidence < 0.80	needs_human_input	Parent task → needs_human_input; artifact → checkpoint_blocked
8	Required schema field missing but artifact is not hostile	failed	Retry/block/fail by branch rules below
9	Unsupported capability request format	failed	Retry/block/fail by branch rules below
10	High-risk artifact + valid schema + classifier label safe_data or untrusted_data + confidence ≥ 0.90	passed	Artifact → injection_scan_passed
11	Ordinary artifact + valid schema + classifier label safe_data or untrusted_data + confidence ≥ 0.80	passed	Artifact → injection_scan_passed
12	Any unclassified remainder	needs_human_input	Parent task → needs_human_input; artifact → checkpoint_blocked


Worked examples now align

Artifact case	Rule hit	Decision

Non-critical rule hit + classifier safe_data + confidence 0.94	Rule 10	passed
Non-critical rule hit + classifier safe_data + confidence 0.85	Rule 6	quarantined
No rule hit + classifier safe_data + confidence 0.83	Rule 11	passed
No rule hit + classifier confidence 0.76	Rule 7	needs_human_input
Critical injection rule hit + classifier says safe	Rule 2	quarantined
Operator-control task request in plan artifact	Rule 3	quarantined


Branch rules for failed

Missing required field

Condition	Transition

Missing field can be regenerated and attempt_count < max_attempts	Parent → retry_pending
Missing field can be regenerated but attempts exhausted	Parent → failed
Missing field is structural and cannot be regenerated from artifact context	Parent → blocked


Unsupported capability request

Condition	Transition

Capability string malformed or outside allowed vocabulary	Parent → blocked
Capability type valid but underspecified and attempt_count < max_attempts	Parent → retry_pending
Capability type valid but underspecified and attempts exhausted	Parent → failed


This removes the implementer-choice ambiguity identified in the v1.6 review. 


---

3. Item 2 — SessionController Thread Locus

Decision

SessionController runs on the main supervisor thread.

It is not the Telegram thread.
It is not the Scheduler thread.
It is not the BootstrapValidationWorker thread.

Thread model

Thread	Owner	Responsibilities

Main supervisor thread	SessionController	Boot, shutdown, thread lifecycle, crash observation, Telegram restart, Scheduler safe-stop request
Telegram thread	TelegramGateway	Operator commands, /status, /cancel, /run_classifier_validation, acknowledgments
Scheduler thread	Scheduler	Sequential autonomous loop, policy gate, role execution, deterministic chain
Bootstrap worker thread	BootstrapValidationWorker	Classifier validation only, bootstrap mode only


Supervisor loop

The main thread runs:

SessionController.supervise()

It monitors:

telegram_thread.is_alive()
scheduler_thread.is_alive()
bootstrap_worker.is_alive()
scheduler_heartbeat.last_tick_at
sessions.shutdown_requested
sessions.operator_interface_status

Telegram crash handling

Telegram thread crashes
↓
Main supervisor thread observes telegram_thread.is_alive() == false
↓
SessionController writes session_events.telegram_thread_exception
↓
SessionController attempts one Telegram thread restart
↓
If restart succeeds:
    continue session
↓
If restart fails:
    sessions.operator_interface_status = unavailable
    sessions.shutdown_requested = true
    Scheduler safe-stops at next boundary

Why this works while Scheduler is blocked

If the Scheduler thread is waiting on a synchronous cloud call for up to 90 seconds, the main supervisor thread still runs. It can observe the Telegram crash and set the shutdown request. The Scheduler will honor it when the current bounded operation returns or times out.

Supervisor failure policy

If the main supervisor thread fails, the process is considered failed. There is no Phase 1 recovery inside the same process. Recovery happens on manual restart through startup recovery.


---

4. Item 3 — provider_usage Row Semantics

Decision

Use one row per provider call.

The row is inserted at call start and updated to final status.

Provider call lifecycle

ModelGateway prepares call
↓
INSERT provider_usage row:
    provider_call_id = uuid
    status = started
↓
HTTP call executes with timeout
↓
On response / timeout / error:
    UPDATE same provider_usage row to final status

Required provider_usage fields

provider_call_id
provider
model
task_id
chain_id
session_id
status
estimated_input_tokens
estimated_output_tokens
actual_input_tokens
actual_output_tokens
charged_input_estimate
charged_output_estimate
actuals_unavailable
cancel_requested_at
call_started_at
call_finished_at
timeout_seconds
error_type
last_update_at

Status values

started
completed
timeout
transport_error
completed_after_cancel_requested
timeout_after_cancel_requested
transport_error_after_cancel_requested
abandoned_session_crash

Cancellation during in-flight call

If cancellation is requested while the call is already in flight:

cancel_requested_at is set
call continues until response, timeout, or transport error
same provider_usage row is updated to *_after_cancel_requested

Orphan started row recovery

On startup recovery, any row where:

status = 'started'
AND session_id = previous_session_id

is treated as an orphaned provider call.

Recovery action:

UPDATE provider_usage
SET
  status = 'abandoned_session_crash',
  actuals_unavailable = true,
  charged_input_estimate = estimated_input_tokens,
  charged_output_estimate = estimated_output_tokens,
  last_update_at = startup_time
WHERE status = 'started'
AND session_id = previous_session_id;

Why estimates are charged on orphan recovery

If the process crashed after dispatch, AXIOM may not know whether the provider completed and consumed quota. The conservative budget rule is:

unknown dispatched call = count estimated usage against budget

This prevents free-tier accounting drift.

Audit event

Startup recovery also writes:

session_events.provider_usage_orphan_recovered

with:

provider_call_id
task_id
previous_status = started
new_status = abandoned_session_crash
reason = previous_session_ended_before_provider_finalization


---

5. Item 4 — Operator-Control Thread Identity Check Refined

Decision

Replace thread-name comparison with thread object identity.

The thread-name check is removed as a security boundary.

Correct check

SessionController stores the actual Telegram thread object:

session.telegram_thread = telegram_thread

OperatorControlInserter.insert() checks:

if threading.current_thread() is not session.telegram_thread:
    reject_insert()

This is object identity, not string equality.

Enforcement stack, strength order

Layer	Mechanism	Role

1	In-memory OperatorControlCapability object identity	Primary runtime security boundary
2	Telegram thread object identity	Secondary runtime boundary
3	Static import-boundary test	Structural boundary
4	Per-command operator-control manifests	Capability minimization
5	created_by_component metadata	Audit only, not security


Capability token rule

OperatorControlCapability is:

created by SessionController at boot
held only by TelegramGateway
passed by object reference into OperatorControlInserter
never serialized
never written to SQLite
never exposed to model output

Import-boundary rule

Only:

app/telegram_gateway.py

may import:

app/operator_control_inserter.py

Forbidden:

core/*
agents/*
gateways/*
security/*

Rejected spoof cases

Attempt	Result

Non-Telegram code passes created_by_component='telegram_gateway'	Rejected; string is audit-only
Non-Telegram thread calls inserter	Rejected by thread object identity
Non-Telegram code obtains no capability token	Rejected by capability identity
Planner artifact requests operator_control	Rejected by TaskCommitter
Module imports inserter outside Telegram path	Static test failure


This corrects the overstatement in v1.6: the security boundary is capability-object identity plus thread-object identity, not thread-name convention. 


---

6. Revised Thread Model Summary

Main supervisor thread
  └── SessionController
        ├── starts Telegram thread
        ├── starts Scheduler thread when autonomous mode enabled
        ├── starts BootstrapValidationWorker only on bootstrap command
        ├── observes thread liveness
        ├── restarts Telegram once
        └── requests Scheduler safe-stop if operator interface fails

Telegram thread
  └── TelegramGateway
        ├── receives operator commands
        ├── owns OperatorControlCapability
        └── may call OperatorControlInserter

Scheduler thread
  └── Scheduler
        ├── owns sequential autonomous task loop
        ├── makes synchronous ModelGateway calls
        └── observes cancel/shutdown flags at boundaries

BootstrapValidationWorker thread
  └── classifier validation only


---

7. Revised Acceptance Tests

Test	Required assertion

test_plan_injection_scanner_ordered_rules.py	Non-critical rule hit + safe classifier + confidence ≥0.90 returns passed
test_plan_injection_scanner_fallthrough.py	No artifact falls through ambiguously; Rule 12 handles remainders
test_session_controller_supervisor_thread.py	SessionController runs on main supervisor thread and observes Telegram death
test_telegram_restart_by_supervisor.py	Supervisor restarts Telegram once, then requests Scheduler safe-stop
test_provider_usage_single_row_lifecycle.py	Provider call creates one row and updates it to final status
test_provider_usage_orphan_recovery.py	Startup recovery marks orphan started rows as abandoned_session_crash
test_operator_control_thread_object_identity.py	Inserter rejects same-name thread that is not session.telegram_thread
test_operator_control_capability_primary_boundary.py	Inserter rejects missing or wrong capability object
test_operator_control_created_by_metadata_not_boundary.py	Correct created_by_component string alone cannot authorize insert



---

8. Final v1.7 Architecture Position

AXIOM v1.7 makes the final four targeted corrections:

PlanInjectionScanner rules and examples now agree.

SessionController runs on the main supervisor thread.

provider_usage uses one row per provider call:
insert at start, update at completion, recover orphan started rows conservatively.

Operator-control authorization uses object identity,
not thread-name convention or component-name strings.