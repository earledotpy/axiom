AXIOM Proposal v1.10.2 — Chief Architect Addendum

Final Spec Completion Before Kimi Implementation Planning

0. Addendum Status

Field	Value

Proposal version	v1.10.2
Type	Small addendum to v1.10.1
Scope	Seven targeted completion items only
Architecture spine changed?	No
Recommended next step	Delta-confirmation by Evaluator, then advance to Kimi


The v1.10.1 synthesis states that the Critic recommends advancement to Kimi and frames all six objections as non-blocking, but asks for a small addendum covering two state-machine/spec gaps, several Kimi-facing notes, and one unresolved test-list footnote. 


---

1. Artifact Lifecycle on Fingerprint-Related Scanner Failure

Decision

Fingerprint-related scanner failure affects both the plan artifact lifecycle and the parent task lifecycle.

Trigger cases

This rule applies when ModelFingerprintGuard produces:

fingerprint_mismatch
verification_timeout
connection_error
malformed_response
schema_change
model_unavailable

Lifecycle disposition

Artifact risk class	Scanner result	Plan artifact state	Parent task state

high_risk	Safe-pass disabled	quarantined	quarantined
ordinary	Safe-pass disabled	checkpoint_blocked	needs_human_input


Rehabilitation rule

High-risk artifacts

High-risk artifacts that become:

quarantined

because of fingerprint mismatch or verification failure are session-terminal.

They may not be re-scanned in the same session.

Recovery path:

operator resolves model/fingerprint issue
↓
classifier calibration or fingerprint verification passes
↓
operator resubmits the original goal
↓
new plan artifact is generated

Ordinary artifacts

Ordinary artifacts that become:

checkpoint_blocked

may be re-scanned only after:

safe-pass re-enabled
AND
fingerprint verification passes
AND
operator explicitly requests retry

The parent task remains:

needs_human_input

until the operator acts.

Why high-risk artifacts cannot rehabilitate in-session

High-risk artifacts may contain unsafe instructions, privileged-task attempts, network/sandbox requests, or memory-write candidates. Once the security boundary fails while evaluating that artifact, AXIOM treats the artifact as tainted for that session and requires regeneration rather than rehabilitation.


---

2. Alert Deduplication Through Safe-Pass Session State

Decision

Once safe-pass is disabled mid-session, PlanInjectionScanner short-circuits classifier-dependent safe-pass rules.

Session flag

Add:

sessions.safe_pass_enabled
sessions.safe_pass_disabled_reason
sessions.safe_pass_disabled_at
sessions.safe_pass_alert_sent

Behavior

When fingerprint mismatch or verification failure occurs:

sessions.safe_pass_enabled = false
sessions.safe_pass_disabled_reason = <reason>
sessions.safe_pass_alert_sent = true after Telegram alert succeeds or is queued

Scanner short-circuit rule

If:

sessions.safe_pass_enabled = false

then PlanInjectionScanner does not call:

ModelFingerprintGuard.verify_current_profile()

for later classifier-dependent safe-pass decisions in the same session.

Instead:

Artifact risk class	Decision

high_risk	quarantined
ordinary	needs_human_input


Alert deduplication

The Telegram alert fires once per session per disablement event.

Repeated scanner evaluations after safe-pass is disabled do not produce repeated fingerprint alerts. /status reports the persistent safe-pass-disabled state.


---

3. Operational Tuning Notes for Kimi

3.1 Fingerprint timeout tunability

Default:

model_fingerprint_verification_timeout_seconds = 5

Kimi may make this timeout configurable in the local config file if first-session measurements show false failures under paging pressure.

Constraints:

must fail closed
must log timeout separately from digest mismatch
must not exceed 15 seconds without panel review

3.2 Manifest registration CLI database settings

tools/register_manifests.py must use:

same AXIOM database path
same SQLite PRAGMAs as main runtime

Required PRAGMAs:

PRAGMA journal_mode=WAL;
PRAGMA synchronous=FULL;
PRAGMA busy_timeout=5000;

3.3 WAL checkpoint tunability

Kimi may tune SQLite WAL checkpoint behavior if it becomes operationally significant on the SATA SSD target.

Allowed tuning:

passive checkpoint strategy
auto-checkpoint threshold
operator-triggered maintenance command

Not allowed without panel review:

changing journal_mode away from WAL
changing synchronous below FULL


---

4. Checkpoint Estimate vs. Realized Dispatch Prompt

Decision

Checkpoint-time token estimation and dispatch-time token estimation use the same local TokenEstimator, but they may evaluate different prompt material.

Distinction

Stage	What is estimated

Checkpoint	Proposed prompt/context shape from the plan artifact
Dispatch	Realized final prompt after context retrieval, memory selection, and final Context Builder assembly


Rule

Checkpoint approval does not guarantee dispatch approval. It only verifies that the proposed task is expected to fit.

The dispatch gate remains authoritative.

Margin protection

The Task Planner sizing rule exists to absorb normal divergence:

Tokenizer mode	Planner target

Calibrated tokenizer	expected prompt ≤50% of manifest input cap
Fallback /3 estimator	expected prompt ≤66% of manifest input cap


If realized dispatch exceeds budget

The existing remediation flow applies:

Context Builder shrinks context once
↓
remove lowest-ranked memory chunks if needed
↓
retry estimate once
↓
if still over budget:
    task → blocked_resource_limit or needs_human_input

This prevents Kimi from reading checkpoint estimation as a promise that dispatch cannot fail.


---

5. Test-List Reconciliation Footnote

Decision

The seven tests flagged as missing are either restored or mapped below.

Flagged test	v1.10.2 disposition	Rationale

test_sandbox_heartbeat_ordering.py	Restored	Required to verify post-sandbox heartbeat writes before any following blocking operation
test_calibration_set_ownership_metadata.py	Restored as test_calibration_set_panel_ownership_metadata.py	Renamed to reflect Gemini primary authorship and panel review chain
test_task_committer_validation_scope.py	Restored	Required to prove TaskCommitter performs deterministic validation only
test_checkpoint_semantic_consistency.py	Restored	Required to prove Result Verifier owns semantic consistency checks
test_operator_control_manifest_binding.py	Restored	Required to prove per-command manifests bind only after capability-token authorization
test_supervisor_liveness_limit_notice.py	Restored	Required to prove whole-system hang limitation and operator keepalive notice are documented/surfaced
test_mvp_module_boundary.py	Restored	Required to verify MVP vs deferred module split


Canonical suite addition

Add these to the canonical MVP acceptance suite:

test_sandbox_heartbeat_ordering.py
test_calibration_set_panel_ownership_metadata.py
test_task_committer_validation_scope.py
test_checkpoint_semantic_consistency.py
test_operator_control_manifest_binding.py
test_supervisor_liveness_limit_notice.py
test_mvp_module_boundary.py

These are additive to the v1.10.1 canonical suite, not replacements.


---

6. Final v1.10.2 Position

v1.10.2 adds no new architecture. It completes the specification by defining:

artifact lifecycle after fingerprint-related scanner failure
safe-pass session-state short-circuit and alert deduplication
Kimi tuning notes for fingerprint timeout and WAL checkpointing
manifest registration CLI database settings
checkpoint-estimate versus dispatch-estimate relationship
the seven missing MVP acceptance tests

Chief Architect recommendation

Attach v1.10.2 to v1.10.1 as the final addendum.

Proceed to Evaluator delta-confirmation. If confirmed, advance to Kimi for implementation planning.