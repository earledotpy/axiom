# Coherence Evaluation — AXIOM Proposal v1.3

**Evaluator role.** This evaluation reviews v1.3 against the v1.2 blocking issues it claims to resolve, against the Core Values, and for new coherence problems introduced by the revisions.

---

## Summary verdict

The proposal substantively resolves most of the eight blocking issues. The architectural spine is sound and the deterministic-trust pattern (Scanner → Verifier checkpoint → Committer → Binder) is the right shape for CV1 and CV3.

However, v1.3 introduces **one hard internal contradiction** and **four smaller coherence gaps** that must be resolved before the proposal can move to DeepSeek targeted re-check. This is tighten-and-clarify work, not redesign.

**Recommendation: Return to Architect for a v1.3.1 patch. Do not advance to Critic.**

---

## What holds

**Issue 1 — Plan injection scan owner.** Ownership assigned to a single component. Verdict triple-stored (`plan_artifacts`, `security_events`, `plan_checkpoints`). Hard gate (`injection_scan_status = 'passed'` required before checkpoint verification) is enforceable and aligns with CV1.

**Issue 2 — Manifest creation flow.** The trust-boundary statement — *"The trusted author of a manifest is deterministic AXIOM code, not model output"* — is exactly the pattern CV3 requires. Capability requests vs. permission grants is the correct split. Manifest immutability + same-transaction insert closes the obvious race.

**Issue 3 — Verifier write scope.** The advisory/applied separation between `recommended_next_state` and `tasks.status` is clean. The contract holds.

**Issue 4 — No direct role-to-role calls.** Static import-graph test is the right primary enforcement. Combined with the role_executor convention, this makes CV5 mechanically testable.

**Issue 7 — Plan/Subtask Committers.** Deterministic, no model calls, no plan content alteration. The committer pattern correctly serves as the trust gate between verified artifact and queued task.

**Issue 8 — Single running task invariant.** Triple enforcement (DB partial unique index + `BEGIN IMMEDIATE` transaction + watchdog assertion) is excellent. The SQL is correct: a unique index on `status` filtered to `WHERE status = 'running'` does prevent multi-row 'running' states.

**Secondary issues 10–13.** Memory dedup at 0.92 cosine matches the legacy consensus. Boot sequence is explicit and gates autonomous operation correctly on classifier and sandbox validation. Recovery semantics are deterministic. The runtime/harness split between `sanitizer.py` and `classifier_validation.py` is correct.

---

## What fails

### F1. Hard contradiction — "Scheduler alone mutates task state" vs. operator_control manifest

This is the blocking issue.

Section 16 states: *"Scheduler alone mutates task state."*

Section 7's `operator_control.json` grants:
```
"allowed_write_fields": [
  "tasks.cancel_requested",
  "tasks.status",                 ← direct mutation of task state
  ...
],
"write_constraints": {
  "tasks.status": ["cancelled"]
}
```

The operator_control role can write `tasks.status = 'cancelled'` directly. That violates the Section 16 invariant. Two parts of the same proposal disagree.

**Consequence.** The acceptance test `test_operator_control_manifest.py` and the (currently unspecified) test for the "Scheduler-only state authority" cannot both pass as written. CV5's "all coordination through the task queue" depends on the scheduler being the sole sequencer of state — an out-of-band cancellation path muddies the audit semantics.

**Resolution path.** Operator_control should write only `tasks.cancel_requested = true` (it already has that capability). The Scheduler observes the flag at its next promotion cycle and transitions the running task to `cancelled` itself. Remove `tasks.status` from operator_control's `allowed_write_fields`. Remove the `write_constraints.tasks.status` clause. Cancellation becomes a queue-mediated request, fully consistent with CV5.

This also makes the `priority: "interrupt"` claim cleaner: "interrupt" means the cancel_requested flag is observed at the *next* scheduler tick, not that it preempts a mid-flight task — which on a sequential single-task runtime it can't anyway.

### F2. Policy Engine referenced but absent from module map

The Policy Engine appears in:
- Section 3 flow: *"Policy Engine verifies manifest before approved_for_execution"*
- Section 4: *"Scheduler must map verifier output through policy"*
- Implicitly throughout

The module map (Section 15) has no `policy_engine.py`. The closest candidates are `core/permissions.py` (probably handles manifest verification) and `core/state_machine.py` (probably handles transition policy).

**Consequence.** Implementation cannot begin without knowing where this code lives. Kimi cannot produce an implementation plan from an architecture that names a component the architecture doesn't include.

**Resolution path.** Either (a) add `core/policy_engine.py` to the module map and define its responsibilities, or (b) explicitly state that "Policy Engine" is a logical name for the combined responsibilities of `permissions.py` (manifest verification) and `state_machine.py` (transition policy), and rewrite the flows to use the actual module names.

### F3. "approved_for_execution" not reconciled with the documented task state space

Section 3's flow ends with *"Policy Engine verifies manifest before approved_for_execution."* The recovery rules in Section 12 enumerate task states (`running`, `cancelled`, `quarantined`, `failed`, `awaiting_verification`, `retry_pending`, `blocked`) and Issue 7 specifies tasks are inserted at `status = 'created'`. There is no `approved_for_execution` state in this list.

**Consequence.** Either there's an undocumented status value, or `approved_for_execution` is a separate boolean flag (e.g., `tasks.policy_approved`), or the term is loose phrasing. Without resolution, the state machine test specification is incomplete.

**Resolution path.** Pick one: (a) add `approved_for_execution` as an explicit task status between `created` and `pending`, (b) introduce `tasks.policy_approved` as a boolean flag the Scheduler reads before promoting `created` → `running`, or (c) drop the term and clarify that the Policy Engine's verification happens in the same transaction as task insert, so `created` already implies policy-approved.

### F4. Issue 5 capability count ambiguity

Section 6: *"Tool Executor may write its own result/error fields, plus one of the explicitly whitelisted shared-state write candidates, only if granted by the bound manifest."*

"Plus one of" reads as "exactly one." But the four candidates serve different purposes (memory writes, artifact references, security event logs, tool invocation logs) — most non-trivial Tool Executor tasks would need at least `tool_invocation.append` plus one other.

**Consequence.** If "exactly one" is intended, most useful manifests can't be expressed. If "any subset" is intended, the wording understates the surface area Qwen needs to evaluate for RAM and write-amplification effects.

**Resolution path.** Reword as: *"Tool Executor may write its own result/error fields, plus any subset of the explicitly whitelisted shared-state write candidates, only those subset members granted by the bound manifest."* Or, if the intent is one-per-task, state that explicitly and explain the rationale.

### F5. Orchestrator of the deterministic chain unspecified

Several deterministic transitions are described, but no module owns the orchestration:
- Who calls `PlanInjectionScanner` after a Planner produces a plan artifact?
- Who calls `ResultVerifier` in checkpoint mode after the scan passes?
- Who calls `PlanCommitter` after the checkpoint passes?

The `role_executor.py` is described as *"the only component that may instantiate or call role modules"* — but `PlanInjectionScanner`, `PlanCommitter`, and `ManifestBinder` are deterministic components, not role modules. So role_executor isn't necessarily the orchestrator.

**Consequence.** The trust chain has no named driver. Implementation is ambiguous.

**Resolution path.** State explicitly that the Scheduler advances plan_artifacts through their deterministic state transitions (`proposed` → `injection_scanned` → `checkpoint_verified` → `committed`), invoking each deterministic component in turn. Or designate a separate `core/orchestrator.py`. Either is fine; the silence is the problem.

---

## Minor coherence notes (non-blocking)

- **Runtime "dispatch guard" framing (Issue 4).** The runtime guard is enforced by code organization plus the static test, not by a runtime mechanism. Python can't actually prevent a misbehaving module from importing a sibling. Reframe as: *"The static import-graph test is the enforcement; the role_executor convention is the structure that makes the test meaningful."* Honest framing reduces false confidence.

- **`/resume` semantics.** The operator_control manifest allows writing `sessions.pause_requested`. Resume implies setting it back to false. Either spell that out, or introduce a separate `sessions.resume_requested` flag.

- **End-to-end deterministic chain not consolidated.** The flow `Planner artifact → PlanInjectionScanner → Verifier (checkpoint mode) → PlanCommitter → ManifestBinder → Scheduler promote` is reconstructable from the proposal but never shown in one place. A single integrated diagram would help Kimi's implementation planning.

---

## Core Values check

| Value | Status | Note |
|---|---|---|
| CV1 — Security baked in | Holds | Scan-before-commit, classifier validation gates, immutable manifests. |
| CV2 — Local model in its lane | Holds | Local classifier confined to sanitization; cognitive work routing not contradicted. |
| CV3 — Zero-trust at boundaries | **Reservations** | F1 (operator_control) creates an out-of-band state mutation path. Otherwise sound. |
| CV4 — Build simple, iterate | Holds | Phase 1 write ceiling, immutable manifests, sequential runtime. v1.3 tightens, doesn't expand. |
| CV5 — Coordination via queue | **Reservations** | Same F1 issue — operator interrupt currently bypasses the scheduler. |
| CV6 — Sandbox/network separation | Holds | Internal scan manifest forbids both; sandbox isolation gated at boot. |

CV3 and CV5 reservations resolve cleanly if F1 is addressed by routing operator cancellation through `cancel_requested`.

---

## What must be resolved before the proposal can proceed

The Architect must produce a v1.3.1 patch resolving:

1. **F1 (blocking)** — Reconcile Section 16's "Scheduler alone mutates task state" with the operator_control manifest. Recommended fix: remove `tasks.status` from operator_control's allowed_write_fields; let the Scheduler observe `cancel_requested` and transition.
2. **F2 (blocking)** — Resolve the Policy Engine references against the module map. Either add the module or rename the references.
3. **F3 (blocking)** — Reconcile `approved_for_execution` with the documented task state space.
4. **F4** — Disambiguate "plus one of" in Issue 5.
5. **F5** — Name the orchestrator of the deterministic-chain transitions.

Items F1–F3 are coherence failures: two parts of the proposal say things that cannot both be true. F4–F5 are clarifications, but each makes a downstream test or implementation step non-executable.

Once these are resolved, the proposal can advance to DeepSeek for targeted re-check on the same issues, then Qwen and Gemini if any of the changes affect their domains (F2's Policy Engine module decision may affect RAM accounting; the others should not).