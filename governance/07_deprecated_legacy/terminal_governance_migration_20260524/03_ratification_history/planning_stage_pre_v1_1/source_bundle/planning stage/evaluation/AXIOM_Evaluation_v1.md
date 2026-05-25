# AXIOM Proposal v1 — Coherence Evaluation

**Evaluator:** Claude Opus 4.7 (Quality and Coherence Evaluator)
**Proposal:** Chief Architect Initial Ground-Up Architecture Proposal
**Verdict:** Sound foundation, but cannot proceed as-is. Ten unresolved issues must be addressed before panel approval.

---

## 1. What Holds

The proposal's structural spine is internally consistent and aligns with Core Values:

- **Sequential execution + logical 3-tier hierarchy** is coherent with the 2.0–2.3 GB headroom and directly implements Core Value 4 (simple first). Rejection of parallel Phase 1 is correctly justified by the Constraints Register.
- **SQLite-backed task queue as sole coordination channel** directly enforces Core Value 5. The "agents do not call agents" rule is stated as an architectural invariant, not a guideline.
- **Sandbox/network separation as a hard boundary** is stated in Section 4 and Section 7. Aligns with Core Value 6.
- **Provider-agnostic Model Gateway with usage logging** is a defensible response to the legacy Groq exhaustion. Tension 3's recommendation to limit to three provider states (available / rate_limited / failed) keeps the simplicity discipline intact.
- **Memory dedup at insert time** correctly addresses the legacy duplicate-entry failure rather than deferring it to cleanup.
- **Deferral of service mode, framework choice, and full daemon autonomy** is consistent with Core Value 4.
- **Local/cloud split** broadly respects Core Value 2 (with one open question — see Issue 10).

The Phase 1 module decomposition in Section 9 is a reasonable starting point, though some elements need clarification (see below).

---

## 2. What Fails — Internal Coherence Issues

### Issue 1 — The `approved_for_execution` state is undefined
The state machine in Section 2 includes `approved_for_execution`, but the proposal never specifies who or what produces approval. Options not adjudicated:
- Human-in-the-loop approval (contradicts autonomous operation)
- Verifier pre-check (Tension 1 hints at this but doesn't commit)
- Automatic transition (then the state is meaningless)

**Consequence:** The queue lifecycle has a gate with no gatekeeper. This is the kind of ambiguity that becomes a Phase 9 retrofit later.

### Issue 2 — Drone architecture is internally inconsistent
- Section 1 defines a single Drone role.
- Section 8 references "Code Drone" and "Web Drone" as distinct components.
- Section 9 has only `agents/drone.py`.

The proposal must commit to either (a) one Drone executor with permission-scoped tool manifests, or (b) multiple typed Drone classes. These have different module structures, different permission enforcement points, and different test surfaces.

### Issue 3 — Sanitization scope is underspecified
The proposal mentions sanitization in four places with non-overlapping framings:
- Section 2: "All writes pass through sanitizer" (queue boundary, all-or-nothing)
- Section 4: Local model performs sanitization (process-level)
- Section 7: Prompt injection labeling at write time (external content only)
- State machine: `created → sanitized` (per-task transition)

These are not the same thing. The proposal must explicitly map: human Telegram input, Overseer-generated subtasks, fetched external content, and tool outputs — each to a sanitization mechanism and placement.

### Issue 4 — The permission manifest is referenced but never defined
Section 7 invokes a "Permission manifest" as the enforcement mechanism for Agent → Tool boundaries. This is the load-bearing artifact for zero-trust, yet it has no schema, storage location, or enforcement point in the proposal. **This is a Core Value 3 gap, not a documentation gap.** Without a defined manifest, "explicit tool scope" is aspirational.

### Issue 5 — Verifier role is incompletely integrated
The state `awaiting_verification` exists. Section 11 Tension 1 acknowledges three options for verifier placement and the Architect's recommendation is "verifier after every state-changing Drone action." But this recommendation isn't reflected back into the state machine, the module list, or the acceptance criteria. The reader cannot tell whether verification is part of the approved Phase 1 scope or a Tension still open for panel decision.

### Issue 6 — Read-access boundaries are not specified
Core Value 3 requires that *no agent reads another agent's full context*. Section 2 carefully defines write boundaries but is silent on read boundaries. Without read-side scoping, a Drone could query the full task table and effectively reconstruct the task tree, defeating the zero-trust intent. Write-side enforcement alone is insufficient.

### Issue 7 — Sandbox isolation mechanism is named but not specified
The proposal correctly states sandbox cannot reach network. It does not state *how*. The Legacy Reference already documents that subprocess.Popen does not provide isolation on Windows, and that Windows Job Objects + restricted token (pywin32) are the established research finding. The proposal must either commit to a mechanism or explicitly defer to a follow-up sub-proposal — but it cannot leave this open while claiming Phase 1 acceptance.

This conflicts directly with **Core Value 1**: security baked in, not bolted on. An undefined sandbox mechanism in the architecture is the bolted-on pattern.

### Issue 8 — Watchdog is required but not architected
Section 5 lists Watchdog as required and Section 10 makes crash recovery an acceptance criterion. The proposal does not specify: where it runs (separate thread? scheduler startup hook? separate process?), what triggers it (startup-only? periodic?), and what authority it has to mutate task state.

### Issue 9 — Overseer task tree has no checkpoint
The Legacy Reference explicitly records pre-rebuild research consensus that "Overseer decomposition reliability is the acknowledged weakest link — a verification/checker step before committing a task tree is recommended." The proposal does not address this. The Overseer creates a task tree that flows directly into the queue. A miscomposed plan from the Overseer becomes the system's reality.

This is a coherence problem because the proposal claims to apply legacy research findings (Section 4 invokes the local-model lane finding; Section 6 invokes the Groq finding) but selectively omits this one without justification.

---

## 3. Conflicts with Core Values

### Open Question — Core Value 2 (Local model stays in its lane)
The Core Value defines the local model's lane as "routing, private data, and embeddings." The proposal extends this to include **sanitization**. The Architect's framing is defensible — sanitization can be characterized as classification, which is adjacent to routing — but this is a scope expansion that should be made explicit, not folded in tacitly.

**Required action:** Either (a) Architect explicitly justifies sanitization as routing-class work and the panel affirms, or (b) this triggers a Core Value 2 amendment under the Charter's process.

This is not a fatal conflict — it's a values-interpretation question that should be surfaced rather than resolved by silent inclusion.

### Soft Tension — Core Value 4 (Build simple)
Section 9's module decomposition lists ~25 distinct modules. Several may be over-decomposed for "minimum viable" — e.g., separate `prompt_injection_labels.py` from `sanitizer.py`, or `state_machine.py` distinct from `scheduler.py`. The Architect labels this "architectural decomposition, not implementation," which is acceptable, but the panel should flag that the implementation specialist (Kimi) be empowered to consolidate where the simpler form is functionally equivalent.

Not a blocking conflict, but worth noting.

---

## 4. What Must Be Resolved Before Proceeding

The Architect must produce a revision addressing all of the following before the proposal advances to DeepSeek (adversarial review). These are coherence-level requirements; feasibility (Qwen) and factual (Gemini) issues are out of scope for this evaluation.

| # | Required resolution |
|---|---|
| A | Define the gate that produces `approved_for_execution`. Name the actor and the criteria. |
| B | Commit to a single Drone architecture: typed classes or one executor with scoped manifests. Reconcile Sections 1, 8, 9. |
| C | Produce a sanitization map: input source × sanitization mechanism × placement. Cover human input, Overseer outputs, external content, tool outputs. |
| D | Define the permission manifest: schema, storage, enforcement point. This is the zero-trust enforcement artifact and cannot remain abstract. |
| E | Integrate the verifier into the state machine and the module list. Commit to "after every state-changing Drone action" or revise. |
| F | Specify read-access boundaries for each role. Pair them with the existing write-access table. |
| G | Specify the sandbox isolation mechanism by name (Windows Job Objects + restricted token, or alternative with rationale). Core Value 1 forbids deferring this. |
| H | Architect the watchdog: placement, trigger conditions, authority. |
| I | Add an Overseer plan-checkpoint step or explicitly justify omission against the legacy research finding. |
| J | Surface the Core Value 2 scope question on local-model sanitization. Either justify in scope or trigger amendment process. |

---

## 5. Recommendation

**Return to Architect for revision.** The structural foundation is sound and worth preserving — sequential execution, queue-mediated coordination, SQLite persistence, sandbox/network separation, and provider-agnostic model gateway are all defensible against constraints and values. The proposal does not need to be rebuilt.

The required revisions are tightening, not redesigning. Most are gaps where the proposal asserts a property (zero-trust, sandbox isolation, verification) without specifying the mechanism that produces it. Those mechanisms must be on paper before this can advance.

Do not advance to DeepSeek, Gemini, or Qwen until the revision addresses items A–J. Sending an underspecified proposal to adversarial review wastes the Critic's effort on gaps that aren't really design decisions yet.