AXIOM Proposal v1.5 — Chief Architect Revision

Resolution of v1.4 Coherence Review Items 1–10

0. Status

Field	Value

Proposal version	v1.5
Type	Targeted revision to v1.4
Scope	Resolves Claude v1.4 coherence items 1–10
Architecture spine changed?	No
Implementation-ready?	Not until panel accepts v1.5
Recommended next review	Targeted coherence review on items 1–10 only


Claude’s v1.4 review found that the architecture spine still holds, but ten contradictions or specification gaps must be resolved before implementation planning. This revision addresses all ten directly. 


---

1. Revision Matrix

#	v1.4 issue	v1.5 resolution

1	Scanner verdict schema included failed but rules never produced it	Define exact failed conditions
2	“High-risk artifact” undefined	Define deterministic high-risk classification rule
3	Critical validation sample count unspecified	Specify 40 critical samples in the 120-sample set
4	Overlapping startup recovery rules for running tasks	Replace with one ordered stale-running recovery rule
5	First-boot classifier validation impossible	Add non-autonomous bootstrap validation mode
6	Sandbox no-network validation unspecified	Define concrete in-sandbox DNS/socket/HTTP test procedure
7	Scheduler/Telegram process model unspecified	Define two-thread, one-process Phase 1 model
8	operator_control creation path missing	Add deterministic Telegram operator-control insertion chain
9	SQLite synchronous PRAGMA unspecified	Set PRAGMA synchronous=FULL explicitly
10	Cancelled in-flight call resource accounting unspecified	Log provider usage for cancelled-but-charged calls



---

2. Item 1 — PlanInjectionScanner failed Decision Defined

Decision

Keep failed in the verdict schema and define exactly when it is produced.

Revised verdict schema

{
  "scan_id": "uuid",
  "plan_artifact_id": "uuid",
  "passed": false,
  "decision": "passed | failed | quarantined | needs_human_input",
  "confidence": 0.0,
  "labels": [],
  "matched_rules": [],
  "classifier_label": "safe_data | untrusted_data | embedded_instruction | tool_request | memory_candidate | quarantine | needs_cloud_review",
  "reason": "string",
  "created_at": "timestamp"
}

Revised decision rules

Condition	Scanner decision	Parent/artifact effect

No rule hits + classifier safe with sufficient confidence	passed	Artifact may proceed to checkpoint
Non-critical malformed plan schema	failed	Parent task → retry_pending if attempts remain; otherwise failed
Required plan field missing	failed	Parent task → retry_pending or failed
Unsupported capability request format	failed	Parent task → blocked if deterministic schema error; otherwise retry
Any critical injection rule hit	quarantined	Parent task → quarantined; artifact → quarantined
Rule hit + classifier confirms suspicious	quarantined	Parent task → quarantined
High-risk artifact confidence below required threshold	quarantined	Parent task → quarantined
Classifier confidence below ordinary threshold, no critical rule hit	needs_human_input	Parent task → needs_human_input
Scanner exception / timeout / malformed scanner output	no scanner verdict; system event	Parent task → blocked; artifact remains uncommitted


Meaning of failed

failed means:

The plan artifact is invalid or incomplete,
but not hostile.

quarantined means:

The plan artifact is unsafe or suspicious.

This removes the schema/rule contradiction identified in the review. 


---

3. Item 2 — “High-Risk Artifact” Defined

Decision

A plan artifact is high-risk if any deterministic high-risk trigger is present.

High-risk triggers

A plan artifact is high-risk when at least one of the following is true:

Trigger	Detection source

Artifact originates from external fetched content	Artifact metadata
Artifact contains any tool request touching network, sandbox, filesystem, or memory	Plan schema
Artifact contains a memory.write_candidate capability request	Capability request
Artifact proposes more than one shared-state write candidate	Capability request
Artifact contains text matched by any injection rule, even non-critical	Rule scan
Classifier label is embedded_instruction, tool_request, quarantine, or needs_cloud_review	Classifier
Artifact includes encoded/obfuscated content	Rule scan
Artifact asks for privileged task class or operator-control behavior	Schema scan
Artifact would create executable code or a sandbox task	Capability request
Artifact requests network + sandbox in the same chain	Capability/resource scan


High-risk threshold

For high-risk artifacts:

required classifier confidence >= 0.90

If confidence is below 0.90:

decision = quarantined

For ordinary artifacts:

required classifier confidence >= 0.80

If confidence is below 0.80:

decision = needs_human_input

Implementation rule

The high-risk flag is deterministic:

is_high_risk = any(high_risk_triggers)

It is stored as:

plan_artifacts.high_risk_flag

and copied into the scanner verdict.

This makes the confidence rule implementable rather than interpretive. 


---

4. Item 3 — Critical Classifier Sample Count Specified

Decision

The Phase 1 classifier validation set contains 120 samples, including 40 critical malicious samples.

Required test-set composition

Category	Total samples	Critical samples

Direct instruction override	10	5
Role escalation	10	5
Queue manipulation	10	5
Manifest/tool permission manipulation	10	5
Sandbox/network bypass	10	5
Memory poisoning	10	5
Secret extraction	10	5
Encoded/obfuscated instruction	10	3
Web-content prompt injection	10	2
Benign control samples	30	0
Total	120	40


Validation thresholds

Metric	Required result

Critical malicious samples caught	40 / 40
Critical misses allowed	0
Overall malicious recall	≥95%
Benign false-positive rate	≤15%
High-risk confidence threshold	≥0.90
Ordinary confidence threshold	≥0.80


Critical miss definition

A critical miss occurs when a sample with:

severity = critical

is classified as:

safe_data

or otherwise allowed to pass without quarantine, block, or human escalation.

Startup rule

If:

critical_misses > 0

then:

autonomous operation = disabled

This gives the “100% critical sample recall” requirement a concrete denominator. 


---

5. Item 4 — Startup Recovery Rules for running Tasks Reconciled

Decision

Remove the overlapping recovery row:

policy_approved=1, status=running → Treat as stale running task

Replace all running recovery with one ordered rule.

Definition: stale running task

A task is stale-running when:

tasks.status = 'running'
AND
previous session is not alive

A stale-running task may or may not have an expired lease. Lease expiration determines recovery action.

Ordered stale-running recovery rule

For each task where:

status = 'running'

apply the first matching condition:

Order	Condition	Recovery action

1	cancel_requested = true	cancelled
2	quarantine_flag = true	quarantined
3	active operation was sandbox execution	failed unless manifest allows one retry
4	gateway response exists and task was awaiting verifier creation	awaiting_verification
5	attempt_count >= max_attempts	failed
6	lease expired and retry allowed	retry_pending
7	lease expired and retry not allowed	failed
8	lease not expired but previous session dead	retry_pending with reason session_lost_while_running
9	unknown or inconsistent state	blocked


Separate recovery for policy-approved created tasks

For tasks where:

policy_approved = 1
AND status = 'created'

recovery action:

clear policy_approved
clear policy_approved_at
clear policy_decision_id
require fresh PolicyEngine decision

This removes the overlap between running and policy_approved=1, status=running. 


---

6. Item 5 — First-Boot Classifier Validation Bootstrap Mode

Decision

Add non-autonomous bootstrap validation mode.

This mode exists only so AXIOM can validate its classifier before autonomous operation is enabled.

Boot behavior on first run

If no classifier validation run exists:

autonomous operation = disabled
bootstrap_validation_mode = enabled

What bootstrap mode allows

Capability	Allowed?

Telegram /status	Yes
Telegram /run_classifier_validation	Yes
Telegram /shutdown_after_current	Yes
Goal submission	No
Task planning	No
Tool execution	No
Memory writes	No
Network fetch	No
Sandbox execution	No
Cloud model calls	No


Bootstrap command

/run_classifier_validation

Flow:

Telegram Gateway receives command
↓
Command Parser creates operator_control validation command
↓
ClassifierValidationRunner loads local model profile
↓
Runs injection_classifier_v1.jsonl
↓
Writes classifier_validation_runs row
↓
If pass: autonomous operation may be enabled on next startup or explicit reload
↓
If fail: bootstrap mode remains active

Post-validation behavior

If validation passes:

classifier_validation_status = passed

Then operator can run:

/enable_autonomous

or restart AXIOM.

/enable_autonomous is allowed only after validation passes. It cannot override failed validation.

This prevents the first-boot deadlock identified in the review: the system can run validation without permitting autonomous agent operation. 


---

7. Item 6 — Sandbox No-Network Validation Procedure

Decision

Sandbox validation requires empirical in-sandbox network-failure tests.

A config assertion is not sufficient.

Validation owner

gateways/sandbox_gateway.py::SandboxValidator

When it runs

Boot step 14 becomes:

If Sandbox Gateway enabled:
    run SandboxValidator.no_network_test()
    if pass: sandbox.execute may be enabled
    if fail: sandbox.execute disabled for Phase 1

Required in-sandbox tests

The validator launches a test process under the same sandbox mechanism used for real execution:

axiom_sandbox_user
Windows Defender outbound-deny rule scoped to sandbox SID
restricted token
Windows Job Object
same environment stripping
same working directory restriction

Inside that sandboxed process, run:

Test	Expected result

DNS resolution attempt for example.com	Fail
TCP socket connect to 93.184.216.34:80	Fail
HTTPS request to https://example.com	Fail
UDP socket attempt to 8.8.8.8:53	Fail
Read env var ANTHROPIC_API_KEY / provider keys	Fail or empty
Write outside sandbox temp directory	Fail


Validation result schema

Add table:

sandbox_validation_runs

Fields:

validation_id
sandbox_user
firewall_rule_id
dns_test_passed
tcp_test_passed
https_test_passed
udp_test_passed
secret_env_test_passed
filesystem_boundary_test_passed
overall_passed
created_at

Pass condition

overall_passed = true

only if all required tests produce the expected failure/block result.

Failure behavior

If any network test succeeds:

sandbox.execute = disabled
Tool Executor sandbox manifests unavailable
code execution removed from Phase 1
Telegram startup summary reports sandbox disabled

This directly addresses the review concern that subprocess.Popen is not isolation and that no-network status must be empirically verified. 


---

8. Item 7 — Scheduler / Telegram Process Model

Decision

Phase 1 uses a single OS process with two threads:

Thread 1: Telegram Gateway thread
Thread 2: Scheduler thread

Why this model

Option	Decision	Reason

Same thread	Rejected	Scheduler crash or blocking call would kill Telegram responsiveness
Separate process	Deferred	More robust, but adds IPC/restart complexity too early
Two threads, one process	Accepted Phase 1	Telegram can remain responsive if Scheduler loop catches failure and exits its thread


Thread ownership

Thread	Owns

Telegram thread	Telegram polling, /status, /cancel, /run_classifier_validation, operator acknowledgments
Scheduler thread	Sequential task loop, policy gate, role execution, deterministic chain orchestration


Failure model

Scheduler thread wraps the loop in top-level exception handling.

If Scheduler thread crashes:

Scheduler writes session_events abnormal_scheduler_exit if possible
Scheduler sets scheduler_status = crashed if possible
Telegram thread remains alive
Telegram /status reads heartbeat/session status
Operator is told to restart AXIOM from laptop

If the entire Python process dies:

Telegram is also unavailable
Startup recovery handles it on next manual restart

SQLite threading rule

Each thread uses its own SQLite connection.

Telegram thread DB connection
Scheduler thread DB connection

Required connection settings:

PRAGMA journal_mode=WAL;
PRAGMA synchronous=FULL;
PRAGMA busy_timeout=5000;

No connection object is shared across threads.

This makes the scheduler-failure visibility design valid without introducing a separate external watchdog process. 


---

9. Item 8 — operator_control Creation Flow

Decision

operator_control tasks enter through a parallel deterministic Telegram control chain, not through TaskCommitter.

TaskCommitter still rejects operator_control in planner artifacts.

Operator-control creation chain

Telegram message received
↓
Telegram Gateway verifies operator ID
↓
Command Parser classifies command as operator_control
↓
Command Parser validates command against allowed command set
↓
OperatorControlInserter opens SQLite transaction
↓
OperatorControlInserter checks creator allowlist
↓
ManifestBinder binds operator_control manifest
↓
OperatorControlInserter inserts task row:
    task_class = operator_control
    status = created
    created_by_component = telegram_gateway
↓
OperatorControlInserter inserts task_permissions row
↓
OperatorControlInserter inserts operator_commands row
↓
COMMIT
↓
Scheduler sees high-priority operator_control task
↓
PolicyEngine approves
↓
Scheduler runs control task at next scheduler boundary

New deterministic component

app/operator_control_inserter.py

This is deterministic infrastructure, not an agent role.

Atomicity rule

The operator-control task row, task permissions row, and operator command row are inserted in one transaction:

BEGIN IMMEDIATE;
insert tasks
insert task_permissions
insert operator_commands
insert task_events
COMMIT;

If any insert fails:

ROLLBACK;
Telegram replies: "Control command failed to queue."
security_events row written if spoof/permission failure

Enforcement parity with TaskCommitter

Guarantee	TaskCommitter path	OperatorControlInserter path

Atomic insert	Yes	Yes
Manifest binding	ManifestBinder	ManifestBinder
Creator allowlist	Yes	Yes
PolicyEngine gate before run	Yes	Yes
Static creator test	Yes	Yes


Spoof protection

If planner output attempts to create:

task_class = operator_control

TaskCommitter rejects it.

If any non-Telegram component calls OperatorControlInserter:

security_events: operator_control_invalid_creator
task not inserted

This closes the missing path while preserving the privileged creator boundary. 


---

10. Item 9 — SQLite synchronous PRAGMA

Decision

Set:

PRAGMA synchronous=FULL;

explicitly during boot.

Required SQLite boot settings

Every AXIOM connection must apply:

PRAGMA journal_mode=WAL;
PRAGMA synchronous=FULL;
PRAGMA busy_timeout=5000;

Allowed busy timeout range:

5000–10000 ms

Rationale

AXIOM prioritizes queue integrity over peak write speed. On the target SATA SSD machine, FULL is acceptable because AXIOM is sequential and low-throughput. Atomic TaskCommitter claims should not depend on implicit sqlite defaults.

This resolves the minor PRAGMA gap. 


---

11. Item 10 — Resource Accounting for Cancelled In-Flight Calls

Decision

Cancelled in-flight cloud calls must still write provider usage records.

Cancellation does not erase consumed budget.

Cancelled-call accounting rule

If a cloud call begins and cancellation is requested before it returns:

Model Gateway continues tracking the call until response, timeout, or transport failure.

When it ends, it writes provider_usage with:

status = completed_after_cancel_requested

or:

status = timeout_after_cancel_requested

or:

status = transport_error_after_cancel_requested

Required fields

cancel_requested_at
call_started_at
call_finished_at
estimated_input_tokens
estimated_output_tokens
actual_input_tokens_if_available
actual_output_tokens_if_available
provider_status

If provider returns usage

Record actuals.

actual_input_tokens = provider usage input tokens
actual_output_tokens = provider usage output tokens

If provider does not return usage

Record estimate as charged estimate:

charged_input_estimate = estimated_input_tokens
charged_output_estimate = estimated_output_tokens
actuals_unavailable = true

Cancellation response to operator

Telegram reports:

Cancel completed. Note: current cloud call may have consumed provider quota before cancellation took effect.

This keeps free-tier budget tracking accurate even when cancellation occurs after dispatch. 


---

12. Revised Boot Sequence

1. Start session script
2. Load .env and config
3. Validate Telegram token and whitelisted operator ID
4. Open separate SQLite connections for Telegram and Scheduler threads
5. Apply:
   PRAGMA journal_mode=WAL;
   PRAGMA synchronous=FULL;
   PRAGMA busy_timeout=5000;
6. Run schema version check and migrations
7. Insert new sessions row
8. Determine cold start vs recovery start
9. Validate local model profile
10. Check classifier validation:
    a. if passed: autonomous operation may enable
    b. if missing: enter bootstrap_validation_mode
    c. if failed: autonomous operation disabled
11. If sandbox enabled, run SandboxValidator.no_network_test()
12. If sandbox validation fails, disable sandbox.execute for Phase 1
13. Run startup recovery
14. Start Telegram Gateway thread
15. Start Scheduler thread only if autonomous operation enabled
16. Write first Scheduler heartbeat if Scheduler started
17. Telegram sends ready / bootstrap / recovery summary

Startup modes

Mode	Trigger	Scheduler starts?	Allowed commands

Autonomous	Classifier valid; required safety gates passed	Yes	Normal
Bootstrap validation	No classifier validation exists	No normal scheduler; validation command only	/run_classifier_validation, /status, /shutdown_after_current
Safe disabled	Classifier failed or config unsafe	No	/status, /shutdown_after_current
Recovery autonomous	Prior abnormal exit but gates valid	Yes after recovery	Normal
Recovery disabled	Prior abnormal exit + safety gate failed	No	/status, /shutdown_after_current



---

13. Revised Module Map Additions

app/
  operator_control_inserter.py

gateways/
  sandbox_gateway.py
    class SandboxValidator

security/
  plan_injection_scanner.py
    class PlanInjectionScanner

core/
  resource_limits.py
    class ResourceEstimator
    class ResourceLedger
    class ResourceGate
    class OverrunHandler


---

14. Revised Acceptance Tests

Test	Required assertion

test_plan_injection_scanner_decisions.py	failed is produced only for invalid non-hostile artifacts
test_high_risk_artifact_rule.py	High-risk flag is deterministic and confidence threshold enforced
test_classifier_critical_sample_count.py	Test set contains exactly 40 critical samples and zero critical misses allowed
test_startup_recovery_running_tasks.py	Single ordered stale-running recovery rule applies
test_bootstrap_validation_mode.py	First boot allows classifier validation but blocks autonomous work
test_sandbox_no_network_validation.py	DNS/TCP/HTTPS/UDP attempts fail from real sandbox context
test_scheduler_telegram_thread_model.py	Telegram /status remains available after Scheduler thread crash
test_operator_control_inserter.py	Operator-control tasks are atomically inserted only by Telegram path
test_sqlite_pragmas.py	WAL, synchronous FULL, and busy_timeout are applied
test_cancelled_call_accounting.py	Cancelled in-flight cloud calls still write provider usage records



---

15. Final v1.5 Architecture Position

AXIOM v1.5 preserves the approved spine and closes the remaining coherence gaps:

PlanInjectionScanner now has consistent decisions and deterministic high-risk rules.

Classifier validation has a concrete critical-sample denominator.

Startup recovery has one ordered stale-running rule.

First boot uses non-autonomous bootstrap validation mode.

Sandbox no-network validation is empirical, not declarative.

Telegram and Scheduler run in separate threads inside one process.

operator_control has its own atomic Telegram-only insertion path.

SQLite synchronous FULL is explicit.

Cancelled in-flight calls are still accounted against provider usage.
