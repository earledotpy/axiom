# Evaluator Review — AXIOM Proposal v1.10.1

**Bottom line:** v1.10.1 resolves six of seven items from the v1.10 synthesis cleanly. Item 7 (test list reconciliation) is partially addressed — the architect did substantial test-suite work and restored seven tests, but they are not the seven specific tests I flagged in my v1.10 evaluation. This is a bookkeeping mismatch, not an architecture issue, but it must be corrected before Kimi takes the proposal. **Approve to advance to bounded delta-confirmation by Critic only**, with one required footnote correction noted below.

The architect made one materially stronger choice than asked: separate registration CLI rather than command-line flag for manifest registration mode. That's a better architectural boundary than I or the Critic recommended.

---

## Resolution Verification

| # | Synthesis Requirement | v1.10.1 Resolution | Verdict |
|---|---|---|---|
| 1 | Fingerprint verification fail-closed semantics | 5s timeout; six failure modes all treated as mismatch; severity=critical security event with reason; risk-class-tiered scanner behavior | ✓ Resolved |
| 2 | Telegram alert on mismatch / verification failure | Two distinct message templates; high-priority alert queue; safe-stop fallback if Telegram cannot be restarted | ✓ Resolved |
| 3 | Manifest registration mode enforcement | Separate CLI tool (`tools/register_manifests.py`); not imported by main runtime; not callable from Telegram; runtime fail-closed on mismatch | ✓ Resolved (stronger than asked) |
| 4 | Cloud-model vs local TokenEstimator coordination | Result Verifier checkpoint invokes local TokenEstimator as source of truth; deterministic harness supplies estimate/mode/margin/pass to verifier context; same estimator at checkpoint and dispatch | ✓ Resolved |
| 5 | SQLite WAL mode | `PRAGMA journal_mode=WAL` + `synchronous=FULL` + `busy_timeout=5000` on every connection; boot abort if WAL cannot be enabled | ✓ Resolved |
| 6 | Calibration workflow dependency acknowledgement | Workflow steps enumerated; Kimi sequencing requirement explicit; interim MVP behavior specified | ✓ Resolved |
| 7 | Test list reconciliation | Architect restored seven tests, but not the seven I called out | ⚠ Partial — see below |

### Specific verification notes

**Item 3 — separate CLI is stronger than command-line flag.** A flag still requires registration code in the autonomous runtime. The CLI approach removes the registration code from the runtime surface entirely, so no compromised runtime path can re-enable registration regardless of how it manipulates state. This is a better Core Value 1 boundary than the synthesis required.

**Item 4 — the deterministic harness pattern resolves the gap by construction.** The cloud Result Verifier reasons about plan quality but does not calculate the token gate; the harness supplies `token_estimate / tokenizer_mode / required_margin / budget_pass` to the verifier context. This means checkpoint approval and dispatch enforcement use the same TokenEstimator output by construction. Cloud-model self-reported token reasoning is not in the trust path. There is a residual subtlety — at checkpoint time the actual prompt isn't fully built (Context Builder runs at dispatch with retrieved memory), so checkpoint estimates a planned shape and dispatch estimates the realized prompt — but the manifest cap is the contract between them and the planner-sizing rule from v1.10 §11 (≤50% / ≤66% target vs cap) gives the necessary headroom. The architecture hangs together.

**Item 5 — `synchronous=FULL` is defensible but worth flagging.** WAL + FULL is the safest combination for write durability but slower than WAL + NORMAL (the SQLite-recommended default for WAL). For audit-log-critical writes, FULL is justified. On SATA SSD with paging concerns, this can compound write latency — but in the sequential single-task model, write contention is bounded. Not blocking, but Kimi should know that NORMAL is a known-safe alternative if FULL produces measurable performance issues during testing.

**Item 6 — workflow dependency is now explicit and Kimi-actionable.** The interim MVP behavior (safe-pass disabled, high-risk → quarantine, ordinary uncertain → human input) gives Kimi a clear bootstrap state to plan against.

---

## What Needs Correction — Item 7

The architect's mapping table (§8) restores these tests, claiming they were the missing v1.9 tests:

- `test_artifact_risk_classification.py`
- `test_privileged_task_class_closed_set.py`
- `test_model_gateway_provider_timeout.py`
- `test_operator_capability_restart_rebind.py`
- `test_provider_usage_orphan_all_sessions.py`
- `test_classifier_embedded_instruction_no_rule_hit.py`

These are valuable tests and their inclusion is appreciated. But they are **not** the seven tests I flagged as missing in my v1.10 evaluation. The seven I called out were:

| Test from v1.9 §14 | Status in v1.10.1 canonical suite |
|---|---|
| `test_sandbox_heartbeat_ordering.py` | Still missing |
| `test_calibration_set_ownership_metadata.py` | Still missing (and would need renaming to reflect Gemini authorship per Item 1) |
| `test_task_committer_validation_scope.py` | Still missing |
| `test_checkpoint_semantic_consistency.py` | Still missing |
| `test_operator_control_manifest_binding.py` | Plausibly subsumed by `test_operator_control_authorization_chain.py` (steps 5–6 of the chain are manifest binding) — should be stated |
| `test_supervisor_liveness_limit_notice.py` | Still missing |
| `test_mvp_module_boundary.py` | Still missing |

Some are arguably consolidable. Others test distinct semantics that the architecture's behavior depends on:

- **`test_checkpoint_semantic_consistency.py`** is the test that proves Result Verifier owns what TaskCommitter does not (the architectural separation introduced in v1.9 Item 4). Losing it leaves that boundary unverified — the very boundary that resolved one of the original blocking items.
- **`test_task_committer_validation_scope.py`** proves TaskCommitter does deterministic validation only and rejects semantic checks. Distinct from atomicity.
- **`test_sandbox_heartbeat_ordering.py`** proves post-sandbox heartbeat completes before subsequent blocking operations. Distinct from freshness — freshness checks the field updates; ordering checks the sequence.
- **`test_supervisor_liveness_limit_notice.py`** proves the keepalive emission and the operator-side rule are both implemented. Without this, Item 7 of v1.10 (keepalive reframing) is documented but unverified.
- **`test_mvp_module_boundary.py`** proves the MVP module list excludes deferred Phase 2 components. This is the only test that asserts MVP scope is held — without it, scope creep is undetected.

**Required correction:** the Architect produces a v1.10.1 footnote (or v1.10.2 minimal patch) that does one of:
(a) adds these seven tests (or appropriately renamed equivalents) to the canonical suite, or
(b) maps each to a consolidated successor in the existing suite with a one-line rationale per test, or
(c) defends the omission of any specific test with an explicit rationale tied to architecture behavior.

This is bookkeeping, not architecture. It does not require restarting the panel cycle. But it cannot be left as-is, because Kimi will treat the canonical suite as canonical and these behaviors will go unverified.

---

## Core Value Compliance

| Value | Status |
|---|---|
| CV1 — Security baked in | **Strongly strengthened** — fail-closed fingerprint verification, Telegram alerts on security events, registration boundary entirely out of autonomous runtime, deterministic budget gate, WAL mode preserves supervisor monitoring availability |
| CV2 — Local model in lane | Unchanged |
| CV3 — Zero-trust at boundaries | **Strengthened** — manifest registration outside the autonomous runtime is a clean zero-trust pattern |
| CV4 — Build simple, prove concept, iterate | **Strengthened** — patches are minimal and targeted; calibration workflow dependency acknowledged honestly without inflating scope |
| CV5 — Queue-mediated coordination | Unchanged |
| CV6 — Sandbox/network separation | Unchanged |

No conflicts.

---

## Decision

**v1.10.1 advances on substance** with the test-list correction outstanding. Recommended panel routing:

1. **Architect produces footnote/addendum** addressing the seven specific tests I flagged. This is a 1-page document, not a new revision. It can be appended to v1.10.1 directly without restarting the cycle.
2. **Critic (DeepSeek) — bounded delta review** on the patches: did v1.10.1 resolve the six v1.10 critique items (Obj 1, 2, 3, 4, 5, 6)? Any new issues introduced by the patches themselves? The Critic's Obj 4 (cloud-model token coordination) was the most substantive; v1.10.1 §5 should satisfy that concern by construction.
3. **Arbiter — skippable.** v1.10.1 introduces no new factual mechanisms. SHA256, Ollama metadata via `/api/show`, tiktoken, SQLite WAL, command-line subprocess invocation are all standard mechanisms surrounding context already factually cleared.
4. **Constraints — skippable.** v1.10.1 adds no new threads, no new RAM-resident components, and the WAL mode change reduces lock contention rather than adding overhead. The separate registration CLI runs only when AXIOM is stopped, so it has no concurrent runtime cost.
5. **Synthesis (this seat)** — confirm delta cycle clean and the test-list addendum delivered.
6. **Implementation planning (Kimi).**

The architect's overall trajectory across five cycles has been productive and converging. v1.10.1 substantively closes the security and coordination gaps. The remaining test-list bookkeeping should be a one-page correction, not a new revision cycle.

Patch the test list, run the bounded delta-Critic review, then advance to Kimi.

---

*AXIOM Evaluation v1.10.1 — May 2026 — save as `AXIOM_Evaluation_v1_10_1.md`*