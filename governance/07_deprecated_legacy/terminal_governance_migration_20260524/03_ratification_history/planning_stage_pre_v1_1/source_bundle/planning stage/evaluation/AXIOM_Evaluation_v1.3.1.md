# Coherence Evaluation — AXIOM Proposal v1.3.1

**Evaluator role.** This evaluation reviews v1.3.1 against the F1–F5 blocking issues from the v1.3 evaluation, against the Core Values, and for new coherence problems introduced by the patch.

---

## Summary verdict

v1.3.1 cleanly resolves all five blocking issues from v1.3. The architectural spine is unchanged and the resolutions are mechanical and well-bounded — no new design surface was opened. The patch is tighter than v1.3 and the core invariants stated in Section 12 are now internally consistent.

Three new minor coherence gaps were introduced or exposed by the patch. None are blocking individually; none touch the architectural spine; all are in the category of "Kimi will hit this when writing the implementation plan unless the Architect spells it out first."

**Recommendation: Advance to DeepSeek for targeted F1–F5 re-check.** In parallel, the Architect should produce a brief addendum addressing the three new notes below before the Synthesis step, so the proposal that goes to Kimi is fully implementable.

---

## What holds — F1–F5 resolutions

**F1 — Scheduler-only state mutation restored.** Clean. `tasks.status` is removed from `operator_control.allowed_write_fields` and explicitly listed in `forbidden_writes`. The intent-flag pattern (`cancel_requested`, `pause_requested`, `shutdown_requested`) routes operator interrupts through Scheduler-mediated state, restoring CV3 and CV5. The reframing of `interrupt` priority as "prioritized handling at the next Scheduler tick" rather than mid-flight preemption is honest and correct for a sequential single-task runtime.

**F2 — Policy Engine added to module map.** Clean. `core/policy_engine.py` is a concrete module with defined responsibilities distinct from `permissions.py` (manifest capability enforcement) and `state_machine.py` (legal transitions). The decision to make it a separate module rather than fold it into the two adjacent modules is justified — the execution gate is load-bearing enough to deserve its own file. The thirteen Policy Engine checks listed give Kimi a concrete implementation surface.

**F3 — `approved_for_execution` reconciled.** Clean. Replaced as a task status with three explicit fields (`policy_approved`, `policy_approved_at`, `policy_decision_id`) plus a `policy_decisions` audit table. The task promotion flow `created → policy_approved=1 → running` is unambiguous, and the schema patch is concrete.

**F4 — Shared-state write scope clarified.** Clean. "Plus one of" replaced with "any explicitly granted subset" of the four-item Phase 1 whitelist. The valid/invalid manifest examples make the rule testable. The ManifestBinder enforcement ceiling preserves CV3.

**F5 — Deterministic chain orchestrator named.** Clean. Scheduler is the orchestrator. The decision *not* to add `core/orchestrator.py` is correct under CV4 — separating sequencing responsibility across two modules would weaken "Scheduler owns sequencing." The role/deterministic-component split (`role_executor.py` calls role modules only; Scheduler calls deterministic components directly) is the right boundary and is testable.

The minor v1.3 notes are also addressed:
- `/resume` semantics: spelled out as `pause_requested = false`. Clear.
- Runtime dispatch guard: honestly reframed as "static import-graph test is the enforcement." Good.
- End-to-end chain: consolidated in Section 9.

---

## What fails or is newly ambiguous

These are new gaps exposed by the patch. None reach the threshold of F1–F3-class hard contradiction, but two are sufficient to make Kimi's implementation plan ambiguous.

### N1. Planning-specific statuses don't reconcile with the consolidated chain

Section 5 lists planning-specific statuses (`plan_artifact_created`, `plan_injection_scan_pending`, `plan_injection_scan_passed`, `plan_checkpoint_pending`, `plan_checkpoint_passed`, `child_tasks_committed`, plus subtask variants) and says they apply to planning tasks.

But the consolidated chain in Section 9 never shows the planning task transitioning through these statuses. It shows the Scheduler creating a *separate* checkpoint verification task — meaning the verification status lives on a different task. So which task carries `plan_injection_scan_passed`? The planning task that produced the artifact, or the artifact itself, or the verification task?

**Consequence.** `tests/test_state_machine_branches.py` and any planning-task-status assertion become unspecifiable until the locus is named.

**Resolution path.** State explicitly whether these are (a) sub-states of `running` for the planning task, (b) statuses on `plan_artifacts` rows rather than tasks, or (c) statuses on the verification task. Pick one and update the chain in Section 9 to show the transitions on the right entity.

### N2. The Scheduler-created checkpoint verification task bypasses the PolicyEngine path — or does it?

Section 9 step 9: *"Scheduler creates checkpoint verification task."* Section 9 then jumps directly to step 10: *"RoleExecutor invokes ResultVerifier."* No PolicyEngine call appears between task creation and role invocation for the verification task — but for the parent goal-planning task, PolicyEngine approval was required before promotion to `running`.

Either:
- (a) Scheduler-created tasks go through PolicyEngine like any other task, and the chain just elides it. Then the elision should be removed, because the test specification (`test_policy_engine_gate.py`) needs to cover Scheduler-created tasks.
- (b) Scheduler-created internal tasks are pre-approved by virtue of being created by trusted code, and skip PolicyEngine. Then this is a privileged path that violates the otherwise uniform "every task goes through PolicyEngine" invariant, and it must be explicit.

**Consequence.** The Policy Engine gate is either universal or it isn't. If it isn't, the carve-out needs documentation, a justification under CV3, and a test.

**Resolution path.** State explicitly. Recommendation: keep PolicyEngine universal — verification tasks have manifests too, and the marginal cost of running them through the gate preserves the simpler invariant under CV4.

### N3. Verifier write scope sits outside the F4 whitelist without explanation

The Phase 1 shared-state write candidates listed in Section 6 are the four Tool-Executor candidates: `memory.write_candidate`, `artifact.create_reference`, `security_event.append`, `tool_invocation.append`. But Section 9 step 11 has the ResultVerifier writing a `verification_results` row — which is not on that list.

The list `tests/test_verifier_write_scope.py` exists in the module map, suggesting the design intent is "ResultVerifier has its own role-specific manifest write fields, separate from the Tool Executor whitelist." That's coherent, but the proposal doesn't make the pattern explicit. A reader could reasonably conclude that the four-item whitelist is the *complete* shared-state write surface, when in fact it's the Tool-Executor-specific surface.

**Consequence.** Kimi cannot write `test_shared_state_write_subset.py` correctly without knowing whether the whitelist is global or role-scoped, and the two test files (`test_shared_state_write_subset.py` and `test_verifier_write_scope.py`) can't be reconciled without it.

**Resolution path.** One sentence: *"The Phase 1 shared-state write candidates in Section 6 are the Tool Executor role's allowed surface. Other roles (ResultVerifier, GoalPlanner, TaskPlanner) have role-specific write surfaces defined in their own manifests."* Or, alternatively, generalize the whitelist to a per-role table.

---

## Minor non-blocking notes

- **Status-space additions.** Section 5 lists `verified` and `completed` as distinct allowed statuses. The relationship between them isn't stated — is `verified` a transient state before `completed`, or are they alternate terminal states for verified-vs-unverified tasks? Worth a sentence, but doesn't block.

- **Shutdown irrevocability.** `sessions.shutdown_requested.allowed_values: [true]` means once requested, the flag cannot be cleared via the same write path. This may be intentional (shutdown is one-way), but it should be stated. Otherwise the operator who fat-fingers `/shutdown_after_current` has no documented recovery.

---

## Core Values check

| Value | Status | Note |
|---|---|---|
| CV1 — Security baked in | Holds | PolicyEngine as concrete gate strengthens the position. |
| CV2 — Local model in its lane | Holds | Patch does not affect routing model boundaries. |
| CV3 — Zero-trust at boundaries | **Holds** (was reservations) | F1 resolved. operator_control writes only intent flags it owns. |
| CV4 — Build simple, iterate | Holds | Section 7's refusal to add `core/orchestrator.py` is the correct CV4 call. |
| CV5 — Coordination via shared state | **Holds** (was reservations) | Operator interrupt now goes through `cancel_requested` flag observed by Scheduler, not direct state mutation. |
| CV6 — Sandbox/network separation | Holds | operator_control manifest explicitly forbids both. |

The two CV3/CV5 reservations from v1.3 are resolved. No new conflicts.

---

## What must be resolved before the proposal can proceed to implementation planning

1. **N1 (blocking for Kimi)** — Pin the locus of the planning-specific statuses (planning task, plan_artifact, or verification task) and update Section 9's flow to show where they apply.
2. **N2 (blocking for Kimi)** — State whether Scheduler-created internal tasks (verification, internal scan) traverse the PolicyEngine gate. Recommendation: yes; preserve the universal invariant.
3. **N3 (blocking for Kimi)** — Clarify that the four-item Section 6 whitelist is the Tool Executor surface, not a global ceiling, and that other roles have role-scoped write surfaces.

These are all tighten-and-clarify; none require redesign. The Architect can resolve all three in a v1.3.2 addendum of perhaps half a page.