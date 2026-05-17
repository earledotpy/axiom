AXIOM Proposal v1.10 — Chief Architect Revision

Resolution of v1.9 Panel Synthesis Items 1–12

0. Status

Field	Value

Proposal version	v1.10
Type	Targeted revision to v1.9
Scope	Resolves blocking revisions, significant specifications, clarifications, and carry-forward items from v1.9 synthesis
Architecture spine changed?	No
Recommended next review	Delta-confirmation by Evaluator and Critic only


The v1.9 synthesis found the architecture spine intact but returned the proposal for twelve targeted fixes: four blocking revisions, two significant specifications, two clarifications, and four carry-forward implementation-readiness clarifications. 


---

1. Resolution Matrix

#	Required v1.10 item	v1.10 resolution

1	Reassign calibration test-set authorship	Gemini authors; DeepSeek adversarially reviews
2	Add mid-session model fingerprint verification	Pre-decision fingerprint check before every classifier safe-pass
3	Add manifest integrity verification	SHA256 fingerprints verified at boot; fail-closed on mismatch
4	Add end-to-end acceptance test	test_full_goal_flow_minimum.py
5	Add reconciliation sanity check	±50% discrepancy threshold with operator confirmation
6	Add tiered token-margin rule	2× calibrated tokenizer, 1.5× fallback ÷3 estimator
7	Reframe keepalive honestly	Retrospective diagnostic, not real-time monitoring
8	Add immediate goal acknowledgement	Telegram replies with planning-latency expectation
9	Reconcile §12.3 and §14 test lists	§14 = full MVP acceptance suite; §12.3 = subset category
10	Locate supervisor stale-check logic	app/session_controller.py::SupervisorMonitor
11	Add task-planner manifest-sizing rule	Planner must budget prompt at ≤50% of manifest cap with calibrated tokenizer, ≤66% with fallback estimator
12	Specify operator-control authorization ownership	Seven-step ownership table added



---

2. Binding Conditions Carried Forward

These remain binding and are not reopened in v1.10:

strict sequential execution
4-thread cap
qwen3:4b Q4 quantized + memory-mapped via Ollama
500 KB serialized context bundle cap
sandbox 256 MB RAM + 60s wall-clock cap
sqlite-vec 100-vector query/batch cap
Brave Search API or panel-approved free-tier alternative before web search
2× token margin when calibrated tokenizer is used
safe-pass disabled until calibration passes
fingerprint mismatch disables safe-pass
stateless PolicyEngine
Scheduler-owned state mutation

The Arbiter factually cleared v1.9 mechanisms, and Constraints approved with twelve binding conditions. The v1.10 changes do not add new threads, background daemons, paid services, or RAM-heavy components. 


---

3. Item 1 — Calibration Test-Set Authorship Reassigned

Decision

Do not assign primary authorship of the injection test set to DeepSeek.

DeepSeek’s role is adversarial critique, not origination of design artifacts. The synthesis correctly identifies that authoring the classifier test set defines the security envelope of the scanner and therefore creates a conflict if assigned to the Critic. 

Revised ownership matrix

Responsibility	Owner

Primary author	Gemini 3.1 Pro — Research and Knowledge Arbiter
Adversarial review	DeepSeek V4 — Adversarial Critic
Coherence / final acceptance review	Claude Opus 4.7 — Quality and Coherence Evaluator
Feasibility review	Qwen 3.6 Plus — Constraints Reviewer
Implementation packaging	Kimi K2.6 — Implementation Specialist
Physical file creation	Human operator


Artifact

security/test_sets/injection_classifier_v1.jsonl

Governance rule

Gemini creates the test set.
DeepSeek attacks the test set.
Claude checks coherence.
Qwen checks feasibility.
Kimi packages it.
Operator writes the approved file to disk.

Interim default

Until this test set exists and calibration passes:

classifier safe-pass = disabled

PlanInjectionScanner may still use deterministic rules and schema checks, but any classifier-dependent safe-pass is unavailable.


---

4. Item 2 — Mid-Session Model Fingerprint Verification

Decision

Use pre-decision fingerprint verification before every classifier-dependent safe-pass.

This is stricter than periodic checking and avoids a window where a changed model can continue authorizing safe-pass decisions until the next interval.

Verification point

Before PlanInjectionScanner applies any rule that would produce:

decision = passed

based on classifier confidence, it calls:

ModelFingerprintGuard.verify_current_profile()

Required comparison

The guard compares current local model fingerprint against the fingerprint attached to the latest passing calibration:

model_name
ollama_model_tag
ollama_model_digest
quantization
thinking_mode
ollama_show_json_hash
model_file_mtime
model_file_size
calibration_id

On match

Safe-pass may proceed if all scanner conditions and calibration thresholds are satisfied.

On mismatch

safe-pass disabled immediately
security_events.model_fingerprint_mismatch written
session_events.safe_pass_disabled_mid_session written
current artifact → needs_human_input or quarantined according to risk_class

Mismatch behavior by risk class

Artifact risk	Behavior

high_risk	quarantined
ordinary	needs_human_input


Why pre-decision instead of periodic

Periodic checking is cheaper but leaves a window of exposure. Pre-decision checking ties the model-profile guarantee directly to the security action being taken. This better satisfies the security-boundary concern raised in the synthesis. 


---

5. Item 3 — Manifest Integrity Verification

Decision

All manifest files are security artifacts and must be fingerprinted.

Table

Add:

manifest_fingerprints

Fields:

manifest_id
relative_path
sha256
manifest_type = role | operator_control
version
created_at
approved_by_panel_version

Covered paths

policy/role_manifests/*.json
policy/operator_control_manifests/*.json

Boot verification

At startup:

ManifestIntegrityVerifier scans manifest files
computes SHA256
compares to manifest_fingerprints table

On mismatch

Fail closed:

autonomous_operation_enabled = false
operator_control task creation disabled except /status and /shutdown_after_current
security_events.manifest_integrity_mismatch written
Telegram reports manifest mismatch and startup enters safe_disabled mode

On missing fingerprint

Treat as mismatch unless boot is in approved deployment-registration mode.

Registration mode

Manifest fingerprints may be registered only during approved implementation/deployment:

manifest_registration_mode = true

This mode is not available during autonomous operation.

Module ownership

Responsibility	Component

SHA256 compute	security/audit.py::ManifestIntegrityVerifier
Manifest binding refusal on mismatch	core/manifest_binder.py
Startup fail-closed	app/session_controller.py


This mirrors the existing model-fingerprint security pattern and closes the runtime manifest-integrity gap. 


---

6. Item 4 — End-to-End Acceptance Test

Decision

Add one required MVP end-to-end acceptance test:

tests/e2e/test_full_goal_flow_minimum.py

Test goal

Use a trivial, no-network, no-sandbox goal:

Summarize the AXIOM Core Values from memory.

Why this goal

It exercises the architecture without invoking web search or sandbox execution:

Telegram input
Goal Planner
PlanInjectionScanner
Result Verifier checkpoint
TaskCommitter
Task Planner if needed
Tool Executor with memory query only
Memory Gateway
Result Verifier tool_result mode
Scheduler completion
Telegram final response

Required boundary assertions

The test must assert:

Boundary	Assertion

Telegram Gateway	Goal accepted and acknowledged
Ingress Sanitizer	Goal task inserted only after sanitization
PolicyEngine	Goal task receives policy decision before running
Goal Planner	Proposed plan artifact created
PlanInjectionScanner	Artifact scan completed and passed
Result Verifier checkpoint	Checkpoint verdict exists
TaskCommitter	Child tasks inserted atomically with manifests
ManifestBinder	Every executable task has task_permissions row
Scheduler	Only one task is running at a time
Context Builder	Context bundle ≤500 KB
Tool Executor	Memory query task executes under manifest
Memory Gateway	Gateway response is recorded
Result Verifier	Tool result verified before completion
Telegram Gateway	Final answer returned to operator


Success criterion

The e2e test passes only if:

final Telegram response contains a coherent summary
AND all required boundary records exist
AND no direct role-to-role call occurs
AND no task bypasses PolicyEngine
AND no task runs without a manifest

This satisfies Core Value 4’s “prove the concept” requirement before declaring MVP complete. 


---

7. Item 5 — Provider-Usage Reconciliation Sanity Check

Decision

Manual reconciliation uses a discrepancy threshold.

Threshold

reconciliation_discrepancy_threshold = 50%

Calculation

discrepancy = abs(operator_reported_total - axiom_estimated_total) / max(axiom_estimated_total, 1)

Behavior

Discrepancy	Behavior

≤50%	Apply reconciliation
>50%	Flag discrepancy and request operator confirmation
Operator confirms	Apply reconciliation with confirmed_large_adjustment = true
Operator rejects	Do not apply; keep conservative estimate
Operator provides corrected values	Recalculate discrepancy


Telegram prompt

Reported provider usage differs from AXIOM's estimate by >50%.
Apply this reconciliation anyway? Reply CONFIRM or CANCEL.

Storage addition

Add to provider_usage_reconciliations:

discrepancy_percent
confirmed_large_adjustment
operator_confirmation_timestamp

This prevents accidental copy/paste errors from silently corrupting the budget ledger. 


---

8. Item 6 — Tiered Token-Margin Rule

Decision

Use a tiered margin based on tokenizer quality.

Token-margin table

Tokenizer mode	Estimation method	Safety margin

Calibrated provider/model tokenizer	Official tokenizer or verified compatible tokenizer	2.0×
OpenAI-compatible calibrated tokenizer	tiktoken-style tokenizer verified for endpoint family	2.0×
Conservative fallback estimator	ceil(character_count / 3)	1.5×


Dispatch rule

dispatch_estimated_tokens * margin <= manifest.budget_policy.max_estimated_input_tokens

Why fallback margin is lower

The /3 character estimator is already conservative. Applying 2× on top produces excessive false blocks. 1.5× preserves caution while improving usability for legitimate large-context tasks.

If tokenizer mode is unknown

Treat as fallback:

ceil(character_count / 3)
margin = 1.5

If high-risk task uses fallback estimator

For high-risk tasks, fallback is allowed only if:

dispatch_estimate * 1.5 <= manifest cap
AND context bundle ≤500 KB
AND task does not request sandbox.execute

If the task requests sandbox execution and no calibrated tokenizer is available:

task → needs_human_input

This balances the Critic’s excessive-blocking concern with AXIOM’s security posture. 


---

9. Item 7 — Keepalive Reframed Honestly

Decision

The keepalive rule is not real-time monitoring.

It is a retrospective diagnostic for the operator.

Replacement wording

During whole-system hangs, Windows hibernation, severe paging storms, or total Python process freezes, the operator may not receive any Telegram notification. AXIOM cannot guarantee real-time hang detection from inside the same process on the same machine.

The 15-minute Telegram keepalive and 30-minute physical-check rule are retrospective diagnostics. They help the operator distinguish "system likely hung" from "system idle or no work available" when they return. They are not real-time alerts.

Real-time hang detection is deferred to Phase 2 through an out-of-process watchdog.

Operator-facing rule

If expected keepalive messages stop for:

30 minutes

during autonomous operation:

operator physically checks the laptop

This makes the limitation honest and avoids overstating what a single-machine, same-process supervisor can detect. 


---

10. Item 8 — Immediate Goal-Receipt Acknowledgement

Decision

Telegram Gateway sends an immediate acknowledgement for every accepted goal.

Acknowledgement template

Goal received. Planning and verification may take 1–3 minutes before the first executable task starts. Use /status for progress or /cancel_current_chain to cancel.

When sent

After:

operator ID verified
command parsed as goal
ingress sanitizer accepts message
goal_planning task inserted

Before:

Goal Planner cloud call
Result Verifier checkpoint call

Why

Goal Planner and Result Verifier may each take up to one cloud-call timeout, so the operator may see 1–3 minutes before meaningful activity. This prevents silence from being misread as a hang. 


---

11. Item 9 — Test List Reconciliation

Decision

The full MVP acceptance test list is the union of:

§12.3 MVP-test-required mechanisms
+
§14 v1.9 delta tests
+
v1.10 e2e test

Canonical MVP acceptance suite

tests/
  test_scheduler_single_running_task.py
  test_policy_engine_gate.py
  test_plan_injection_scanner.py
  test_classifier_calibration_thresholds.py
  test_task_committer_atomic_batch.py
  test_memory_gateway_verifier_context.py
  test_sandbox_no_network_validation.py
  test_sandbox_wall_clock_timeout.py
  test_token_estimator_dispatch_gate.py
  test_operator_control_capability_boundary.py
  test_scheduler_heartbeat_freshness.py
  test_provider_usage_reconciliation.py
  test_manifest_integrity_verification.py
  test_model_fingerprint_mid_session.py
  test_reconciliation_sanity_check.py
  test_task_planner_manifest_sizing.py
  test_operator_control_authorization_chain.py
  e2e/test_full_goal_flow_minimum.py

Meaning of sections

Section	Meaning

§12.3	Baseline MVP mechanism tests
§14	Delta tests added by v1.9
v1.10 §11	Canonical merged acceptance suite


Kimi should implement the canonical merged suite, not choose between prior lists.


---

12. Item 10 — Supervisor Stale-Check Logic Location

Decision

Supervisor stale-check logic lives in:

app/session_controller.py::SupervisorMonitor

Responsibility

SupervisorMonitor owns:

scheduler heartbeat stale check
Telegram thread liveness check
BootstrapValidationWorker liveness check
operator-interface-down safe-stop request
whole-session shutdown coordination

It does not own

task status transitions
PolicyEngine decisions
Tool execution
Result verification
ModelGateway calls

Stale-check flow

SupervisorMonitor reads scheduler_heartbeat.last_freshness_at
↓
if now - last_freshness_at > 120s:
    sessions.scheduler_status = stale
    sessions.autonomous_operation_enabled = false
    sessions.shutdown_requested = true
    session_events.scheduler_stale_detected
    Telegram alert if available

This prevents Kimi from splitting fail-closed stale handling across Scheduler, Telegram, and SessionController.


---

13. Item 11 — Task-Planner Manifest-Sizing Rule

Decision

Task Planner must size child-task manifests so dispatch-time prompt estimates have room for the required safety margin.

Rule

For any child task that may call a cloud model, Task Planner must set:

manifest.budget_policy.max_estimated_input_tokens

so that the expected prompt size is no more than the usable budget.

Usable budget by tokenizer mode

Tokenizer mode	Safety margin	Task Planner target

Calibrated tokenizer	2.0×	expected prompt ≤50% of manifest input cap
Fallback /3 estimator	1.5×	expected prompt ≤66% of manifest input cap


Formula

expected_prompt_tokens <= manifest_input_cap / safety_margin

If Task Planner cannot size within budget

Then it must produce one of:

smaller-context task
split task
needs_human_input
blocked_resource_limit

It may not simply request a manifest cap that violates session/provider budget.

Result Verifier checkpoint responsibility

Result Verifier in checkpoint mode must reject plans where:

expected prompt > manifest_input_cap / safety_margin

for any cloud-calling child task.

This prevents systematic false blocks at dispatch caused by planner-sized manifests that cannot satisfy the dispatch gate. 


---

14. Item 12 — Operator-Control Authorization Chain Ownership

Decision

Define ownership of each operator-control authorization step.

Seven-step chain

Step	Check	Owner

1	Telegram operator ID whitelist	app/telegram_gateway.py
2	Telegram thread object identity	app/operator_control_inserter.py
3	OperatorControlCapability object identity	app/operator_control_inserter.py
4	Command is in allowed operator-command table	app/command_parser.py
5	Matching per-command manifest exists	core/manifest_binder.py
6	ManifestBinder binds exact command manifest	core/manifest_binder.py
7	PolicyEngine approves operator_control task	core/policy_engine.py


Failure behavior

Failed step	Behavior

1	Ignore message or send unauthorized notice; no task
2	Reject insert; write security_events.operator_control_invalid_thread
3	Reject insert; write security_events.operator_control_invalid_capability
4	Reject command; no task
5	Reject command; write security_events.operator_control_manifest_missing
6	Roll back insert transaction
7	Task remains blocked; no control action applied


Atomic insertion

Operator-control task row, command row, and task-permission row must be inserted in one transaction after steps 1–6 pass.

Scheduler executes the operator-control task only after step 7 passes.


---

15. Revised Module Map Additions

security/
  manifest_integrity.py
  model_fingerprint_guard.py

core/
  resource_limits.py
    TokenEstimator
    ResourceGate
    ResourceLedger

app/
  session_controller.py
    SupervisorMonitor

tests/
  e2e/
    test_full_goal_flow_minimum.py

manifest_integrity.py may be implemented as part of security/audit.py if Kimi determines consolidation is simpler, but the mechanism remains required.


---

16. Final v1.10 Architecture Position

AXIOM v1.10 preserves the approved spine:

sequential runtime
SQLite task queue
Scheduler-owned state transitions
stateless PolicyEngine universal gate
manifest-scoped Tool Executor
Telegram control plane
sandbox/network separation
local classifier for sanitizer lane only
cloud models for cognitive work

v1.10 closes the remaining gaps:

Calibration test-set authorship now respects panel role separation.

Model fingerprint is checked before every classifier safe-pass decision.

Manifest files are SHA256-verified at boot and fail closed on mismatch.

MVP now has an end-to-end acceptance test.

Manual provider reconciliation has a ±50% sanity check.

Token margins are tiered by tokenizer quality.

Keepalive is framed as retrospective diagnostics, not real-time monitoring.

Telegram acknowledges goals immediately and sets latency expectations.

Acceptance tests are merged into one canonical suite.

Supervisor stale-check logic is owned by SessionController.

Task Planner must size manifests to satisfy dispatch-time budget margins.

Operator-control authorization has explicit per-step ownership.

Chief Architect recommendation

Return v1.10 to the panel for bounded delta review only.

If accepted, advance to Kimi for implementation planning constrained to the MVP module subset, canonical acceptance suite, and binding runtime conditions.