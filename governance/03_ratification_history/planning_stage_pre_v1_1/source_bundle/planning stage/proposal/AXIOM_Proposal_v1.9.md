AXIOM Proposal v1.9 — Chief Architect Revision

Resolution of v1.8 / v1.8.1 Panel Synthesis

0. Status

Field	Value

Proposal version	v1.9
Type	Targeted architectural revision
Scope	Resolves ten required synthesis items from v1.8 / v1.8.1
Architecture spine changed?	No
Implementation-ready?	Pending targeted panel confirmation
Recommended next step	Targeted review against items 1–10 only


The panel synthesis found that v1.8 / v1.8.1 preserved the architecture spine but still contained unresolved specification gaps around heartbeat semantics, sandbox wall-clock enforcement, calibration ownership, TaskCommitter validation scope, operator-control manifests, token counting, model-profile change detection, provider-usage reconciliation, supervisor liveness limits, and MVP scope. None of the objections were overruled by the Arbiter and Constraints Reviewer, so v1.9 resolves them directly. 


---

1. Binding Rulings Carried Forward

1.1 Arbiter binding

Sandbox wall-clock enforcement requires:

subprocess.run(timeout=60)

or an equivalent wall-clock timeout wrapper in addition to the Windows Job Object controls. Job Object limits remain required for RAM/process containment, but they are not the wall-clock duration boundary. 

1.2 Constraints binding

The following remain binding implementation constraints:

Constraint	Required value

Execution	Strict sequential execution
Thread cap	4 threads maximum: main supervisor, Telegram, Scheduler, BootstrapValidationWorker
Local model	qwen3:4b, Q4 quantized, memory-mapped via Ollama
Context bundle	≤500 KB serialized
Sandbox	256 MB RAM cap + 60s wall-clock cap
Vector search	sqlite-vec ≤100 vectors per query/batch
Token budget	2× safety margin before cloud dispatch
PolicyEngine	Stateless
Web search	Brave Search API or panel-approved free-tier alternative before enabling web search
Safe-pass	Disabled until calibration passes


The hardware and budget constraints remain the controlling limits: HP laptop, Celeron N4500, 8 GB RAM, Windows 11, no GPU, no new hardware, Telegram interface, and free/near-zero API budget. 


---

2. Resolution Matrix

#	Required revision	v1.9 resolution

1	Heartbeat field semantics	Introduces last_freshness_at; every heartbeat write updates it
2	Sandbox wall-clock enforcement	Adds subprocess.run(timeout=60) + termination-overhead budget + heartbeat ordering
3	Calibration test-set ownership	Assigns authorship to DeepSeek, factual review to Gemini, final coherence review to Claude
4	TaskCommitter validation scope	Bounds TaskCommitter to deterministic validation; assigns semantic consistency to Result Verifier checkpoint mode
5	Operator-control manifest role	Operator-control manifests are enforced and bound to capability token; moved to dedicated enforced operator policy folder
6	Token-counting mechanism	Adds dispatch-time tokenizer policy with conservative fallback
7	Model-profile change detection	Adds Ollama model digest/checksum record and boot verification
8	Orphan provider-call reconciliation	Adds /reconcile_provider_usage manual reconciliation + monthly ledger reset option
9	Supervisor liveness limitation	Documents whole-system hang limitation and operator-side keepalive mitigation
10	MVP module subset	Tags MVP-required vs deferred modules



---

3. Item 1 — Heartbeat Field Semantics

Decision

Replace ambiguous freshness use of:

last_tick_at

with canonical freshness field:

last_freshness_at

Heartbeat schema

scheduler_heartbeat
  session_id
  last_freshness_at
  last_tick_started_at
  last_tick_completed_at
  last_blocking_operation_started_at
  last_blocking_operation_completed_at
  last_blocking_operation_type
  active_task_id
  active_chain_id
  scheduler_state
  last_action
  tick_count

Canonical freshness rule

Every heartbeat write updates:

scheduler_heartbeat.last_freshness_at = now()

This includes heartbeat writes:

before scheduler tick
after scheduler tick
before cloud call
after cloud call
before sandbox execution
after sandbox termination handling completes
before any subsequent blocking operation

Supervisor stale check

The supervisor uses only:

now - scheduler_heartbeat.last_freshness_at > scheduler_stale_threshold_seconds

It does not use last_tick_started_at as the freshness signal.

Re-audited heartbeat math

Operation	Maximum duration

Sandbox wall-clock execution	60s
Sandbox termination overhead budget	10s
Largest cloud provider call	90s
Freshness margin	30s


The Scheduler writes a freshness heartbeat between sandbox completion/termination and any later cloud call. Therefore the supervisor never sees a legitimate combined 60s + 10s + 90s silence window. The maximum legitimate silence window is the largest single bounded operation plus its own cleanup margin:

max(90s cloud call, 60s sandbox + 10s termination overhead) + 30s margin
= 120s

Therefore:

scheduler_stale_threshold_seconds = 120

remains valid only because every blocking-operation boundary updates last_freshness_at.


---

4. Item 2 — Sandbox Wall-Clock Enforcement

Decision

Sandbox duration is enforced by both:

subprocess.run(timeout=60)

and the existing Windows Job Object controls.

Sandbox enforcement stack

Control	Mechanism	Purpose

Wall-clock duration	subprocess.run(timeout=60) or equivalent wall-clock wrapper	Stops sleeping/waiting processes
RAM	Windows Job Object memory limit	256 MB cap
Process containment	Windows Job Object	Child process containment
Network	Dedicated sandbox user + outbound firewall deny	No network
Privilege	Restricted token	Least privilege
Filesystem	Sandbox working dir + ACLs	No host writes


Sandbox duration rule

max_sandbox_execution_seconds = 60
max_sandbox_termination_overhead_seconds = 10

Timeout behavior

SandboxGateway starts sandboxed process
↓
subprocess.run(..., timeout=60)
↓
If timeout fires:
    terminate process tree under Job Object
    wait up to 10s for termination cleanup
    write gateway_response.status = failed_resource_limit
    write resource_usage.sandbox_timeout = true
    update scheduler_heartbeat.last_freshness_at
    task → failed_resource_limit

Heartbeat ordering requirement

The Scheduler must complete this sequence:

sandbox execution starts
↓
heartbeat before sandbox
↓
sandbox returns / fails / times out
↓
termination handling completes
↓
heartbeat after sandbox termination handling
↓
only then may the Scheduler start a cloud call or any other blocking operation

A post-sandbox heartbeat is not optional. If the heartbeat write fails, the Scheduler must halt autonomous execution and mark the session abnormal.


---

5. Item 3 — Calibration Test Set Ownership

Decision

The classifier calibration test set is a panel-authored security artifact.

The operator does not author it.

Ownership

Responsibility	Owner

Primary author	DeepSeek V4 — Adversarial Critic
Factual/coverage review	Gemini 3.1 Pro — Research and Knowledge Arbiter
Coherence/final acceptance review	Claude Opus 4.7 — Quality and Coherence Evaluator
Feasibility review	Qwen 3.6 Plus
Implementation packaging	Kimi K2.6
Physical file creation	Human operator executes approved file operation only


Test-set artifact

security/test_sets/injection_classifier_v1.jsonl

Required contents

Category	Samples

Direct instruction override	10
Role escalation	10
Queue manipulation	10
Manifest/tool manipulation	10
Sandbox/network bypass	10
Memory poisoning	10
Secret extraction	10
Encoded/obfuscated instruction	10
Web-content injection	10
Benign controls	30
Total	120


Required critical samples:

40 critical malicious samples

Interim default until calibration passes

Until the classifier calibration passes:

classifier safe-pass = disabled

Runtime behavior:

Classifier signal	Interim behavior

Any suspicious label	Quarantine for high-risk artifacts; needs_human_input for ordinary artifacts
Low confidence	needs_human_input or quarantine depending on risk
Safe/untrusted label	Does not safe-pass by itself
Scanner ambiguity	Block or escalate; do not commit child tasks


Maintenance rule

DeepSeek owns updates when new attack classes are identified. Gemini verifies factual realism of attack examples. Claude confirms the set still matches AXIOM’s security model. Qwen confirms runtime feasibility.

Trigger for test-set maintenance:

new attack vector identified
model profile changed
classifier drift detected
false negative found
Phase 2 tool surface expands


---

6. Item 4 — TaskCommitter Validation Scope

Decision

TaskCommitter performs deterministic commit validation only.

It does not perform semantic consistency reasoning.

TaskCommitter validation scope

TaskCommitter validates:

plan_artifact.artifact_status = checkpoint_passed
plan_artifact.commit_status = not_started
plan schema shape
child task required fields
task_class allowed value
capability vocabulary
creator allowlist
manifest template existence
manifest compatibility
acceptance criteria field presence
commit_batch_id generation
task_permissions row creation

TaskCommitter does not validate:

whether the task is a good plan
whether the acceptance criteria are semantically sufficient
whether the tool choice is strategically wise
whether the chain fully solves the human goal
whether task decomposition is conceptually correct

Semantic consistency owner

Semantic consistency belongs to:

Result Verifier in plan_checkpoint / subtask_checkpoint mode

Result Verifier checkpoint responsibilities

Before an artifact reaches TaskCommitter, Result Verifier must check:

Semantic check	Required?

Child task matches parent goal	Yes
Tool assignment fits task intent	Yes
Acceptance criteria are testable and relevant	Yes
Task dependencies are coherent	Yes
Plan does not smuggle privileged task classes	Yes
Plan obeys Core Values	Yes
Plan obeys Constraints Register	Yes


Chain of responsibility

PlanInjectionScanner
  security / injection risk

Result Verifier checkpoint mode
  semantic consistency

TaskCommitter
  deterministic schema + manifest + atomic commit

This avoids the false implication that deterministic code is expected to perform semantic review.


---

7. Item 5 — Per-Command Operator-Control Manifest Role

Decision

Per-command operator-control manifests are enforced artifacts, not documentation.

They are bound only after object-identity authorization succeeds.

Directory relocation

Move operator-control manifests out of general role manifests:

policy/operator_control_manifests/
  status.json
  cancel_current_chain.json
  pause_after_current.json
  resume.json
  shutdown_after_current.json
  run_classifier_validation.json
  enable_autonomous.json
  reconcile_provider_usage.json

General role manifests remain in:

policy/role_manifests/

Enforcement order

Operator-control authorization requires all layers:

1. Telegram operator ID whitelist passes
2. Telegram thread object identity passes
3. OperatorControlCapability object identity passes
4. Command is in allowed operator command table
5. Matching per-command manifest exists
6. ManifestBinder binds that exact command manifest
7. PolicyEngine approves operator_control task

Critical rule

The manifest is not the primary authorization boundary.

The manifest limits what an already-authorized operator-control command can do.

Example

cancel_current_chain.json may grant:

tasks.cancel_requested
operator_commands
task_events

It may not grant:

tasks.status
task_permissions
memory_items
plan_artifacts

Manifest mismatch rule

If command type and manifest file do not match:

operator_control task not created
security_events.operator_control_manifest_mismatch

This removes ambiguity between capability-token security and manifest-based capability minimization.


---

8. Item 6 — Token-Counting Mechanism

Decision

Cloud dispatch uses dispatch-time local token estimation, not plan-time manifest estimates alone.

Token estimator component

core/resource_limits.py::TokenEstimator

Estimation policy

Provider/model type	Tokenizer

Provider supplies official tokenizer locally	Use provider/model tokenizer
OpenAI-compatible tokenizer available	Use tiktoken-style tokenizer
No tokenizer available	Conservative character approximation
Unknown model/provider	Conservative approximation only


Conservative approximation

Default fallback:

estimated_tokens = ceil(character_count / 3)

Reason: this intentionally overestimates token count compared with common 4-character approximations.

Dispatch-time token check

At dispatch time, after the Context Builder assembles the final prompt:

actual_dispatch_estimate = TokenEstimator.count(final_prompt)

Then:

actual_dispatch_estimate * 2.0 <= task_manifest.budget_policy.max_estimated_input_tokens

must be true.

If dispatch estimate exceeds manifest estimate

Condition	Behavior

Exceeds but can shrink context	Context Builder rebuilds once with smaller memory/context bundle
Still exceeds after rebuild	Task → blocked_resource_limit
Exceeds due to retrieved memory	Remove lowest-ranked memory chunks and retry once
Exceeds due to required task payload	Task → needs_human_input
Exceeds due to planner underestimation	Record resource_events.planner_underestimate


Actual usage logging

If provider returns actual tokens:

provider_usage.actual_input_tokens
provider_usage.actual_output_tokens

If provider does not return actuals:

provider_usage.actuals_unavailable = true
provider_usage.charged_input_estimate = dispatch_estimated_input_tokens
provider_usage.charged_output_estimate = manifest_estimated_output_tokens

This operationalizes the 2× safety-margin binding condition and prevents variable context bundles from bypassing the budget gate. 


---

9. Item 7 — Model Profile Change Detection

Decision

Calibration is tied to a concrete local model profile fingerprint.

If the fingerprint changes, safe-pass is disabled until recalibration succeeds.

Model profile record

Add table:

model_profile_fingerprints

Fields:

profile_id
model_name
ollama_model_tag
ollama_model_digest
quantization
thinking_mode
ollama_show_json_hash
model_file_mtime
model_file_size
calibration_id
created_at

Boot-time verification

At boot:

read current Ollama model metadata
compute current profile fingerprint
compare to fingerprint stored with latest passing calibration

Mismatch behavior

Mismatch	Behavior

Ollama digest changed	Disable classifier safe-pass; require recalibration
Quantization changed	Disable classifier safe-pass; require recalibration
Thinking mode changed	Disable classifier safe-pass; require recalibration
Model file mtime changed but digest unavailable	Warn operator; disable safe-pass until recalibration
Model unavailable	Disable autonomous operation
Metadata query fails	Disable safe-pass; allow bootstrap validation only


Accepted fallback if digest unavailable

If Ollama cannot provide stable digest metadata, AXIOM uses:

model_file_mtime
model_file_size
ollama_show_json_hash

as a weaker fingerprint.

If any of those change:

safe-pass disabled
calibration invalidated

No silent model-profile drift is allowed.


---

10. Item 8 — Orphan Provider-Call Reconciliation

Decision

AXIOM uses conservative immediate charging plus manual reconciliation.

Immediate recovery behavior

On startup, all non-current orphan provider calls:

provider_usage.status = started
AND session_id != current_session_id

become:

status = abandoned_session_crash
actuals_unavailable = true
charged_input_estimate = estimated_input_tokens
charged_output_estimate = estimated_output_tokens

Reconciliation command

Add operator command:

/reconcile_provider_usage

Reconciliation method

Because free-tier provider usage endpoints may not expose full programmatic usage data, Phase 1 uses manual reconciliation.

Flow:

Operator opens provider dashboard
↓
Operator copies usage totals for date range
↓
Operator sends /reconcile_provider_usage
↓
Telegram prompts for provider/date/token totals
↓
AXIOM stores reconciliation record
↓
ResourceLedger adjusts local budget ledger

Reconciliation table

provider_usage_reconciliations
  reconciliation_id
  provider
  date_range_start
  date_range_end
  operator_reported_input_tokens
  operator_reported_output_tokens
  local_estimated_tokens
  adjustment_tokens
  notes
  created_at

Reset cadence

If the operator does not reconcile manually:

budget ledger reset recommended monthly

Monthly reset does not delete audit records. It starts a new budget accounting window:

provider_budget_window

Budget policy

Situation	Behavior

Unknown orphan usage	Count estimate against current budget
Manual reconciliation lower than estimate	Adjust available budget upward
Manual reconciliation higher than estimate	Adjust available budget downward
No reconciliation	Conservative estimate remains
Monthly reset	New accounting window; old audit retained


This preserves safety while acknowledging that permanent drift is otherwise unavoidable.


---

11. Item 9 — Supervisor Liveness Limitation and Mitigation

Decision

AXIOM acknowledges that a single-machine system cannot fully detect whole-system hangs.

Explicit limitation

If Windows hibernates, the machine enters a severe paging storm, the Python process freezes, or the OS scheduler stalls all threads:

main supervisor thread may not run
Telegram thread may not respond
Scheduler heartbeat may not update
AXIOM may be unable to notify the operator

This cannot be solved completely inside the same process on the same machine.

Phase 1 mitigation

Use operator-side keepalive expectation.

Telegram Gateway sends heartbeat summary messages when autonomous mode is active:

default: every 15 minutes

Message:

AXIOM alive.
Scheduler status: running / paused / blocked
Active task: <task_id or none>
Last freshness: <timestamp>
Budget window: <summary>

Operator rule

If no Telegram keepalive or status response is received for:

30 minutes

during expected autonomous operation:

operator must physically check the laptop

Optional Phase 2 mitigation

Phase 2 may add an out-of-process watchdog:

Windows Scheduled Task
or
Servy-managed watchdog process

It may check a local health file or endpoint and notify the operator if heartbeat stops.

Not Phase 1 primary path because it adds another moving part and must be evaluated separately under Core Value 4.


---

12. Item 10 — MVP Module Subset

Decision

v1.9 splits the architecture into:

MVP-required
MVP-test-required
Deferred Phase 2

This prevents Kimi from treating every named file as mandatory for the first executable slice.

12.1 MVP-required modules

These must exist for AXIOM Phase 1 to start safely:

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

persistence/
  db.py
  schema.sql
  repositories.py

12.2 MVP policy artifacts

policy/role_manifests/
  goal_planner.json
  task_planner.json
  tool_executor_network_fetch.json
  tool_executor_sandbox_execute.json
  tool_executor_file_limited.json
  result_verifier.json

policy/operator_control_manifests/
  status.json
  cancel_current_chain.json
  pause_after_current.json
  resume.json
  shutdown_after_current.json
  run_classifier_validation.json
  enable_autonomous.json
  reconcile_provider_usage.json

security/test_sets/
  injection_classifier_v1.jsonl

12.3 MVP-test-required, but implementation sequencing flexible

Kimi may sequence these tests across implementation milestones, but the MVP is not accepted until they pass:

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

12.4 Deferred Phase 2 modules/features

These are not required for MVP start:

external watchdog process
Servy-managed service mode
advanced provider scoring
automatic provider-dashboard reconciliation
large-context special routing beyond current manifest cap
parallel task execution
background model-call completion handlers
additional UI beyond Telegram
automated test-set generation
dynamic calibration-set expansion

Why this satisfies Core Value 4

The MVP remains larger than a toy system because AXIOM’s minimum viable slice must include the security boundaries that make autonomy safe. The deferred list excludes scalability and convenience features while preserving the non-negotiables: queue mediation, policy gate, sandbox/network separation, manifest binding, memory verification, and operator control.


---

13. Revised Module Map

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

    operator_control_manifests/
      status.json
      cancel_current_chain.json
      pause_after_current.json
      resume.json
      shutdown_after_current.json
      run_classifier_validation.json
      enable_autonomous.json
      reconcile_provider_usage.json

Removed from MVP map:

watchdog.py
cancellation.py

Their functions are absorbed into:

scheduler.py
session_controller.py
resource_limits.py

This reduces module count while preserving behavior.


---

14. Revised Acceptance Tests

Test	Required assertion

test_scheduler_heartbeat_freshness.py	Every heartbeat write updates last_freshness_at; stale check uses only that field
test_sandbox_wall_clock_timeout.py	Sandbox process sleeping >60s is terminated by wall-clock timeout
test_sandbox_heartbeat_ordering.py	Post-sandbox heartbeat writes before any following blocking operation
test_calibration_set_ownership_metadata.py	Test set records DeepSeek author, Gemini review, Claude acceptance
test_task_committer_validation_scope.py	TaskCommitter does deterministic validation only
test_checkpoint_semantic_consistency.py	Result Verifier owns tool/acceptance semantic consistency
test_operator_control_manifest_binding.py	Per-command operator manifests bind only after capability token passes
test_token_estimator_dispatch_gate.py	Final prompt token estimate with 2× margin gates cloud call
test_model_profile_fingerprint.py	Model fingerprint mismatch disables safe-pass
test_provider_usage_reconciliation.py	Manual reconciliation adjusts budget ledger without deleting audit
test_supervisor_liveness_limit_notice.py	Operator keepalive policy is documented and status messages emit
test_mvp_module_boundary.py	MVP module list excludes deferred Phase 2 components



---

15. Final v1.9 Architecture Position

AXIOM v1.9 preserves the architecture spine:

Sequential runtime.
SQLite task queue.
Scheduler-owned state transitions.
Stateless PolicyEngine universal gate.
Manifest-scoped Tool Executor.
Telegram control plane.
Sandbox/network separation.
Local classifier for sanitizer lane only.
Cloud models for cognitive work.

v1.9 closes the remaining panel objections:

Heartbeat freshness semantics are explicit.

Sandbox wall-clock enforcement uses subprocess timeout plus Job Object controls.

Calibration test-set authorship belongs to the panel, not the operator.

TaskCommitter validation is deterministic and bounded.

Semantic consistency belongs to Result Verifier checkpoint mode.

Operator-control manifests are enforced only after capability-token authorization.

Dispatch-time token counting gates cloud calls.

Model-profile changes invalidate calibration.

Orphan provider-call budget drift has manual reconciliation.

Whole-system hangs are acknowledged with operator-side keepalive mitigation.

The MVP module subset is separated from deferred Phase 2 features.