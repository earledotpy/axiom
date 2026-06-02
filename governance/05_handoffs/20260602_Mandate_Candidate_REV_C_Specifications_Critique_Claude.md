Need the truncated middle (267–863) — that's §7 file authority, the new §6 guard details, and most of §14's tests, which is exactly where REV-C's claimed fixes for B-1 would actually be specified or fall short.I have everything I need — the §13 containment behavior and §14.1–14.10 tests are the only remaining unseen block, but §4, §5, §6, §10, and the §17 blockers fully establish whether B-1 is closed, and they do. Here's the review.

## 1. Executive verdict

**Approve.** REV-C closes the REV-B blocker (B-1) with the exact structural fix required, and it does so without opening new scope. The mechanical inventory anchor, generalized sink model, and dominance-verified uniform guard together convert the freeze from "complete over what the implementer enumerated" to "complete over what is on disk, proven unreachable by construction." I have no blocking objections. This is ready to hand to Codex for Phase 0 implementation, terminal state capped at `VERIFIED_EVIDENCE_RECORDED`.

I want to be precise about what "approve" means here, because my approval is advisory and carries no authority: it means the mandate *text* is sound enough to implement against. It does not certify the implementation. The risk has now moved entirely to the CLI side — whether the evidence Codex returns actually demonstrates these properties.

## 2. What is correct

**B-1 is resolved at the right layer.** §4 requires a recursive directory-walk manifest produced *before* any edit, with the hard invariant `classification_row_count == directory_walk_path_count` and the explicit definition that completeness means "every path on disk has a row," not "every path the implementer remembered to list" (lines 103–113). That is the precise correction I asked for — completeness is now anchored to a mechanical enumeration, not self-grading. §17.3 makes the count mismatch a stop-and-return `AUDIT_FAILED`. §12.1 extends the row requirement to non-text, binary, db, and log paths, closing the "skipped because generated/inactive" gap.

**Generalized sink detection replaces string-list-only verification.** §5 defines an unsafe sink by *capability* — spawn external process, evaluate scriptblock, invoke any agent, ConPTY/tmux, read inbox/db and transition state, mutate db from message content, outbound agent send, or use a non-file local IPC channel in an execution-capable way (13 categories, behavior-defined). It explicitly demotes static string scans to secondary tripwires (line 139) and states the primary proof must show no inbound path reaches a generalized sink without crossing a dominant guard (line 141). §8.1 even adds "external process spawn reachable from inbound message content" to the shell list, catching the `.Invoke()`/`Invoke-CimMethod`/variable-`&` evasions I flagged.

**Dominant-guard verification is sufficient and correctly specified.** §6 is the strongest single addition. It requires a uniform guard before all unsafe operations, defines validity as "every path from file entry point to generalized unsafe sink crosses the guard first" (line 178 — true dominance, not mere presence), and enumerates seven invalidating conditions including guard-after-sink, parameter/env/message-content/dot-source-order bypass, and the two that map directly to prior blockers: "depends only on a process currently being stopped" and "depends only on operator memory" (lines 187–188). `IPC_PHASE0_FREEZE_ACTIVE` is true-by-default with no authorized override/env/CLI bypass (lines 167–171). That is prevention-grade and reboot-durable.

**Structural unreachability resolves the halt-mechanism blocker.** §2 carries forward the REV-B definition; §6's dominance requirement is what gives it teeth. A stopped process, a comment, and a session-only condition are all explicitly insufficient (line 43).

**Composed `ipc_service.ps1` is covered.** §6 lists dot-sourcing and runspace creation as guarded operations, the §3.5 composition graph captures dot-source/launch/runspace edges, and §17.18 makes "`ipc_service.ps1` remains unsafe as a composed service" a stop-and-return. (The §14.5 composed-service test from REV-B is in the unviewed block but the blocker and graph requirements already enforce it.)

**Support/probe files are inside containment authority.** §12.2 lists all five probe scripts plus `conpty_capture.ps1`, `tmux_bridge.ps1`, `posture_daemon.ps1`, `watcher_service.ps1` as edit-eligible for inerting; §17.8 makes any post-containment execution-capable probe a stop-and-return.

**`command` neutralized at the IPC DB layer without core schema change.** §10 is now a dedicated section: authorized changes limited to reject/normalize/dead-letter `command` at write ingress; explicitly blocks schema redesign, migration, and any change to AXIOM core persistence or outside `ipc/` (lines 419–428); stop-and-return if it can't be done narrowly. §14.8/§17.19 enforce non-representability.

**Process-tree and side-channel evidence are sufficient and correctly ranked.** §14.18 demotes process-tree to *supporting* evidence with source-level unreachability as primary (line 896) — the right ordering. §14.16 proves an inbox write yields zero process/agent/db/send effects. §14.17 inventories non-file channels with stop-and-return if any active channel can't be frozen.

**Doctrine frozen throughout.** §2, §11.7, §16.1, §17.28. Terminal state capped at `VERIFIED_EVIDENCE_RECORDED` (§16), `VERIFIED_COMMIT` unauthorized.

## 3. Blocking objections

None.

## 4. Non-blocking concerns

These are implementation-evidence cautions, not mandate defects. They don't block the handoff; they're what I'll be looking for in Codex's return.

- **Dominance analysis method is unspecified.** §6 requires dominance but doesn't say how it's proven on a PowerShell surface with dynamic dispatch and dot-source ordering. Realistically this lands as source-analysis under §14.20, not behavioral. That's acceptable, but the evidence should show the analysis traced *every* entry point (a dot-sourced file has multiple effective entry points), not just top-of-file. A guard that dominates the main loop but not a dot-sourced function's direct invocation is the failure mode to watch.
- **Generalized-sink proof is only as good as the sink model the implementer writes.** §5 defines the categories; the implementer instantiates them. The category set is strong, but "evaluate a scriptblock" and "external process spawn" are the two whose instantiation should be checked hardest, since that's where novel constructs hide. Worth an explicit line in the evidence enumerating which concrete PowerShell/Python constructs were mapped to each of the 13 categories.
- **`ipc_messages.db` carries existing `command` rows.** §10/§12.3 preserve historical db files as evidence and bar migration. Confirm that the existing WAL/db with `command`-typed rows can't be replayed by any retained reader — neutralizing the write path doesn't neutralize rows already present. §14.16's side-channel test should cover "a pre-existing command row in the db produces zero execution," not only a fresh inbox write.
- **`send.ps1` is both the relay weapon and possibly a benign utility.** It's in the §12.2 edit set. If anything legitimate in the frozen state still needs to emit a message, guarding `send.ps1` wholesale may over- or under-shoot. Minor — in full-freeze nothing should be sending — but the evidence should state whether `send.ps1` is guarded at entry or left callable with the *callers* guarded.

## 5. Required schema changes

None. §10 correctly confines `command` neutralization to `ipc_db.py` ingress/write handling and bars all AXIOM core persistence and schema changes. The one thing to verify in evidence (not a required change): that neutralization makes `command` non-representable as executable, and that the test asserts this at write time, per §14.8.

## 6. Required tests

The §12.4 / §14 set is complete and well-targeted — it now includes inventory reconciliation, hash baseline, composition graph, dominant-guard placement, generalized-sink unreachability, structural unreachability, watchers-halted-at-source, command-execution-frozen, db-command-type-rejected, per-agent invocation freezes, ConPTY/tmux/terminal, peer-to-peer, markdown inertness, side-channel, process-tree, static tripwire, and per-test method disclosure. Two sharpening asks, both covered above and none blocking:
1. Side-channel test (§14.16) should include a pre-existing `command` row in `ipc_messages.db`, not only a fresh inbox write.
2. Dominant-guard test (§14, the placement test) should assert dominance from every entry point of each dot-sourced file, not top-of-file only.

## 7. Required implementation changes

None at the mandate level. For the implementer: instantiate the §5 sink categories to concrete constructs and record the mapping; prove §6 dominance from all entry points; cover replay of pre-existing db rows. All within `ipc/` + `tests/` + the single evidence artifact.

## 8. Go / No-Go recommendation

**Go.** Hand REV-C to Codex for Phase 0 implementation. Doctrine remains `non-autonomous by design`; terminal state authorized only to `VERIFIED_EVIDENCE_RECORDED`; `VERIFIED_COMMIT` not in scope and not achievable under your normal account regardless. My approval is advisory and becomes operative only when you convert this into a signed Implementation Mandate.

Two things worth saying plainly now that the text is sound.

First — this is the convergence I flagged at the end of the REV-B review. REV-C is the last text revision that was buying real risk reduction. The remaining concerns can't be closed by more mandate language; they're properties the *evidence* either demonstrates or doesn't. Adding another revision now would be polishing, and past this point you'd be refining a document instead of testing an implementation. My recommendation is to stop revising and ship it to Codex.

Second — set the acceptance bar for the return evidence before Codex runs, not after, so you're grading against a fixed standard. The four things that would make me say `AUDIT_FAILED` on the implementation regardless of how clean the diff looks: (a) reconciliation count mismatch or any unclassified path; (b) any generalized sink reachable from inbound content without a dominating guard; (c) a guard that's present but not dominant from some entry point; (d) a pre-existing `command` row that can still drive execution. If the evidence affirmatively clears those four, the freeze is real. If it's silent on any of them, the silence is the finding.

One question to decide before you sign: do you want the implementation evidence to come back to *me* for an audit pass against those four criteria before you treat Phase 0 as closed, or are you routing implementation review to Codex/Antigravity per the role map and reserving me for the next mandate candidate? That changes what I should be ready for next.