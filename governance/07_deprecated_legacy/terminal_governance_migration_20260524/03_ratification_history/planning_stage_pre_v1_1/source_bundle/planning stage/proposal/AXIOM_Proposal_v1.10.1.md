AXIOM Proposal v1.10.1 — Chief Architect Patch

Resolution of v1.10 Synthesis Patch Items 1–7

0. Patch Status

Field	Value

Proposal version	v1.10.1
Type	Patch to v1.10
Scope	Seven targeted spec additions only
Architecture spine changed?	No
Recommended next review	Delta-confirmation by Evaluator and Critic


The v1.10 synthesis states that the remaining work is “spec polish, not design re-think,” and identifies seven patch items before the proposal can advance to Kimi. This patch addresses only those items. 


---

1. Resolution Matrix

#	Required item	v1.10.1 resolution

1	Fingerprint verification error handling	5-second timeout; timeout/connection/malformed response fail closed
2	Telegram alert on fingerprint mismatch/failure	Immediate high-priority operator alert through Telegram Gateway
3	Manifest registration mode enforcement	Separate registration CLI; not available inside main AXIOM runtime
4	Cloud-model vs local TokenEstimator coordination	Result Verifier checkpoint invokes local TokenEstimator as source of truth
5	SQLite journal mode	Explicit PRAGMA journal_mode=WAL on every AXIOM connection
6	Calibration workflow dependency	MVP completion gates on panel-produced calibration artifact
7	Test list reconciliation	Restores/maps missing v1.9 tests into canonical suite
Note	Ollama thinking_mode	Kimi note: infer from /api/show template or system fields



---

2. Item 1 — Fingerprint Verification Error Handling

Decision

ModelFingerprintGuard.verify_current_profile() fails closed.

No infrastructure error may allow classifier safe-pass.

Timeout

model_fingerprint_verification_timeout_seconds = 5

Failure cases treated as mismatch

Failure	Behavior

Ollama API timeout	Treat as mismatch
Ollama connection refused	Treat as mismatch
Ollama malformed response	Treat as mismatch
Ollama schema changed / missing required fields	Treat as mismatch
Digest unavailable and fallback fingerprint unavailable	Treat as mismatch
Local model unavailable	Treat as mismatch


Failure behavior

On verification failure:

safe-pass disabled immediately
current classifier-dependent decision cannot return passed
security_events.model_fingerprint_verification_failed written
session_events.safe_pass_disabled_mid_session written
Telegram alert sent

Required security event

security_events.event_type = model_fingerprint_verification_failed
security_events.reason = timeout | connection_error | malformed_response | schema_change | digest_missing | model_unavailable
security_events.severity = critical

Scanner behavior after failure

Artifact risk	Scanner decision

high_risk	quarantined
ordinary	needs_human_input


This resolves the risk that a security-boundary check could fail open during an Ollama failure. The synthesis explicitly required fail-closed semantics for timeout, connection error, and malformed response. 


---

3. Item 2 — Telegram Alert on Fingerprint Mismatch or Verification Failure

Decision

Any mid-session model fingerprint mismatch or fingerprint verification failure sends an immediate Telegram alert.

Trigger conditions

Telegram alert fires when:

ModelFingerprintGuard detects fingerprint mismatch
OR
ModelFingerprintGuard verification fails due to timeout/connection/malformed response/schema change

Alert path

ModelFingerprintGuard
↓
security_events row
↓
session_events row
↓
Telegram Gateway high-priority alert queue
↓
operator receives alert

Message template — mismatch

SECURITY ALERT: AXIOM local model fingerprint changed mid-session.
Classifier safe-pass has been disabled.
High-risk artifacts will quarantine; ordinary artifacts will require human input.
Use /status for current session state.

Message template — verification failure

SECURITY ALERT: AXIOM could not verify the local model fingerprint.
Reason: <timeout | connection_error | malformed_response | schema_change | model_unavailable>.
Classifier safe-pass has been disabled.
Use /status for current session state.

If Telegram is unavailable

If the Telegram thread is down:

session_events.operator_alert_pending = true
SupervisorMonitor attempts Telegram restart
if restart fails: autonomous execution safe-stops

The v1.10 synthesis identifies mid-session model-profile change as a highest-criticality security event and requires a pushed Telegram alert, not merely a logged event. 


---

4. Item 3 — Manifest Registration Mode Enforcement

Decision

Manifest registration is performed by a separate operator-invoked CLI tool, not by the main AXIOM runtime.

CLI tool

tools/register_manifests.py

Main runtime rule

The main AXIOM process cannot enable manifest registration mode.

Remove any runtime-configurable setting equivalent to:

manifest_registration_mode = true

from the main autonomous process.

Registration flow

Operator stops AXIOM
↓
Operator runs tools/register_manifests.py from laptop
↓
CLI computes SHA256 for approved manifest files
↓
CLI writes manifest_fingerprints table
↓
CLI exits
↓
Operator starts AXIOM normally
↓
Runtime verifies manifest fingerprints at boot

CLI restrictions

Rule	Requirement

Not imported by main AXIOM runtime	Required
Not callable from Telegram	Required
Not available during autonomous operation	Required
Requires local filesystem access	Operator-only
Writes only manifest_fingerprints and audit event	Required


Runtime fail-closed behavior

If a manifest changes after registration:

ManifestIntegrityVerifier mismatch
↓
autonomous_operation_enabled = false
↓
operator_control disabled except /status and /shutdown_after_current
↓
Telegram reports manifest mismatch

Why CLI instead of command-line flag

A command-line flag is acceptable, but a separate CLI tool creates a cleaner boundary: manifest registration code is not part of the autonomous runtime surface at all. This directly addresses the concern that a compromised runtime could re-enable registration mode and silently re-register altered manifests. 


---

5. Item 4 — Cloud-Model vs Local TokenEstimator Coordination

Decision

Use option (a) from the synthesis:

Result Verifier checkpoint mode invokes the local TokenEstimator.

Cloud model self-reported token reasoning is not trusted for approval.

Source of truth

core/resource_limits.py::TokenEstimator

is the sole authority for prompt-size gate checks.

Checkpoint flow

Task Planner proposes child task and manifest budget
↓
Result Verifier checkpoint mode receives proposed task
↓
Checkpoint harness calls local TokenEstimator on proposed prompt/context shape
↓
TokenEstimator returns dispatch_estimated_tokens
↓
Checkpoint compares estimate against manifest budget using tiered margin
↓
If estimate violates budget: checkpoint fails
↓
If estimate passes: checkpoint may proceed to other semantic checks

Important boundary

The cloud Result Verifier may reason about whether the plan is semantically good, but it does not calculate the final token gate from its own intuition.

The deterministic harness supplies:

token_estimate
tokenizer_mode
required_margin
budget_pass = true | false

to the verifier context.

Failure behavior

If TokenEstimator is unavailable during checkpoint:

checkpoint fails closed
plan_artifact → checkpoint_failed
parent task → blocked or needs_human_input
security_events.token_estimator_unavailable

Dispatch consistency

The same TokenEstimator logic is used at:

checkpoint time
dispatch time

This removes divergence between cloud-model token reasoning and the local dispatch gate, the most substantive remaining gap identified in the synthesis. 


---

6. Item 5 — SQLite Journal Mode

Decision

AXIOM uses SQLite WAL mode.

Every SQLite connection must apply:

PRAGMA journal_mode=WAL;
PRAGMA synchronous=FULL;
PRAGMA busy_timeout=5000;

Allowed busy timeout range remains:

5000–10000 ms

Applies to

Telegram connection
Scheduler connection
BootstrapValidationWorker connection
registration CLI connection
any future AXIOM SQLite connection

Boot failure

If WAL cannot be enabled:

startup aborts
session_events.sqlite_wal_enable_failed
Telegram reports database initialization failure if Telegram is available

Rationale

SupervisorMonitor must be able to read heartbeat/session state while the Scheduler performs writes. WAL reduces read/write contention and is required for the concurrent-thread design. The synthesis specifically identified rollback-journal lock contention as a risk on the target SATA SSD system. 


---

7. Item 6 — Calibration Test-Set Workflow Dependency

Decision

MVP completion depends on a panel-produced calibration artifact.

This is a project-management dependency, not an architecture defect.

Required workflow before safe-pass and full e2e acceptance

Gemini authors injection_classifier_v1.jsonl
↓
DeepSeek adversarially reviews it
↓
Claude checks coherence and final acceptance
↓
Qwen checks feasibility
↓
Kimi packages it into implementation plan
↓
Human operator writes approved file to disk
↓
Classifier calibration runs
↓
Safe-pass may enable only if calibration passes

Implementation sequencing requirement

Kimi must sequence MVP work so that:

safe-pass paths
classifier-dependent PlanInjectionScanner pass decisions
full e2e acceptance with classifier paths

are not marked complete until the calibration test set exists and passes.

Interim MVP behavior

Before calibration artifact exists:

classifier safe-pass disabled
high-risk artifacts quarantine or escalate
ordinary uncertain artifacts require human input

The synthesis requires this dependency to be visible so Kimi does not treat the e2e classifier path as implementable before the panel workflow produces the test set. 


---

8. Item 7 — Canonical Test List Reconciliation

Decision

The canonical MVP acceptance suite is the merged list below.

The v1.10 canonical list is amended to restore/map the missing v1.9 tests.

Canonical MVP acceptance suite — v1.10.1

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
  test_artifact_risk_classification.py
  test_privileged_task_class_closed_set.py
  test_model_gateway_provider_timeout.py
  test_operator_capability_restart_rebind.py
  test_task_committer_atomicity.py
  test_classifier_embedded_instruction_no_rule_hit.py
  test_provider_usage_orphan_all_sessions.py
  test_model_fingerprint_guard_fail_closed.py
  test_fingerprint_telegram_alert.py
  test_manifest_registration_cli_boundary.py
  test_checkpoint_uses_local_token_estimator.py
  test_sqlite_wal_mode.py
  e2e/test_full_goal_flow_minimum.py

Mapping of previously missing v1.9 tests

v1.9 test	v1.10.1 status	Rationale

test_artifact_risk_classification.py	Restored	Required for scanner risk-class determinism
test_privileged_task_class_closed_set.py	Restored	Required for closed privileged class set
test_model_gateway_provider_timeout.py	Restored	Required for per-provider-call timeout
test_operator_capability_restart_rebind.py	Restored	Required for Telegram restart capability continuity
test_task_committer_atomic_batch.py	Already present	Canonical name retained
test_memory_gateway_verifier_context.py	Already present	Covers memory verification loop
test_provider_usage_orphan_all_sessions.py	Restored	Required for all-session orphan recovery
test_classifier_embedded_instruction_no_rule_hit.py	Restored	Required for classifier-only injection signals


New v1.10.1 tests

Test	Required assertion

test_model_fingerprint_guard_fail_closed.py	Timeout/connection/malformed Ollama response disables safe-pass
test_fingerprint_telegram_alert.py	Mismatch/failure triggers Telegram alert
test_manifest_registration_cli_boundary.py	Main runtime cannot register manifests
test_checkpoint_uses_local_token_estimator.py	Checkpoint budget gate uses local TokenEstimator
test_sqlite_wal_mode.py	WAL enabled for all connections


This resolves the outstanding test-list reconciliation requested in the synthesis. 


---

9. Kimi Implementation Note — Ollama thinking_mode

Forward-pass note

Ollama does not expose a native stable field named:

thinking_mode

Therefore ModelFingerprintGuard must infer qwen3:4b thinking-state from metadata returned by:

/api/show

Specifically inspect:

template
system
parameters

for the configured no-thinking / thinking-disabled prompt pattern.

Fingerprint implication

The inferred thinking-state is part of the model profile fingerprint.

If the template/system fields change such that thinking-disabled state cannot be verified:

safe-pass disabled
security_events.model_fingerprint_verification_failed
Telegram alert sent

This captures the Arbiter implementation note so Kimi does not assume an Ollama field that may not exist. 


---

10. Final v1.10.1 Patch Position

v1.10.1 makes no structural changes. It tightens established boundaries:

Fingerprint verification fails closed on Ollama errors.

Fingerprint mismatch/failure alerts the operator immediately.

Manifest registration is moved out of the autonomous runtime into a separate CLI.

Checkpoint budget validation uses the local TokenEstimator as the source of truth.

SQLite WAL mode is explicit and required.

Calibration test-set workflow is acknowledged as an MVP dependency.

The canonical MVP acceptance suite is reconciled and complete.

Ollama thinking-mode verification is documented for Kimi.

Chief Architect recommendation

Return v1.10.1 to the Evaluator and Critic for delta-confirmation only.

If accepted, advance to Kimi for implementation planning under the canonical MVP acceptance suite and binding runtime conditions.