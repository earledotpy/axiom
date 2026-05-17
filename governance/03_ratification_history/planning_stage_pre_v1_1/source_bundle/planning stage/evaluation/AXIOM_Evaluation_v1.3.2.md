# Synthesis — AXIOM Panel Review of Proposal v1.3.1 + Addendum v1.3.2

**Evaluator role.** Synthesizing outputs from Critic (DeepSeek), Arbiter (Gemini), and Constraints Reviewer (Qwen), against my prior coherence evaluation.

---

## Verdict

**Return to Architect. Cannot proceed to implementation planning.**

The Arbiter and Constraints Reviewer have approved the technical and feasibility surface. My prior N1–N3 coherence gaps appear resolved in the v1.3.2 addendum (per Qwen's notes on plan_artifacts status migration, universal PolicyEngine gate, and role-scoped write surfaces). However, DeepSeek's critique exposes a recurring architectural anti-pattern that v1.3.2 has not addressed: **multiple security-critical components exist as filenames, manifest entries, and test names without specified mechanism**. This is the same "labeled box with no contents" failure that the Legacy Reference warned against. It cannot proceed to Kimi.

---

## Part 1 — Objections That Are Valid and Must Be Resolved

### Tier A — Blocking. Direct architectural revision required.

| # | Objection | Why it is valid |
|---|---|---|
| **O1+O5** | PlanInjectionScanner has no specified mechanism, detection model, verdict schema, or owner — *and* its role-vs-deterministic-component status contradicts itself (manifest exists, but F5 says deterministic components don't have manifests) | This is the sole injection defense between cloud Goal Planner output and the task queue. The Legacy Reference identifies prompt injection via task queue as the unresolved Phase 9 failure. CV1 ("security baked in") cannot hold while the primary injection defense is a name. The role/deterministic ambiguity means Kimi cannot determine whether to write a role module or a utility — the two paths produce different security properties. |
| **O4** | `core/resource_limits.py` exists only as a filename and a test name. No runtime tracking mechanism, no budget estimator, no overrun behavior specified | Constraints Register documents Groq exhaustion as a *demonstrated* failure mode. A Tool Executor authorized for `max_model_calls: 1` that issues 3 calls has no specified interceptor. CV1 + Constraints budget conditions both depend on this being real, not nominal. |
| **O8** | Classifier validation has no accuracy threshold, no test set specification, no remediation path when the classifier is unreliable | The local-model classifier is the Phase 1 sanitizer for ingress content. Without a validation criterion, "the classifier validated successfully" means nothing. Same failure pattern as O1 and O4 — infrastructure named, contents undefined. |
| **O6** | No transactional boundary specified around TaskCommitter; no failure-handling specified for any deterministic-chain step | TaskCommitter inserting child tasks without a single SQLite transaction means partial commits leave orphaned subtrees in the queue at `created`. Scheduler will pick them up. CV5 (queue-mediated coordination) requires queue integrity. This is concrete and small to fix — wrap TaskCommitter inserts in a single transaction, specify rollback on any insert failure — but it must be in the architecture before Kimi can write `test_task_committer_atomicity.py`. |
| **O7** | Boot sequence and startup recovery are referenced by `test_boot_sequence.py` and `test_startup_recovery_rules.py` but not specified anywhere in v1.3.1/v1.3.2 | The v1.1 startup watchdog logic cannot apply unchanged because the status space was substantially revised (`approved_for_execution` removed, `cancelled` added, plan_artifact statuses introduced). Concretely missing: how `policy_approved=1` tasks from a crashed session are handled, how partial task trees from a mid-chain crash are detected, how the Scheduler distinguishes resume from cold start. Tests exist but the spec they test does not. |
| **O9** | Memory Gateway dedup responses are not routed to the Result Verifier | A Tool Executor's `memory.write_candidate` may be silently deduplicated by the gateway. The Result Verifier sees only the Tool Executor's `output_payload`, not the gateway's "already exists" response. This makes verification of memory-write tasks underspecified — is silent dedup a success or a failure? Concrete fix: extend the context bundle delivered to the Verifier to include gateway-level response data, or add a `gateway_response` field on the task row. |
| **O10** | `operator_control` task creation path has no specified privileged-path enforcement | If `operator_control` is just another manifest, a compromised Task Planner with `task.create` capability via TaskCommitter could spoof a control task with `priority=interrupt`. CV3 (zero-trust at boundaries) requires that the human-operator-only commands be exclusively initiable by the Telegram Gateway. The current architecture treats the manifest as the constraint — but the manifest doesn't constrain *who creates the task*, only what the task can do once created. |

### Tier B — Valid in part. Specific aspects require revision; framing partially overruled.

| # | Valid aspect | Overruled aspect | Reason for overruling |
|---|---|---|---|
| **O2** | Cloud call timeout must be specified. Operator-feedback path on cancel ack must be specified. Duplicate `/cancel` commands must be deduplicated, not stacked. | The cooperative-cancellation model itself. | Gemini's Arbiter ruling §2 verified that cooperative cancellation at the next Scheduler tick is the factually correct model under Python's GIL and asyncio. Forceful preemption risks SQLite corruption. The architectural choice stands; the operational specifications around it are still missing. |
| **O3** | Scheduler exception-handling policy and failure-visibility path must be specified (last-action log, crash signal visible to next session start). | The "split the Scheduler" architectural request. | CV4 ("build simple, prove the concept, iterate"). Adding an external watchdog process and splitting Scheduler responsibilities now is speculative complexity. The Scheduler's responsibility count is high but the responsibilities are all sequencing-related — they belong together. The right Phase 1 mitigation is making Scheduler crashes *visible*, not preventing them through structural separation. |

---

## Part 2 — Objections Overruled

| # | Aspect overruled | Authority |
|---|---|---|
| O2 | Cooperative cancellation as architectural model | Arbiter ruling §2 — binding factual ruling |
| O3 | Architectural separation of Scheduler responsibilities | Core Value 4 — premature complexity for speculative benefit |

No factual claim in the proposal was contradicted by Gemini. No feasibility ruling from Qwen blocks the proposal — Qwen's verdict is **APPROVED with 8 binding conditions**, all of which are operational guardrails rather than redesign requirements.

---

## Part 3 — Required Revisions for v1.4

The Architect must produce v1.4 addressing the following. Each item is small in isolation; together they are not optional.

1. **PlanInjectionScanner — define it.** Specify (a) mechanism: rule-based, local-model classifier, or hybrid; (b) detection patterns covered in Phase 1; (c) verdict schema (boolean + label set + confidence, or simpler); (d) module location (`security/` is the natural home given `sanitizer.py` and `classifier_validation.py` already live there); (e) resolve the role-vs-deterministic contradiction by picking one. *Recommendation: deterministic component in `security/plan_injection_scanner.py`, no role manifest, Scheduler calls it directly. Drop `internal_plan_injection_scan.json`.*

2. **Classifier validation — define the contract.** Accuracy threshold for "trusted as boundary" (e.g., ≥X% on the injection test set). Test set composition: who curates, how many samples, attack vectors covered. Behavior when `classifier_validation_status` indicates the classifier is below threshold (refuse to start? degraded mode? cloud fallback with budget impact?).

3. **Resource limits — operationalize.** How tracking happens at runtime (per-task counter? session counter? both?). Who produces the budget estimate (cloud planner output is *unvalidated*; an estimator helper deserves its own component). What happens on overrun mid-execution. How `resource_limits.py` integrates with `provider_usage` in persistence. Carries Qwen's binding condition #7 (2× safety margin, log actuals).

4. **TaskCommitter transactional boundary.** Wrap the child-task insert sequence in a single SQLite transaction. Specify rollback behavior on any failure (constraint violation, manifest binder failure, schema violation). Add a single sentence per other deterministic-chain step (PlanInjectionScanner exception, ResultVerifier failure, ManifestBinder failure) stating where the parent task transitions to.

5. **Boot sequence + startup recovery.** Module initialization order. Schema verification/migration approach. Resume-vs-cold-start detection. Handling of `running` tasks from crashed session. Handling of `policy_approved=1` tasks from crashed session. Handling of partial task trees (depends on item 4). This makes `test_boot_sequence.py` and `test_startup_recovery_rules.py` specifiable.

6. **Memory Gateway response routing.** Specify how gateway-level responses (dedup outcome, write success/silent-skip) are surfaced to the Result Verifier. Either extend context bundle, add a `gateway_response` column, or route through an existing audit mechanism.

7. **operator_control privileged path.** State that `operator_control` task creation is restricted to the Telegram Gateway component, not enforced by manifest but by the component identity of the creator. Specify the enforcement mechanism (e.g., TaskCommitter rejects `task_class=operator_control` from any caller other than `telegram_gateway.py`, verified by import-graph test). This may require a per-task-class creator allowlist.

8. **Cancellation operational specs.** Cloud call timeout (recommend 30s for Cerebras, with cascade fallback). Telegram acknowledgment pattern: bot replies "cancel queued; will take effect after current cloud call completes (up to N seconds)" so the human knows the difference between "ignored" and "pending". Deduplicate repeated `/cancel_current_chain` against the same active task — second issuance is a no-op with status reply.

9. **Scheduler failure visibility (Tier B from O3).** Specify Scheduler-loop exception handling: top-level try/except, write a `session_events` row marking abnormal exit, ensure the Telegram Gateway can detect Scheduler liveness via heartbeat row updated each tick. This does not split the Scheduler — it makes its silent death detectable.

**Carry into v1.4:**
- Gemini's WAL caveat: SQLite connection must be configured `PRAGMA journal_mode=WAL` with explicit timeout (5–10s).
- Qwen's 8 binding conditions, restated in v1.4 as binding implementation constraints.

---

## Part 4 — Routing

**Status:** Proposal does not advance to Kimi.

**Next step:** Architect produces v1.4 addressing items 1–9 above. v1.4 returns to the panel for re-review, but the cycle can be abbreviated:
- Re-evaluation by me: targeted to items 1–9 only.
- Re-critique by DeepSeek: targeted to whether items 1–9 resolve objections O1, O2-specifics, O3-specifics, O4, O5, O6, O7, O8, O9, O10.
- Arbiter and Constraints: only re-engage if v1.4 introduces new technical claims or new runtime components.

**Estimated v1.4 surface:** ~2–3 pages of additions. None of these items requires architectural redesign; all are specifications for components already named.

**One pattern observation for the Architect:** v1.3.1 and v1.3.2 introduced multiple components by name and test, without contents. This pattern (PlanInjectionScanner, resource_limits, classifier_validation) creates the appearance of completeness while deferring the load-bearing design work. v1.4 should not introduce any new named component without specifying its mechanism in the same revision. If a component is too large to specify in a half-page, it deserves its own section, not a filename.