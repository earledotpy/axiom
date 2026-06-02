I need the truncated middle (285–595) — that's where §7 file authority, the §8 containment requirements, and the start of §9 tests live. Those are exactly the sections the prior blockers targeted, so I can't review without them.I have the complete document now. REV-B closes both prior blockers cleanly and adds the side-channel coverage I'd flagged as non-blocking. Here's the review.

## 1. Executive verdict

**Approve after one change** — and the change is a verification-discipline gap, not a containment-scope gap. Substantively this mandate is sound: structural unreachability is correctly defined, the composed `ipc_service.ps1` is covered, the probe/scratch and ConPTY/tmux files are now inside containment authority, `command` is neutralized at the DB layer, and side-channel + process-tree evidence are required. The one residual blocker is about who certifies the inventory is complete, because the entire freeze rests on an enumeration the implementer produces and grades itself against.

## 2. What is correct

The §2 definition resolves the prior halt-mechanism blocker directly: "A stopped process is not sufficient… The freeze must survive manual relaunch and reboot," with unsafe branches allowed in source only behind a *dominant fail-closed guard*. That is prevention-grade, not runtime-state. §8.1–8.2 and §9.4 enforce it as a source-level property tested under manual launch.

The composed-service blocker (prior B-2) is closed: §8.14 requires `ipc_service.ps1` safe *as a composed service, not merely safe when leaf scripts are inspected separately*, §9.3 requires the dot-source/runspace composition graph, and §9.5 requires proving the composed service exposes no path to any of the seven execution sinks. That is exactly the topology-aware coverage that was missing.

Support/probe files are now first-class: §7.2 explicitly lists `conpty_capture.ps1`, `tmux_bridge.ps1`, `posture_daemon.ps1`, `watcher_service.ps1`, and all five probe scripts as edit-eligible for inerting, and §7.1 forces any file with an execute/invoke/listener pattern to be classified execution-capable *unless tests prove unreachability* — closing the "clearly inert" soft exception from REV-A.

`command` is handled at the right layer: §8.12 and §9.8 require it be rejected/non-representable at `ipc_db.py`, explicitly without touching AXIOM core schema. That converts "no handler acts on it" into "the type cannot carry execution."

Side-channel and process-tree evidence (the things I'd raised as non-blocking) are now required: §9.14 proves a write to an inert inbox yields zero process/agent/db/send effects; §9.15 inventories named pipes, loopback, sockets, shared memory, runspaces, ConPTY/tmux, posture channels; §9.16 validates the process tree. §9.18's per-test method disclosure (behavioral vs source-analysis vs process-tree vs static vs manual) is the right honesty mechanism for a PowerShell surface a pytest suite can only partially exercise. Doctrine stays frozen end to end (§2, §6.7, §11.1, §12.24). The SHA-256 pre-modification baseline (§3.2, §5.2, §9.2) makes the before-state tamper-evident, fixing the REV concern that before/after evidence was reconstructed rather than captured.

## 3. Blocking objections

**B-1 — The freeze's completeness depends on a self-graded inventory with no independent enumeration anchor.**
Every guarantee in this mandate is scoped to "files under `$AXIOM_WORKSPACE/ipc/`" and to the patterns the implementer searches for. The implementer both produces the inventory and certifies it complete against its own list. If a file is missed, or an execution sink uses a construct not in the §3.5/§9.17 pattern set (e.g. `.Invoke()` on a stored scriptblock, `Invoke-CimMethod`, `&` against a variable resolved from the DB, a `.lnk`/scheduled-task launcher, a wrapper that execs without the literal strings), it passes silently — the tests only assert over the enumerated patterns, and §9.1 "every file was inventoried" is provable while still being under-inclusive.
- *Invariant violated:* a freeze must be complete over the actual surface, not over the surface the implementer happened to enumerate; this is the "model obedience mistaken for machine enforcement" failure at the meta level — the enumeration itself is the unverified instruction.
- *Minimum correction:* anchor completeness to a mechanical, non-judgment baseline. Require the inventory to be reconciled against a directory enumeration captured independently (e.g. a hash-manifest of every path returned by a recursive directory walk, with file count asserted equal to the classification-table row count), so "complete" means "every path on disk has a row," not "every file I decided to list." Second, require the unreachability tests (§9.4/§9.5) to assert on a *generalized* sink definition — any external process spawn or scriptblock evaluation reachable from an inbound message — not only the literal strings in §9.17. The static tripwire list stays as the secondary layer; the behavioral/source proof must not be list-bounded.

That is the only blocker. It is narrow but real: without it, REV-B is a rigorous freeze of *everything the implementer found*, and the one thing Phase 0 most needs to guarantee is that "everything it found" equals "everything there is."

## 4. Non-blocking concerns

- §9.4/§9.5 say "even if scripts are manually launched," but PowerShell unreachability is genuinely hard to prove behaviorally (dynamic dispatch, dot-sourcing order). Expect most of these to land as source-analysis under §9.18. That's acceptable, but require the source-analysis to show the guard *dominates* every sink (no path from entry to sink that doesn't cross the guard), not merely that a guard exists somewhere in the file. A guard after a reachable sink passes a naive "guard present" check.
- §7.2 permits edits to any `ipc/` file "only if necessary to make an unsafe path unreachable." Combined with §6.27 (no new durable disposition helper without stop-and-return), there's mild tension: a clean dominant guard sometimes *is* a small shared helper. Pre-decide whether a one-line shared guard counts as a "helper" so the implementer doesn't either over-duplicate guards or trip the stop-and-return.
- `conpty_capture.ps1` is now edit-eligible, good — but note it's the engine `_inbox_antigravity` calls; inerting the caller and the engine both is belt-and-suspenders, and the evidence should state which layer the dominant guard sits at so a future Orchestrator re-enable doesn't assume the engine is safe.
- §9.6 phrases launcher safety as "unless a future signed Orchestrator/Mandate mechanism exists." Fine as intent, but no such mechanism exists, so the test should assert unconditional fail-closed now and treat the Orchestrator clause as a documented future-relaxation note, not a branch in the test.

## 5. Required schema changes

None beyond what's already specified. §8.12/§9.8 correctly confine the `command`-type neutralization to `ipc_db.py` and explicitly bar AXIOM core schema changes. Confirm the test asserts non-representability (the type cannot be written/stored), not only non-execution on read — REV-B's wording allows either; the stronger reading should be the required one.

## 6. Required tests

The §9 set is comprehensive. Add or sharpen:
1. **(B-1)** Inventory reconciliation: row count of the classification table equals the file count of an independent recursive directory walk; every walked path has a hash and a classification.
2. **(B-1)** Generalized-sink unreachability: no inbound-message-reachable path spawns an external process or evaluates a scriptblock, defined structurally rather than by the §9.17 string list.
3. **(non-blocking)** Guard dominance: for each neutralized file, prove no entry-to-sink path bypasses the guard.
Keep §9.18 method disclosure applied to all of the above.

## 7. Required implementation changes

Mechanical inventory anchor (directory-walk hash manifest reconciled to the classification table). Dominant-guard placement verified per file. Generalized-sink definition in the unreachability tests. Everything else stays within `ipc/` + `tests/` + the single evidence artifact, terminal state `VERIFIED_EVIDENCE_RECORDED`.

## 8. Go / No-Go recommendation

**Go after B-1.** This is the first revision I'd call structurally sound — the containment scope is complete and the verification is mostly prevention-grade. The remaining fix is to stop the freeze's completeness from resting on a self-produced enumeration: anchor "complete" to a mechanical directory walk and define the execution sinks structurally rather than by string list. Make that one change and REV-B is safe to hand to Codex for Phase 0 implementation, with doctrine frozen and `VERIFIED_COMMIT` unauthorized.

A note on where you are in the loop, since you've now run three revisions: the marginal return has shifted. REV → REV-A → REV-B each closed real blockers, but B-1 is the first objection that can't be fully closed by adding more enumeration to the mandate — it's closed by changing *how completeness is proven*, which is a one-time structural fix. Once that's in, further mandate revision will mostly be polishing rather than risk reduction, and the real test moves to whether the implementation evidence actually demonstrates the dominant-guard and reconciliation properties. That's a CLI-side question, not a mandate-text question. I'd expect REV-C to be the last text revision before this goes to Codex.