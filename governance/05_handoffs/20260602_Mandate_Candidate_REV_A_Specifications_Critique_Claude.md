I need to actually read REV_A before reviewing it — it wasn't included in the document text, only the path. Let me read it from disk.Let me see the truncated test-file block (313–317) so I'm reviewing the complete required-test list, not a partial one.I have the full document. This is a substantial revision and it closes the four blockers I raised. Here's the review.

## 1. Executive verdict

**Approve after changes.** REV-A is close to go. It fixed the prior blockers: all five executors are named, all three mechanisms are enumerated, the peer-to-peer send edge is targeted directly, static scans are demoted to secondary, and the containment posture is now a clean full-halt rather than a leaky notification-only mode. The remaining objections are narrower but two are still blocking — they concern the *halt mechanism* and the *startup re-arm path*, which are exactly where a "frozen" system quietly thaws.

## 2. What is correct

The posture decision in §2 — `FULL WATCHER / EXECUTOR HALT` over `NOTIFICATION-ONLY LIVE MODE` — is the right call and resolves the B-3 ambiguity from the prior round: with nothing reading the inboxes, the markdown files become inert by construction rather than by claim. All five executors (`loop_watcher`, `_inbox_claude`, `_inbox_codex`, `_inbox_antigravity`, `agent_bridge`) are now in the §7.2 edit set, and `agent_bridge` is correctly included. §4 enumerates the three mechanisms (`Invoke-Expression`/scriptblock, `codex exec`, `agy`/ConPTY) plus the relay loop. §9.6 reframes the peer-to-peer test as "zero outbound agent-directed sends" — the correct prevention-grade phrasing, not the old "does not create authority" wording. §9.8 explicitly labels the static scan secondary and not sufficient alone. §3.1/§7.1 mandate full `ipc/` inventory with no skip-because-legacy. Doctrine stays frozen throughout (§2, §6.7, §11.1). The startup scripts are now in scope (§7.2, §9.2), which the prior version missed.

## 3. Blocking objections

**B-1 — "Halt" is underspecified, and one plausible reading is non-durable.**
§8.10 says startup scripts "must not launch active IPC watcher/executor services during the freeze." "During the freeze" admits a runtime reading: stop the processes now, leave the code armed. If halt = "don't run it," the executor returns on next boot or next manual `ipc_service.ps1` invocation, and every §9 test still passes because they assert on a quiescent process table. That is detection-grade freeze masquerading as prevention.
- *Invariant violated:* freeze must be structural, not a runtime state.
- *Minimum correction:* require the dispatch/execute branch in each of the five executors to be **structurally removed or made unreachable in source** (early-return/throw before any execute path), so the freeze survives a reboot and a manual relaunch. §9.2 must assert that launching `ipc_service.ps1` / `startup_*.ps1` reaches no execute branch — not merely that "active processing does not start."

**B-2 — `ipc_service.ps1` dot-sources the executors; editing the leaf scripts may not neutralize the composed runspace.**
The earlier `_posture_runspace.ps1` header showed `ipc_service.ps1` is the composition root that dot-sources `_inbox_*` and the posture runspace into one process ("Replaces: loop_watcher.ps1, agent_bridge.ps1… posture_daemon.ps1"). If the implementer neutralizes the standalone `_inbox_*.ps1` files but `ipc_service.ps1` contains or inlines its own dispatch, the freeze has a hole. The mandate lists both but does not require proving the *composed* service has no execute path.
- *Invariant violated:* completeness of the halt across the actual execution topology.
- *Minimum correction:* require the inventory (§5.2) to record the dot-source / inlining graph — which files `ipc_service.ps1` loads and whether any dispatch is inlined there — and require §9.2 to assert the executor-free property on the *composed* `ipc_service.ps1`, not only on the leaf scripts in isolation.

## 4. Non-blocking concerns

- §7.1 has a soft exception: an executor found outside the known list need not stop-and-return "if the file is clearly inert and can be documented as evidence-only." "Clearly inert" is an implementer judgment call on the exact category of file (probe/scratch executors) most likely to be re-armable. Tighten to: any file containing an execute/agent-invoke pattern goes to stop-and-return regardless of believed inertness, unless its inertness is proven by the §9.2 launch test. Non-blocking because the §12.1/§12.2 blockers already catch the dangerous cases.
- §9.7 markdown-inertness is phrased as "not active control inputs during the freeze" — again the runtime "during the freeze" wording. Given the full-halt posture this is consistent, but it would be stronger as "no source file in `ipc/` contains an active reader of the `to_*.md` files after edits."
- `tmux_bridge.ps1` (send-keys) and `conpty_capture.ps1` (the ConPTY engine `_inbox_antigravity` depends on) are inspect-only in §7.3. Correct for this slice, but the evidence artifact should explicitly record that neutralizing `_inbox_antigravity`'s caller leaves `conpty_capture.ps1` present as a re-armable capability behind the future Orchestrator.
- No concern with the blocked list; adding `tools/orchestrator.py` and `tools/verify_mandate.py` to the must-not-create set (§7.6) is a good tightening over REV.

## 5. Required schema changes

`ipc/ipc_db.py`: as before, remove `command` from the accepted message `type` so the database cannot represent an executable frame even if a future reader regresses. REV-A allows `ipc_db.py` edits (§7.2) but §9 does not require proving the `command` type is unrepresentable — only that handlers don't act on it. Add a test that the DB layer rejects or has no `command` type. This is the difference between "no current reader executes it" and "the type cannot exist." Still within IPC scope; no `axiom/` schema touched.

## 6. Required tests

The §9 set is sound. Add or sharpen:
1. **(B-1)** Launch-reaches-no-execute: invoking `ipc_service.ps1` and each `startup_*.ps1` in a harness reaches no dispatch/execute branch (source-level unreachability, not process-absence).
2. **(B-2)** Composed-service property: `ipc_service.ps1` with all dot-sourced components loaded exposes no execute path.
3. **(Schema)** `command` type is not representable/accepted at the `ipc_db.py` layer.
4. Keep §9.6 as the peer-to-peer proof; add that it holds for all five executors individually, not just one representative.

The PowerShell-vs-pytest method gap remains real: most executors are `.ps1`, the test suite is pytest. The mandate should require the implementer to state, per test, whether it is behavioral (executed harness) or source-analysis, and justify any source-only test as the best available given the PowerShell surface. REV-A gestures at this in §9.8 for the tripwire but should require it for §9.2–9.6 too.

## 7. Required implementation changes

Structural removal/unreachability of the execute branch in all five executors (not process-halt alone). Inventory must capture the `ipc_service.ps1` dot-source graph. Remove auto-send-to-`from_agent` in source across the five. `command` type removed at the DB layer. No changes outside `ipc/` + `tests/` + the single evidence artifact.

## 8. Go / No-Go recommendation

**No-go as written; go after B-1 and B-2.** The gap between REV and REV-A is large and the right things got fixed — this is no longer a mandate an implementer can satisfy while leaving Codex and Antigravity executors live. What remains is making sure "freeze" means *unreachable in source*, not *not currently running*, and that the composed `ipc_service.ps1` is proven executor-free rather than only its leaf scripts. Close those two and it is safe to hand to Codex, terminal state capped at `VERIFIED_EVIDENCE_RECORDED`.

One decision point for you before REV-B, because it sets the standard the implementer will be held to: do you want the freeze defined as **deletion** of the execute branches (smallest possible attack surface, but you lose the relay logic you may want to port behind the Orchestrator later), or **structural unreachability** — guarded early-return/throw with the original logic left inert below it (preserves the code for later reuse, but a future edit can re-arm it by removing one guard)? Deletion is the stronger invariant; unreachability is the more recoverable one. That choice determines whether B-1's test asserts "branch absent" or "branch present but provably unreachable."