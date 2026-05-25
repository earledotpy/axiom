# Evaluator Review — AXIOM Proposal v1.8

**Bottom line:** v1.8 closes seven of eight blocking items (A–H) cleanly and folds in the four spec touch-ups (I′–L) and Qwen's nine binding conditions. **One architectural gap remains** — the scheduler heartbeat threshold is derived only from cloud-call duration and does not account for sandbox execution time, which is itself uncapped. Plus one documentation inconsistency between §11 and §16 worth tightening. **Recommend: Architect produces a small v1.8.1 patch addressing both, then a targeted re-cycle on the delta only.** No structural revision needed.

---

## 1. Resolution of v1.7 Synthesis Items

I traced each item from my prior synthesis through the v1.8 proposal independently of the Architect's own resolution matrix.

| Item | v1.8 location | Resolution | Status |
|---|---|---|---|
| **A** Artifact risk class definition | §3 | Risk class is scanner-computed (not Goal-Planner-assigned), tied to plan-artifact contents via 14 deterministic triggers; ANY trigger → high_risk; stored as `plan_artifacts.risk_class`. Rules 6, 7, 10, 11 reference the field, not prose labels | **Closed** |
| **B** Privileged task class enumeration | §4 | Closed set: `{operator_control, bootstrap_validation}`. Rule 3 reworded. Allowed-creator table per class. Spoof attempt → `security_events.privileged_task_class_spoof_attempt` | **Closed** |
| **C** Cloud-call timeout ceiling | §5 | Per-provider-call timeouts: 30s primary / 45s fallback / 60s large-context / 90s absolute hard ceiling. Per-call enforcement (not per-cascade). `max_model_calls=2` default. Cancel-during-call documented as "continues until timeout/response" — that's the operator-responsiveness bound | **Closed** |
| **D** Heartbeat liveness threshold + dead-scheduler action | §6 | Threshold = 120s (90s ceiling + 30s margin). Stale rule explicit. Action = fail-closed + human-escalate (no auto-restart, with rationale). Telegram notification specified | **Closed for cloud-call path; gap for sandbox path** — see §3 below |
| **E** OperatorControlCapability re-establishment | §7 | SessionController owns the cap for session lifetime; passes reference to Telegram Gateway on construction and on restart; OperatorControlInserter validates object identity. Fail-closed if cap can't be re-passed: restart fails, operator_control disabled, scheduler safe-stops. **No degraded gateway without capability** | **Closed** |
| **F** TaskCommitter atomic boundary | §8 | `BEGIN IMMEDIATE` ... `COMMIT` with 12 ordered steps; ROLLBACK on any failure. Scheduler selection guard requires non-NULL `commit_batch_id` and existing `task_permissions`. Crash recovery for partial-commit corruption explicitly specified as fallback path, not the normal path | **Closed** |
| **G** Memory verification loop | §9 | `memory.write_candidate` no longer exempt. Memory Gateway writes to `gateway_responses`; task enters `awaiting_verification`; Result Verifier reviews with explicit interpretation table. State transition diagram is unambiguous | **Closed** |
| **H** Classifier calibration acceptance criterion | §10 | Two gates: accuracy + confidence calibration. Explicit 120-sample test set with 10 attack-vector categories. Required thresholds: 40/40 critical caught, ≥95% recall, ≤15% FPR, ≥95% precision at 0.90, ≥90% precision at 0.80, **0 critical misses above either threshold**. Calibration failure behaviors specified for each scenario, including model-profile change → calibration invalidated | **Closed** |
| **I′** PlanInjectionScanner module location | §15 | Placed at `security/plan_injection_scanner.py` | **Closed** |
| **L** Resource limits runtime enforcement | §12 | Pre-dispatch gate + post-dispatch ledger pattern. Six resource types covered (cloud calls, network fetches, context bundle, sandbox RAM, sqlite-vec, chain duration). New status `failed_resource_limit`. Ledger writes to `resource_usage`, `provider_usage`, `gateway_responses` | **Closed** |
| **K** Boot-recovery delegation to Kimi | §14 | Three architectural invariants stated as non-negotiable; five mechanics areas explicitly delegated to Kimi; five non-delegable architectural limits stated. Boundary is clean | **Closed** |
| Touch-up: orphan recovery scope | §13 | Broadened to `session_id != current_session_id` | **Closed** |
| Touch-up: classifier-only embedded_instruction | §11 + §16 | New rule(s) inserted before safe-pass rules. **Documentation inconsistency** — see §3 below | **Closed substantively, needs documentation fix** |
| Qwen binding conditions | §2 | All nine restated as binding | **Closed** |

---

## 2. Core Value Compliance

| Core Value | v1.8 status |
|---|---|
| 1 — Security baked in | **Strengthened.** Atomic commits, capability fail-closed, calibration as security gate, scheduler-stale fail-closed, classifier-only embedded_instruction blocked |
| 2 — Local model in its lane | **Strengthened.** Calibration requirement explicitly conditions the local model's role as security boundary; model swap invalidates calibration |
| 3 — Zero-trust at boundaries | **Strengthened.** Memory verification loop closed (no tool class is verification-exempt); capability re-establishment is identity-validated; privileged task classes have creator allowlist |
| 4 — Build simple | **Held.** No new components; resource gate is single pre-dispatch check; heartbeat is single threshold + fail-closed action; manual restart preferred over automated recovery during scheduler staleness |
| 5 — Queue coordination | **Held.** TaskCommitter atomic write to queue; Scheduler is sole state mutator; non-delegable invariant restated |
| 6 — Sandbox/network separation | **Held and reaffirmed** as non-delegable in §14 |

No Core Value conflicts.

---

## 3. Issues Found in v1.8

### 3.1 Blocking — Sandbox execution duration is uncapped relative to heartbeat threshold

**The conflict.** §6 derives the 120s scheduler-stale threshold as `90s max provider-call hard ceiling + 30s margin`. The heartbeat update points listed in §6 are:

> 4. Immediately before sandbox execution
> 5. Immediately after sandbox execution returns or times out

So the heartbeat is bracketed before/after sandbox execution but **not updated during** it. If a sandbox execution exceeds 120s, the heartbeat goes stale during legitimate operation and the supervisor will fail-closed on a healthy scheduler.

§12 lists "Chain duration: Check timeout/call count → Escalate to `needs_human_input`" as a resource limit, but this is per-chain, not per-sandbox-execution. Nowhere in v1.8 is a per-sandbox-execution duration cap specified. Sandbox RAM is capped at 256 MB; sandbox time is not capped at all.

**Why it matters.** The fail-closed action in §6 is severe: `autonomous_operation_enabled=false`, `shutdown_requested=true`, operator must manually restart. Triggering this on a legitimate long-running sandbox execution is a serious false positive — it converts a working chain into a forced manual-restart and lost work.

**Fix (small).** Specify a per-sandbox-execution duration cap, derived to fit within the heartbeat threshold. Either:

- Cap sandbox execution at ≤60s via Job Object timeout (parallels the cloud-call ceiling and leaves margin), and document it in §2 alongside the existing 256 MB RAM cap; or
- Allow sandbox execution to update the heartbeat from a watchdog thread or via the Job Object's notification callback (more complex; conflicts with the 4-thread cap unless implemented inside the supervisor thread).

The first option preserves Core Value 4 (build simple) and the 4-thread cap. Recommended.

This is a one-paragraph addition. It does not require restructuring the architecture.

### 3.2 Documentation — §11 prose does not match §16 ordered rules table

**The inconsistency.** §11 introduces a rule numbered "5A" with this text:

> Classifier label in {embedded_instruction, tool_request, quarantine, or needs_cloud_review}, regardless of rule hits → quarantined for high-risk artifacts; needs_human_input for ordinary artifacts

But §16 splits this into three rules with different conditions:

| §16 rule | Condition | Decision |
|---|---|---|
| 5A | No rule hit + classifier label = `quarantine` | quarantined |
| 5B | No rule hit + classifier label ∈ {`embedded_instruction`, `tool_request`} + risk_class=high_risk | quarantined |
| 5C | No rule hit + classifier label ∈ {`embedded_instruction`, `tool_request`} + risk_class=ordinary | needs_human_input |

Three differences:
1. §16 5A is narrower (only `quarantine` label), and §16 5B/5C handle `embedded_instruction`/`tool_request` separately by risk class
2. §16 5A/5B/5C all require **no rule hit** — they don't fire when a rule already matched (because Rule 5 in §16 already covers `rule hit + suspicious classifier label → quarantined`)
3. The `needs_cloud_review` label is in §11's list but not in §16 5A/5B/5C — it falls through to Rule 12 (`any unclassified remainder → needs_human_input`), which is consistent with §11's intent but not explicit

The §16 table is the implementable version and is correct. §11 is a prose summary that doesn't match the implementation. An implementer reading §11 alone would build the wrong rule.

**Fix (trivial).** Either remove §11's rule description and reference §16 as the canonical rule set, or rewrite §11 to match §16 verbatim.

### 3.3 Observations — Not blocking, worth recording

These do not require revision but should be on the record:

**a. Triggers 13–14 in §3 partially overlap with Rules 8–9 in §16.** Trigger 13 ("any task lacks testable acceptance criteria") and Trigger 14 ("any task requests capability outside known vocabulary") elevate an artifact to high_risk. Rules 8 and 9 in the scanner table treat schema-field-missing and unsupported-capability-format as `failed`. Since Rules 8/9 fire before any risk-class-dependent rule, the triggers are effectively redundant for those cases. This is belt-and-suspenders, not a defect — but the architect may want to clarify which condition the triggers are meant to catch that Rules 8/9 wouldn't.

**b. Calibration sample size (§10).** 30 benign samples is a small base for a ≤15% FPR threshold (the difference between 4 and 5 false positives is the difference between pass and fail). Acceptable for Phase 1; flag for expansion in Phase 2 or after first calibration drift event.

**c. Cancel-during-call operator UX is unspecified (§5).** The architectural decision is sound: cancel-during-call waits up to the timeout. But the operator-facing experience — what Telegram tells the user when /cancel is sent during an in-flight call — is not specified. This is implementation territory; flag for Kimi.

**d. v1.8 is the closure pass on accumulated specification debt.** Items E, F, G, H, and the §13 broadening have all carried across two or three review cycles. v1.8 closes them. The remaining gap (3.1) is genuinely new — it surfaced as a side effect of the heartbeat threshold derivation in §6, which is itself a v1.8 addition. Worth noting that the panel cycle did its job: blocking items closed, new derivation introduced one new question.