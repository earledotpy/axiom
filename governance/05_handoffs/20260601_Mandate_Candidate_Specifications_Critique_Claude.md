Before I write this up I need to confirm one load-bearing fact about the cross-handler loop, since it changes whether a containment objection is blocking.Confirmed the facts I needed. The picture is worse than a single `Invoke-Expression` — there are **five distinct executors** with **three distinct execution mechanisms**, and the mandate as written only names one mechanism by its string. Here's the review in the required format.

## 1. Executive verdict

**Approve after changes.** The mandate is correctly bounded — it does not overreach into Orchestrator/Mandate/verifier territory, it keeps doctrine frozen, and it correctly degrades terminal state to `VERIFIED_EVIDENCE_RECORDED`. But as written it under-specifies the threat surface and accepts detection-grade tests for a prevention-grade invariant. It is not yet safe to hand to Codex, because an implementer could fully satisfy it and leave live execution paths intact.

## 2. What is correct

The non-authorization discipline is right: §4 blocks Orchestrator, Ed25519, Console, autonomy, gateways, doctrine; §10.8–10.10 halt if any of those become necessary; §12 forbids `VERIFIED_COMMIT` and degrades to `VERIFIED_EVIDENCE_RECORDED`, matching the §4.4 honesty rule. The blocked-file set correctly walls off `axiom/core/` (including the `scheduler_tick` gate-bypass flag, which is a real but separate concern) and `governance/01_live_spine/`. §8's acknowledgment that static/mock tests have limitations is the right instinct — it just doesn't go far enough. This is a genuinely well-scoped containment slice, not a Trojan for autonomy.

## 3. Blocking objections

**B-1 — The mandate names one execution string; the build has three execution mechanisms across five executors.**
The mandate's tests and blocked actions center on `Invoke-Expression` and `codex exec`. The actual surface:
- `loop_watcher.ps1` and `_inbox_claude.ps1` → `Invoke-Expression $msg.body`
- `_inbox_codex.ps1` and `agent_bridge.ps1` → `& codex exec --sandbox workspace-write -C C:\axiom $Prompt` (message body becomes a Codex prompt with workspace-write)
- `_inbox_antigravity.ps1` → `Invoke-ConPtyCaptureHosted -Command $agyExe --print $Prompt` (body driven into the Antigravity binary via ConPTY)

A test suite that proves "`Invoke-Expression` is unreachable" leaves the Codex and Antigravity executors fully live.
- *Invariant violated:* "raw command frames cannot trigger execution" / hub-and-spoke-only relay.
- *Minimum correction:* the mandate must enumerate all three mechanisms and require each executor (`loop_watcher`, `_inbox_claude`, `_inbox_codex`, `_inbox_antigravity`, `agent_bridge`) to be neutralized and individually tested. Add `agent_bridge.ps1` to §5.1 (it is currently unlisted and is a full executor).

**B-2 — "Static source scan" and "Invoke-Expression unreachable" are detection-grade, not prevention-grade.**
A grep for `Invoke-Expression` proves a string is absent. It does not prove no message body reaches an evaluator — `iex`, `&`, `Invoke-Command`, `[scriptblock]::Create()`, `.Invoke()`, `Start-Process`, and `codex exec`/`agy --print` all evade it. As specified, the invariant rests on the implementer's diligence, which is precisely "model obedience mistaken for machine enforcement."
- *Invariant violated:* prevention must be machine-enforced, not documented.
- *Minimum correction:* require the implementer to **extract the dispatch decision into a pure, testable function** (input: message record; output: a disposition enum of `rejected | dead_letter | manual_review | notify | requires_orchestrator`) and prove by behavioral test that no input — including `type:"command"`, spoofed `from_agent`, and arbitrary body — ever returns an execute disposition. The static grep stays only as a secondary tripwire, over a broadened forbidden-pattern set, explicitly labeled detection-grade.

**B-3 — The peer-to-peer test, as worded, passes while the routing edge survives.**
Every executor ends with `& $sendScript -To $msg.from_agent`. The `_inbox_*` handlers have **no `re:` skip** (only `loop_watcher`/`agent_bridge` do) — they are damped solely by a 60-second same-subject circuit breaker. So codex→claude→codex can form a real execution loop. §8.6 only requires proving relay "does not create execution authority," which is satisfiable while the auto-send edge still exists and still drives the other agent's executor.
- *Invariant violated:* no direct agent-to-agent edge; identity must not come from `from_agent`.
- *Minimum correction:* require removal of the auto-`$sendScript`-to-`from_agent` edge in all five executors (not merely proving the receiver doesn't execute), and a test that an inbound message produces zero outbound agent-directed sends.

**B-4 — Baseline must cover all of `ipc/`, not the enumerated subset.**
`_agy_probe.ps1` and `_agy_hosted_test.ps1` contain execution/agent-invocation patterns and are in neither the allowed nor blocked list — a gap. An implementer following the file lists literally will not inspect them, and a re-armable probe executor survives the "freeze."
- *Invariant violated:* "freeze" requires a complete inventory.
- *Minimum correction:* §2.1 baseline must require enumerating and classifying **every** file under `ipc/`; any executor found outside §5.1 triggers the §10 stop-and-return rule rather than being silently skipped.

## 4. Non-blocking concerns

- The candidate merges the proposal's Phase 0 (baseline/freeze) and Phase 2 (neutralize) into one slice. Defensible, but it means "before" evidence is produced in the same slice that mutates the files. Require the baseline snapshot to be committed/hashed **before** any neutralization edit, or the before/after evidence is reconstructed rather than captured.
- `tools/seal.py` and `tools/gatekeeper.py` are blocked but don't exist in the repo. Harmless, but the blocked list implies they do; note them as "must-not-create" rather than "must-not-modify."
- The markdown inbox files (`to_*.md`) are the live inputs the watchers read. If watchers keep running in notification-only mode, those files remain live attack surface. Prefer halting the watcher services in Phase 0 over leaving them running degraded.
- `_inbox_codex` runs Codex with `--sandbox workspace-write` against `C:\axiom`. Even "frozen," note in residual risk that this grants repo-write to an LLM-driven path; it belongs behind the future Orchestrator.

## 5. Required schema changes

`ipc/ipc_db.py` / `ipc_messages.db`: remove `command` from the accepted `type` enum and define the disposition enum from B-2 as the only legal outcomes. Add a signed-identity placeholder column note for the future Orchestrator (do not implement signing now). No `axiom/` schema changes — correctly out of scope.

## 6. Required tests

Reframe §8 around the dispatch function and all five executors:
1. Dispatch function returns a non-execute disposition for `type:"command"`.
2. Dispatch returns non-execute for arbitrary body with spoofed `from_agent`.
3. No executor path reaches `Invoke-Expression`, `iex`, `&`-call of a body, `codex exec`, or `agy/ConPTY` on a message body (behavioral where feasible; broadened static tripwire otherwise).
4. Inbound message produces zero outbound agent-directed `send` calls (kills the peer-to-peer edge).
5. `_inbox_codex` cannot invoke `codex exec` from inbound content.
6. `_inbox_antigravity` cannot invoke `agy --print`/ConPTY from inbound content.
7. Every unsafe message yields a deterministic disposition value.
8. Notification-only path, if retained, performs no execution and no agent-directed send.

## 7. Required implementation changes

Add `ipc/agent_bridge.ps1` to §5.1. Require the dispatch-extraction refactor (B-2). Require removal of auto-send-to-`from_agent` in `loop_watcher.ps1`, `_inbox_claude.ps1`, `_inbox_codex.ps1`, `_inbox_antigravity.ps1`, `agent_bridge.ps1`. Require full `ipc/` inventory including the probe/scratch scripts. No changes outside `ipc/` + `tests/ipc/` + the single evidence artifact.

## 8. Go / No-Go recommendation

**No-go for Codex as written; go after the B-1 through B-4 edits.** The mandate's authority discipline is sound and doctrine stays frozen — that part needs no change. What it lacks is threat-surface completeness and machine-enforceable test criteria. Make the four corrections and it is safe to hand to Codex for Phase 0/2 implementation, with terminal state capped at `VERIFIED_EVIDENCE_RECORDED`.

One thing for you to decide before you revise the candidate, because it determines the test strategy: do you want Phase 0 to **halt the watcher services entirely** (cleanest freeze — nothing reads the inboxes, and the dispatch-function tests become the proof that the *future* re-enabled path is safe), or **keep them running in a neutered notification-only mode** (preserves the relay plumbing for later, but keeps live FileSystemWatchers reading attacker-controllable files and makes "frozen" a runtime claim rather than a structural one)? Your answer changes whether B-3's correction is "remove the send edge" or "stop the process that would traverse it."