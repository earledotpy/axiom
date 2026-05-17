# AXIOM Proposal v1.1 — Coherence Re-Check

**Evaluator:** Claude Opus 4.7 (Quality and Coherence Evaluator)
**Verdict:** A–J substantively resolved. Four residual coherence items must be clarified before advancement to DeepSeek. These are tightening clarifications, not redesigns — likely a short Architect addendum rather than a v1.2.

---

## 1. Correction to v1 Evaluation

On Item J (Core Value 2 scope), my v1 evaluation was wrong. The Core Values document explicitly lists "classifier, router, **sanitizer**, and embedding engine" as the local model's defined lane. The Architect's framing is correct: sanitization is already in scope. No amendment is required, and I should not have flagged it. The Architect's narrowing rule — that the local model may classify but may not decide whether plans are good or whether to override manifests — is a useful guardrail that should be retained.

I note this directly because the panel's evaluation record should be accurate, not because it changes the proposal.

---

## 2. Resolution Check on A–J

| Item | Status | Note |
|---|---|---|
| A — `approved_for_execution` gate | Resolved | Owner named (Scheduler + Policy Engine), criteria defined, human role correctly bounded |
| B — Drone architecture | Resolved | Single executor + manifests; module map consistent |
| C — Sanitization map | Resolved | Six-source map with placement and mechanism for each |
| D — Permission manifest | Resolved | Schema, storage, double-enforcement point (Scheduler + Tool Gateway), no self-expansion rule |
| E — Verifier integration | Resolved | State machine includes verification states; verifier types and trigger conditions defined |
| F — Read boundaries | Resolved | Role-by-role read/write table + Context Builder as the bundling enforcement point |
| G — Sandbox mechanism | Resolved at coherence level | Windows Job Objects + restricted token via pywin32 named; factual sufficiency correctly deferred to Gemini |
| H — Watchdog | Resolved | Two modes, placement, bounded mutation authority |
| I — Plan checkpoint | Resolved in concept | But see Issue 3 below — the state attachment is unclear |
| J — Core Value 2 | Resolved (my error) | See Section 1 above |

---

## 3. Residual Coherence Issues

### Issue 1 — Terminology drift across sections
Three names appear for what looks like one component:
- Section 3: **Policy Engine** (gate evaluator)
- Section 4 (early): **permission_engine.py** (manifest enforcement)
- Section 14 (consolidated): **permissions.py** (single module)

If these are the same component, unify the name. If they are distinct (e.g., Policy Engine evaluates broader gating rules including resource budget and parent status, while the Permission Engine enforces tool/scope manifests), say so explicitly and reflect it in the module map.

### Issue 2 — State machine treats some states as universal that are conditional
The lifecycle in Section 3 reads as a linear sequence:

```
created → ingress_sanitized → planned → plan_checkpoint_pending → 
plan_checkpoint_passed → approved_for_execution → running → 
awaiting_verification → verified → completed
```

But Section 3's approval criteria say plan checkpoint applies "if task came from Overseer plan." A Drone-level subtask created by a Taskmaster does not have its own plan to checkpoint. Either the state machine has branches (some states are skipped for non-plan-bearing tasks), or every task has to traverse all states with no-op transitions. The proposal should commit to one and show it in the diagram.

### Issue 3 — Plan checkpoint state attachment is ambiguous
This is the most material residual gap.

- Section 11 stores **proposed plans** in a `plan_artifacts` table — separate from the `tasks` table.
- Section 3 includes `plan_checkpoint_pending` and `plan_checkpoint_passed` as **task** states.
- Section 13 lists `checkpoint_id` as a task field.

So which entity carries the checkpoint state — the plan artifact, the Overseer task that produced it, or the child tasks the plan will become? Three different reads are possible:

(a) The Overseer task transitions through `plan_checkpoint_pending → plan_checkpoint_passed`, and only after passing does it commit child tasks to the queue at `created` state. In this read, the child tasks never enter the checkpoint states.

(b) The plan artifact has its own status separate from any task, and `plan_checkpoint_pending` in the task lifecycle is misplaced — it belongs to the artifact lifecycle.

(c) Child tasks are created in `plan_checkpoint_pending` and only advance to `approved_for_execution` after the parent plan checkpoint passes.

Each has different implications for the schema, the scheduler logic, and audit trails. Pick one explicitly.

### Issue 4 — Plan Checkpoint Verifier vs. Verifier — same component?
Section 7 lists the Verifier running after "Overseer plan generation" with cloud verification for "plan coherence, task decomposition quality." Section 11 introduces a **Plan Checkpoint Verifier** with criteria that look identical (goal preservation, role separation, queue compliance, etc.). The module map has only `verifier.py`.

If they are the same component operating in different modes, state that. If they are distinct, the module map needs to reflect the second one. As written, the reader can't tell whether the Plan Checkpoint Verifier is a configuration of the Verifier or a separate role.

---

## 4. Out of Scope for This Re-Check

These are flagged for downstream panel members, not for the Architect to address now:

- **Sandbox mechanism factual sufficiency** — Gemini's call. The Architect correctly named the mechanism and deferred the factual question.
- **RAM impact of the consolidated runtime** (manifests, context bundles, plan artifacts table, watchdog overhead) — Qwen's call. Worth noting that v1.1 added persistent state machinery that v1 didn't have; whether this fits the 2.0–2.3 GB headroom is a feasibility ruling.
- **Whether the verifier's frequency (after every state-changing Drone action + Overseer plan + Taskmaster subtask + final completion) is sustainable on free-tier API budgets** — also Qwen, partly Gemini.
- **Adversarial vectors** — DeepSeek's job, not mine.

---

## 5. Recommendation

**Conditional advancement.** The Architect should produce a short addendum (not a full v1.2) addressing Issues 1–4. Issue 3 is the only one that is structurally load-bearing; the other three are tightening. Once those four points are clarified, the proposal can advance to DeepSeek.

The architectural spine is now coherent enough that DeepSeek's adversarial work will produce useful results. Holding the proposal further on coherence grounds beyond these four items would be over-policing — the remaining design questions are better answered by the Critic, the Arbiter, and the Constraints Reviewer than by another coherence pass.