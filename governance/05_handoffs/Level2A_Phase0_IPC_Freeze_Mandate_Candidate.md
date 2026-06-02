# AXIOM Level 2A Implementation Mandate Candidate

## Phase 0 — Baseline and Unsafe IPC Freeze

**Candidate ID:** `MND-CANDIDATE-2026-0001`
**Target Level:** `2A`
**Status:** Candidate only. Not signed. Not executable authority.
**Doctrine Status:** No doctrine change authorized. AXIOM remains **non-autonomous by design**.

---

## 1. Intent

Establish a Level 2A pre-implementation baseline and freeze unsafe IPC behavior by documenting current IPC execution paths, neutralizing raw command execution, preventing peer-to-peer agent auto-invocation, and adding regression tests proving that unsafe IPC paths are disabled.

This mandate does **not** authorize Orchestrator construction, Mandate sealing, verifier-account execution, autonomous operation, safe-pass enablement, model-profile promotion, live gateway activation, or doctrine transition.

---

## 2. Scope

This mandate is limited to Phase 0 containment work.

The permitted scope is:

1. Baseline the current IPC implementation.
2. Identify active IPC paths capable of:

   * shell execution;
   * `Invoke-Expression`;
   * Codex auto-invocation;
   * Antigravity/Gemini auto-invocation;
   * direct peer-to-peer agent relay;
   * hidden background agent execution.
3. Neutralize unsafe IPC execution paths.
4. Preserve notification-only or manual-review IPC behavior where safe.
5. Add regression tests proving the unsafe paths remain frozen.
6. Produce evidence artifacts showing before/after behavior.
7. Record audit notes identifying any remaining non-Level-2A IPC surfaces.

This scope is a containment baseline only. It does not establish Level 2A acceptance.

---

## 3. Allowed Actions

The implementer may:

1. Inspect IPC source files and existing IPC documentation.
2. Modify IPC handlers only to disable unsafe execution behavior.
3. Change IPC behavior from auto-execution to:

   * notification-only;
   * manual-review queue;
   * dead-letter;
   * rejected unsafe message type;
   * explicit “requires Orchestrator” disposition.
4. Add or update IPC tests proving unsafe execution paths are unreachable.
5. Add lightweight IPC disposition fields or constants if required to test rejection/dead-letter behavior.
6. Add read-only audit or diagnostic helpers if they do not create new execution authority.
7. Update narrow documentation explaining that IPC is frozen pending Level 2A Orchestrator mediation.
8. Preserve existing evidence of prior IPC behavior unless explicitly marked as unsafe runtime behavior.
9. Produce a before/after file inventory and test evidence.

---

## 4. Blocked Actions

The implementer must not:

1. Build the deterministic Orchestrator.
2. Build Ed25519 Mandate sealing tools.
3. Build or activate a signing Console.
4. Create, sign, or reuse live authority-bearing Mandates.
5. Change the live doctrine.
6. Mark AXIOM as Level 2A accepted.
7. Emit or claim `VERIFIED_COMMIT`.
8. Enable autonomous operation.
9. Enable `safe_pass_enabled`.
10. Promote any model profile to trusted/current.
11. Activate real model calls.
12. Activate real cloud calls.
13. Activate real network gateway fetches.
14. Activate real sandbox execution.
15. Activate real memory embedding writes or queries.
16. Activate Telegram/operator control plane execution.
17. Add new peer-to-peer agent routing.
18. Add new hidden auto-execution services.
19. Preserve `Invoke-Expression` in an active IPC execution path.
20. Allow inbound IPC to invoke `codex exec`.
21. Allow inbound IPC to invoke `agy`, Antigravity, Gemini, ConPTY capture, or equivalent agent execution.
22. Modify unrelated AXIOM runtime policy, manifest, schema, gateway, model, memory, scheduler, or task-lifecycle logic.
23. Modify governance live-spine doctrine except to add a clearly labeled Phase 0 evidence/audit note if explicitly within the allowed artifact list.

---

## 5. Files and Artifacts Allowed

### 5.1 IPC Files Allowed for Inspection and Minimal Containment Edits

The implementer may inspect and minimally modify:

```text
ipc/_inbox_claude.ps1
ipc/_inbox_codex.ps1
ipc/_inbox_antigravity.ps1
ipc/loop_watcher.ps1
ipc/agent_bridge.ps1
ipc/ipc_service.ps1
ipc/send.ps1
ipc/ipc_db.py
```

### 5.2 IPC Files Allowed for Inspection Only Unless Needed for Containment

```text
ipc/conpty_capture.ps1
ipc/startup_claude.ps1
ipc/startup_codex.ps1
ipc/startup_agy.ps1
ipc/watcher_service.ps1
ipc/notify.ps1
ipc/tmux_bridge.ps1
ipc/to_claude.md
ipc/to_codex.md
ipc/to_antigravity.md
ipc/pending_for_claude.md
```

Markdown inbox files may be preserved as historical evidence. They must not be treated as authority-bearing records.

### 5.3 Test Files Allowed

The implementer may add or update focused IPC safety tests under an appropriate test location, for example:

```text
tests/test_ipc_command_frames_rejected.py
tests/test_ipc_invoke_expression_unreachable.py
tests/test_ipc_codex_autoinvocation_disabled.py
tests/test_ipc_antigravity_autoinvocation_disabled.py
tests/test_ipc_peer_to_peer_relay_denied.py
tests/test_ipc_notification_only_behavior.py
tests/test_ipc_requires_orchestrator_disposition.py
```

Existing IPC-related tests may be updated only if the update narrows authority or corrects assumptions made invalid by the unsafe IPC freeze.

### 5.4 Evidence and Audit Artifacts Allowed

The implementer may create a narrow evidence artifact such as:

```text
governance/05_handoffs/Phase0_IPC_Freeze_Evidence.md
```

or, if governance handoff files are not to be touched in this slice:

```text
docs/phase0_ipc_freeze_evidence.md
```

Only one evidence artifact should be created unless there is a clear reason to split audit and evidence.

### 5.5 Files Blocked from Modification

The implementer must not modify:

```text
governance/01_live_spine/
governance/06_archives/
axiom/core/
axiom/persistence/
axiom/security/
axiom/gateways/
axiom/app/
axiom/agents/
axiom/policy/
config/axiom.yaml
requirements.txt
tools/seal.py
tools/gatekeeper.py
```

If a blocked file appears necessary, implementation must stop and request a new mandate candidate.

---

## 6. Evidence Required

The implementation response must include evidence for each of the following:

1. Current IPC baseline summary:

   * which IPC files were inspected;
   * which paths previously allowed command execution;
   * which paths previously allowed agent auto-invocation;
   * which paths remain notification-only or manual-review.

2. Unsafe path neutralization evidence:

   * raw command frames are rejected, dead-lettered, or downgraded to manual review;
   * `Invoke-Expression` is not reachable from active IPC processing;
   * inbound IPC does not invoke Codex;
   * inbound IPC does not invoke Antigravity/Gemini;
   * direct peer-to-peer relay does not create execution authority.

3. Test evidence:

   * exact test files added or updated;
   * test names and what each proves;
   * full test result summary;
   * any skipped tests and why;
   * any failing tests and whether failure is environmental or implementation-caused.

4. Diff evidence:

   * files changed;
   * files inspected but unchanged;
   * blocked files not modified.

5. Residual-risk evidence:

   * any IPC scripts still present but inactive;
   * any legacy scripts retained only as historical evidence;
   * any remaining behavior that must be moved behind the future Orchestrator.

---

## 7. Audit Requirements

The final implementation handoff must include:

1. `MANDATE_CANDIDATE_ID`: `MND-CANDIDATE-2026-0001`.
2. Statement that this was a candidate-derived implementation slice and not a signed Level 2A acceptance.
3. Statement that no doctrine change was performed.
4. Statement that no `VERIFIED_COMMIT` claim is made.
5. Statement that any verification under Jeremy’s normal Windows account is evidence only.
6. List of changed files.
7. List of blocked files confirmed untouched.
8. Test result summary.
9. Residual risk summary.
10. Explicit go/no-go recommendation for the next mandate.

The audit language must distinguish:

```text
VERIFIED_EVIDENCE_RECORDED
```

from:

```text
VERIFIED_COMMIT
```

`VERIFIED_COMMIT` is not authorized in this phase.

---

## 8. Required Tests

At minimum, the implementation must include tests proving:

1. `command` message type does not execute shell content.
2. `Invoke-Expression` is not reachable from active IPC handlers.
3. Inbound messages to Claude do not execute automatically unless future Orchestrator authority exists.
4. Inbound messages to Codex do not call `codex exec`.
5. Inbound messages to Antigravity/Gemini do not call `agy.exe`, ConPTY capture, or equivalent agent execution.
6. Peer-to-peer relay does not create execution authority.
7. Unsafe messages receive a deterministic disposition:

   * rejected;
   * dead-lettered;
   * manual-review;
   * or requires-Orchestrator.
8. Notification-only IPC behavior, if retained, remains non-executing.

If tests must mock PowerShell handlers or inspect static source text, the implementation must explain the test method and limitation.

---

## 9. CLI Agent Review Prompts

### 9.1 Antigravity / Gemini Review Prompt

Review this Phase 0 Level 2A IPC freeze mandate candidate as architecture planner.

Focus only on whether the scope is correctly bounded for baseline and unsafe IPC freeze.

Do not propose doctrine changes.
Do not propose Orchestrator construction in this mandate.
Do not propose Ed25519 Mandate tooling in this mandate.
Do not authorize autonomous operation.

Return:

1. Executive verdict.
2. Scope errors or overreach.
3. Missing unsafe IPC surfaces.
4. Missing evidence requirements.
5. Missing tests.
6. Whether this mandate is safe to hand to Codex for implementation.
7. Required edits before implementation.

### 9.2 Codex Review Prompt

Review this Phase 0 Level 2A IPC freeze mandate candidate as Implementation Specialist.

Do not implement yet.
Do not run commands from this prompt.
Do not modify files.
Do not treat this as signed authority.

Assess feasibility only.

Return:

1. Files likely requiring changes.
2. Files that should remain untouched.
3. Minimal implementation approach.
4. Test files likely required.
5. Risks of breaking existing IPC notification/manual-review behavior.
6. Any blocked action that would require a separate mandate.
7. Whether the mandate is sufficiently specific for implementation.

### 9.3 Claude Code Review Prompt

Review this Phase 0 Level 2A IPC freeze mandate candidate as Governance Auditor and Specification Critic.

Do not implement.
Do not modify files.
Do not claim verification.
Do not accept Level 2A.

Evaluate whether this candidate satisfies the Level 2A control model for Phase 0 containment.

Use the required AXIOM review format:

1. Executive verdict.
2. What is correct.
3. Blocking objections.
4. Non-blocking concerns.
5. Required schema changes.
6. Required tests.
7. Required implementation changes.
8. Go/no-go recommendation.

Pay special attention to:

* whether unsafe IPC execution is fully frozen;
* whether the mandate avoids Orchestrator overreach;
* whether evidence requirements are sufficient;
* whether tests prove machine enforcement rather than documented norms;
* whether doctrine remains non-autonomous by design.

---

## 10. Go / No-Go Blockers

Implementation must stop and return for governance review if any of the following occur:

1. Neutralizing IPC requires changes outside the allowed file set.
2. Tests require modifying runtime policy, gateway, manifest, or schema files.
3. Codex or Antigravity auto-invocation cannot be disabled without breaking required manual-review behavior.
4. `Invoke-Expression` remains reachable from active IPC paths.
5. Any agent proposes preserving command-frame execution for convenience.
6. Any change introduces a new hidden execution service.
7. Any change creates new peer-to-peer execution authority.
8. Any change requires Orchestrator construction.
9. Any change requires Ed25519 signing/sealing tooling.
10. Any change requires verifier-account implementation.
11. Any test result is ambiguous about whether shell execution occurred.
12. Any implementation attempts to claim Level 2A acceptance.
13. Any implementation attempts to update doctrine.
14. Any secret, token, private key, or local credential appears in evidence.

---

## 11. Explicit Non-Authorization Statement

This mandate candidate does not authorize a doctrine change.

AXIOM remains:

```text
non-autonomous by design
```

This mandate candidate does not authorize:

```text
operator-governed, fail-closed, autonomy-gated, scalable, transferable, and AI-built
```

as live doctrine.

That doctrine transition remains blocked until Level 2A acceptance tests pass under the required verifier-isolated path.

---

## 12. Expected Terminal State

The expected terminal state after this Phase 0 slice is:

```text
VERIFIED_EVIDENCE_RECORDED
```

or, if evidence is incomplete:

```text
AUDIT_FAILED
```

The expected terminal state is not:

```text
VERIFIED_COMMIT
```

Level 2A acceptance remains blocked after this mandate unless a later signed mandate completes the remaining verifier-isolated Orchestrator, Mandate sealing, trusted-test, and audit-chain requirements.
