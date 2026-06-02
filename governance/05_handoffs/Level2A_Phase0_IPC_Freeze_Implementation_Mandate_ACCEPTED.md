# Level2A_Phase0_IPC_Freeze_Implementation_Mandate_ACCEPTED

**Accepted Mandate ID:** `MND-ACCEPTED-2026-0001-PHASE0-IPC-FREEZE`
**Source Candidate:** `MND-CANDIDATE-2026-0001-REV-C`
**Status:** Accepted for Phase 0 implementation only.
**Accepted By:** Jeremy Earle, Governance Principal / Operator.
**Authority Boundary:** This accepted mandate authorizes only the Phase 0 IPC Freeze implementation slice described in REV-C.
**Doctrine Status:** No doctrine change authorized. AXIOM remains `non-autonomous by design`.
**Authorized Terminal State:** `VERIFIED_EVIDENCE_RECORDED` or `AUDIT_FAILED`.
**Unauthorized Terminal State:** `VERIFIED_COMMIT`.
**Level 2A Acceptance:** Not authorized.
**Live-Spine Update:** Not authorized.
**Orchestrator Construction:** Not authorized.
**Mandate Signing / Sealing Tooling:** Not authorized.
**Verifier Account Implementation:** Not authorized.

---

## 1. Acceptance Decision

REV-C is accepted as the operative Phase 0 implementation mandate for IPC freeze and containment.

The acceptance decision is based on the completed review loop:

1. Gemini scoped architecture review returned approval.
2. Claude governance/specification review returned approval.
3. Codex feasibility review returned go after Jeremy approval.
4. No remaining blocking objections require further mandate-text revision.

This document converts REV-C from candidate status into an accepted Phase 0 implementation mandate.

---

## 2. Operative Mandate Body

The operative implementation body is:

```text
Level2A_Phase0_IPC_Freeze_Mandate_Candidate_REV_C
Candidate ID: MND-CANDIDATE-2026-0001-REV-C
```

REV-C is incorporated as the controlling implementation specification.

If this accepted wrapper conflicts with REV-C, the stricter containment rule controls.

If REV-C conflicts with the no-doctrine-change rule, the no-doctrine-change rule controls.

If REV-C conflicts with the prohibition on `VERIFIED_COMMIT`, the prohibition controls.

---

## 3. Authorized Implementation Scope

The implementer is authorized to perform only the Phase 0 IPC freeze slice.

Authorized implementation scope:

1. Mechanically inventory every path under `$AXIOM_WORKSPACE/ipc/`.
2. Capture pre-modification SHA-256 hashes.
3. Reconcile directory-walk path count against classification row count.
4. Classify every IPC file and runtime artifact.
5. Identify generalized unsafe sinks.
6. Establish structural unreachability using dominant fail-closed guards.
7. Freeze watcher, executor, startup, ConPTY, tmux, terminal, agent-invocation, markdown-inbox, database-dispatch, and peer-relay IPC paths.
8. Apply narrow `ipc_db.py` neutralization for executable `command` message types only.
9. Add focused IPC containment tests.
10. Produce one evidence artifact.
11. Return implementation evidence for audit.

---

## 4. Additional Accepted Implementation Note

Composition-graph traversal must be bounded.

If graph traversal exceeds three nested layers, encounters cycles, or becomes ambiguous, the implementer must stop automated traversal, record the unresolved edge in the evidence artifact, and return for governance review rather than guessing.

This note does not authorize omission of the edge. It authorizes bounded traversal with explicit unresolved-edge reporting.

---

## 5. Non-Authorization Statement

This accepted mandate does not authorize:

1. live-spine doctrine modification;
2. Level 2A acceptance;
3. `VERIFIED_COMMIT`;
4. autonomous operation;
5. `safe_pass_enabled`;
6. model-profile promotion;
7. Orchestrator construction;
8. Ed25519 signing or sealing tools;
9. verifier-account implementation;
10. Console construction;
11. Telegram/operator-control activation;
12. real model calls;
13. real cloud calls;
14. real network gateway calls;
15. real sandbox execution;
16. real memory embedding writes or queries;
17. changes to AXIOM runtime core outside the REV-C allowed scope.

AXIOM remains:

```text
non-autonomous by design
```

---

## 6. Implementation Evidence Acceptance Bar

The returned implementation evidence must affirmatively prove all of the following.

1. Directory-walk path count equals classification row count.
2. Every path has SHA-256, size, classification, and containment status.
3. No generalized unsafe sink is reachable from inbound content without a dominant guard.
4. Dominant guards are proven from all entry points, including dot-sourced entry points.
5. `ipc_service.ps1` is safe as a composed service.
6. Existing `command` rows in `ipc_messages.db` cannot drive execution.
7. Markdown inbox mutation produces zero process, agent, database, or outbound-send effects.
8. Startup scripts cannot re-arm IPC execution.
9. Process-tree evidence is captured as supporting evidence only.
10. Evidence contains no secrets, raw usernames, private keys, tokens, unredacted environment values, or machine-specific user paths.
11. No blocked files were modified.
12. No doctrine change was performed.
13. No `VERIFIED_COMMIT` claim was made.

If any item is missing, ambiguous, or contradicted by evidence, the implementation result is `AUDIT_FAILED`.

---

## 7. Required Implementation Return Package

The implementer must return:

1. implementation summary;
2. files changed;
3. files inspected but unchanged;
4. blocked files confirmed untouched;
5. mechanical directory-walk manifest summary;
6. SHA-256 baseline summary;
7. classification reconciliation result;
8. composition graph summary;
9. generalized unsafe sink model used;
10. dominant guard pattern used;
11. dominant guard placement summary;
12. `ipc_db.py` command-neutralization summary;
13. test files added or updated;
14. test method disclosure;
15. test result summary;
16. process-tree validation summary;
17. side-channel ingress test result;
18. residual risks;
19. final recommendation: `VERIFIED_EVIDENCE_RECORDED` or `AUDIT_FAILED`.

The implementer must not claim `VERIFIED_COMMIT`.

---

## 8. Codex Implementation Handoff Prompt

Role: Implementation Specialist and Troubleshooter.

You are authorized to implement only the accepted Phase 0 IPC Freeze mandate:

```text
MND-ACCEPTED-2026-0001-PHASE0-IPC-FREEZE
```

The operative specification is:

```text
MND-CANDIDATE-2026-0001-REV-C
```

This mandate authorizes Phase 0 IPC containment only.

Do not alter doctrine.
Do not modify the live spine.
Do not build the Orchestrator.
Do not build signing or sealing tools.
Do not implement a verifier account.
Do not claim Level 2A acceptance.
Do not claim `VERIFIED_COMMIT`.
Do not modify files outside the REV-C allowed scope.

Use structural unreachability, not deletion, unless structural unreachability cannot be proven. If it cannot be proven, stop and return `AUDIT_FAILED`.

Before making containment edits, capture the mechanical directory-walk manifest and pre-modification SHA-256 baseline for every path under `$AXIOM_WORKSPACE/ipc/`.

Bound composition-graph traversal to three nested layers. If traversal exceeds that depth, cycles, or becomes ambiguous, record the unresolved edge and stop for governance review rather than guessing.

Return the required implementation evidence package. The maximum successful terminal state is:

```text
VERIFIED_EVIDENCE_RECORDED
```

The failure terminal state is:

```text
AUDIT_FAILED
```

No other terminal state is authorized.
