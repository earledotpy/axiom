# Evaluation of AXIOM_Implementation_v1.11 (Kimi K2.6)

## Verdict

**Return for revision before implementation queue acceptance.** The plan correctly identifies 7 gaps but then partially contradicts itself by directing the operator to commit work that depends on those unresolved gaps. There are also two structural defects that Kimi did not flag.

---

## What Holds

The plan is faithful to the approved spine on the items it does specify concretely:

- **WAL mode and PRAGMAs** match v1.10.1 §6 / v1.10.2 §3.2 exactly. Adding `foreign_keys=ON` is a reasonable extension.
- **Manifest registration CLI** is correctly placed outside the autonomous runtime per v1.10.1 §4. The boundary requirement is respected.
- **Fingerprint guard timeout = 5s, fail-closed on timeout/connection/malformed/schema** matches v1.10.1 §2.
- **Telegram alert path** for fingerprint mismatch/failure aligns with v1.10.1 §3.
- **Safe-pass session state with `safe_pass_alert_sent` deduplication** matches v1.10.2 §2.
- **Scanner short-circuit** when `safe_pass_enabled=False` skipping the fingerprint guard call matches v1.10.2 §2 verbatim.
- **Core Values alignment** — security threaded through Tasks 1–3 (boot-time manifest integrity, pre-decision fingerprint verification) honors CV1, CV2, CV3.
- **Gap honesty** — Kimi correctly refuses to invent answers for genuinely unspecified items (calibration test set, sandbox Job Object internals, cloud cascade auth, operator whitelist mechanism).

---

## What Fails

### Structural defects Kimi did not flag

**1. Initial fingerprint registration workflow is missing.** Task 3 implements `verify_current_profile()` which calls `profile_repo.get_current()` to retrieve the calibrated fingerprint to compare against. But there is no mechanism in the plan to *write* that initial fingerprint. On first boot, `get_current()` returns nothing → `_handle_failure(reason="no_stored_profile")` → safe-pass disabled forever.

This is a circular dependency. The plan needs a parallel CLI tool — `tools/register_model_fingerprint.py` — analogous to `register_manifests.py`, run after calibration passes, before AXIOM enters autonomous operation. This is a structural omission, not a "gap."

**2. `_extract_quantization()` is hardcoded to `"Q4_K_M"`.** This silently defeats part of the fingerprint security boundary. If the operator changes the Ollama model to a different quantization, this function returns the same constant string, so quantization mismatch will not be detected. Quantization must be extracted from the Ollama `/api/show` response (typically the `details.quantization_level` field), not returned as a literal.

**3. `PlanInjectionScanner.scan()` conflates artifact state and parent task state.** v1.10.2 §1 explicitly defines a two-tier state on fingerprint failure:

| Risk class | Plan artifact state | Parent task state |
|---|---|---|
| high_risk | quarantined | quarantined |
| ordinary | checkpoint_blocked | needs_human_input |

Kimi's scanner returns a single `decision` field with values like `"quarantined"` or `"checkpoint_blocked"`. The caller has no way to know the parent task should transition to `needs_human_input` when the artifact is `checkpoint_blocked`. The scanner contract must return both states, or the calling code must encode the mapping — neither is specified in the plan.

**4. `_apply_classifier()` is called in `scan()` but never stubbed.** A concrete code path references an undefined method. Minor, but the plan presents itself as executable.

**5. Task 3 tests are all negative-path.** No test verifies that a *matching* profile returns `True`. At minimum, `test_model_fingerprint_guard_happy_path.py` is needed alongside the failure-mode tests.

### Self-contradictions in the plan

**6. Task 1 is presented as "foundational and reversible" but is not.** The closing recommendation says the operator may begin Task 1 immediately. This is misleading. Once `init_db()` runs and any session, task, manifest, or security event row is committed, schema changes require migration. The operator must not run Task 1 against an inferred schema (Gap #1). Either the plan should be amended to explicitly *propose* the schema for panel ratification before `init_db()`, or Task 1 should be split into "Task 1a: schema proposal for panel review" and "Task 1b: execute init_db after panel confirms."

**7. Task 2.2 directs the operator to create role manifests using the inferred JSON schema (Gap #2), which Kimi simultaneously flags as unconfirmed.** Once manifests are written and SHA256-registered, the schema is locked into the audit ledger. Changing it later requires re-registration, panel re-approval, and possibly invalidates calibration metadata. Task 2.2 must wait on Gap #2.

**8. Task 3 ships a `_infer_thinking_mode()` heuristic that Kimi flags as Critical (Gap #3).** The placeholder pattern (`"/no_think" in template`) is a guess. The proposal explicitly warned that incorrect inference causes false fingerprint mismatches *or* allows a thinking-enabled model to pass as disabled. The latter is a security boundary failure. Task 3 must wait on Gap #3.

### Schema-level issues to resolve when Gap #1 is taken up

These are not blocking by themselves, but they are concrete items the panel needs to settle when ratifying the schema:

- `tasks.status` enum is asserted but never canonically defined across v1.9–v1.10.2. The set in Task 1.3 (`pending, running, completed, failed, quarantined, needs_human_input, blocked_resource_limit`) is plausible but should be confirmed.
- `plan_artifacts.artifact_status` includes both `checkpoint_failed` and `checkpoint_blocked`. v1.10.2 §1 introduced `checkpoint_blocked` for the ordinary+safe-pass-disabled path. v1.10 §6 used `checkpoint_failed` for token-budget/checkpoint failure. Are these distinct states or duplicates? The schema commits to both without specifying when each applies.
- `manifest_fingerprints.manifest_id` is `INTEGER PRIMARY KEY` in the schema, but Task 2.1's JSON manifest example uses `"manifest_id": "goal_planner_v1"` as a logical string identifier. Two different things share a name. One needs to be renamed (e.g., `fingerprint_id` for the row PK, `manifest_id` for the logical name in the JSON, with a separate column on the table).
- `memory_items.embedding` is declared `BLOB`. sqlite-vec uses virtual tables, not a regular column. The schema needs a `vec0` virtual table declaration or equivalent.
- `ON DELETE` / `ON UPDATE` behavior is unspecified throughout. For audit-critical tables (`security_events`, `provider_usage`, `plan_artifacts`), the panel must decide whether cascades are allowed at all — for an immutable audit log, the answer is probably no.

### Carry-forward items from binding conditions

- The plan does not reference the **Brave Search API or panel-approved free-tier alternative** binding condition. Acceptable to defer to the gateway phase, but should be listed in the recommended sequencing for Phase 4.
- The plan does not reference **`test_sandbox_heartbeat_ordering.py`** (v1.10.2 §5). The heartbeat schema is sketched but the write-ordering invariant — heartbeat write must complete before any following blocking operation — is not addressed in the scheduler stub. Defer to Phase 2, but flag now so it is not lost.

---

## What Must Be Resolved Before Implementation Proceeds

**Panel-side resolutions required before Kimi produces a revised plan:**

1. **Gap #1 — Canonical database schema.** The Architect should produce a proposed schema for panel ratification. The Evaluator (me), Critic (DeepSeek), Arbiter (Gemini), and Constraints Reviewer (Qwen) need to delta-confirm. This is now the next required cycle.
2. **Gap #2 — Canonical manifest JSON schema.** Same panel cycle as Gap #1, or a parallel one.
3. **Gap #3 — Thinking-mode inference pattern for `qwen3:4b`.** The Arbiter (Gemini) is the right authority — this is a factual question about Ollama's `/api/show` output for `qwen3:4b` with thinking disabled. Until Gemini rules, Task 3 cannot be safely implemented.

**Kimi-side revisions required to the implementation plan:**

4. Add a `tools/register_model_fingerprint.py` CLI and document the calibration-then-register-then-boot sequence.
5. Replace the hardcoded `_extract_quantization()` with extraction from Ollama `/api/show` (likely `details.quantization_level`).
6. Rewrite `PlanInjectionScanner.scan()` return contract to express both artifact state and parent task state per the v1.10.2 §1 table.
7. Add a stub for `_apply_classifier()`, even if it always returns `passed` until calibration exists.
8. Add at least one positive-path fingerprint guard test.
9. Restructure the closing sequencing note: Task 1 is *not* safe to execute against the inferred schema; only directory creation, `requirements.txt`, and the `db.py` connection-layer code are reversible. `init_db()` waits on panel ratification of Gap #1.

**Gaps #4–#7 (calibration test set, Windows Job Object specifics, cloud cascade config, Telegram operator whitelist) are correctly flagged and can remain deferred.** They block later phases but not the revised Tasks 1–3.

---

## Recommended Next Step

Route this back to the Architect (GPT-5.5) with two parallel asks:

- Produce a **canonical schema proposal** (Gap #1) and **canonical manifest JSON schema** (Gap #2) for full panel review.
- Route Gap #3 (thinking-mode inference for `qwen3:4b`) to the Arbiter (Gemini) for a binding factual ruling on what `/api/show` returns when thinking is disabled.

Once those three items are resolved, return to Kimi to produce **AXIOM_Implementation_v1.12** addressing items 4–9 above. The current v1.11 should not enter the implementation queue.