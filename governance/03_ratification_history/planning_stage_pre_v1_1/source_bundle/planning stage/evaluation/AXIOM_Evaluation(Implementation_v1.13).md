I need to see the truncated section of the tool capability map and verify a few more details before delivering the evaluation.

# Evaluator Review — AXIOM Implementation Plan v1.12

**Verdict: BLOCKED — return to Architect/Implementer with three coherence-critical defects.**

The structural work is sound: schema, manifest schema, tool-capability map, registration CLIs, Gap 3 integration, and seven-step authorization are all faithful to the approved proposal stack. But three defects break logical coherence between the scanner contract, the schema CHECK constraints, and the manifest_id regex. Two of these will cause the canonical acceptance tests to fail at first execution. The third corrupts the v1.10.2 two-tier lifecycle that v1.11.1 was specifically authored to repair.

---

## What Holds

**Schema fidelity (Section 3).** Matches v1.11.1 §1.2 with v1.11.4 amendments. Confirmed:
- All 17 logical tables plus the `memory_item_embeddings` virtual table using `vec0(embedding float[768])`.
- `PRAGMA cache_size = -32768` in both `schema.sql` and `_apply_pragmas()` (binding condition 11).
- ON DELETE behavior: `RESTRICT` on session/task/parent_task references; `SET NULL` on `scheduler_heartbeat.active_task_id`. Internally consistent with append-only semantics.
- `idx_model_profile_one_current` is a partial unique index `WHERE is_current = 1`, correctly enforcing the at-most-one-current invariant per profile_label.
- `manifest_fingerprints.manifest_type` CHECK admits all three types (`role`, `operator_control`, `tool_capability_map`), and the row-level CHECK enforces the correct (role+role_name) | (operator_control+command_name) | (tool_capability_map+neither) tri-state.

**Manifest schema (Section 4).** Faithful to v1.11.2 §2 with v1.11.3 and v1.11.4 patches. `additionalProperties: false` everywhere. Role manifests carry `allowed_commands.maxItems = 0`; operator-control manifests carry `minItems = 1, maxItems = 1`. Tool ID enum lists the canonical 14. `max_response_bytes.maximum = 5242880`. Conditional `allOf` blocks correctly enforce `deny_all → allowlist=[], timeout=0, bytes=0` and `allowlist_only → allowlist≥1, timeout≥1, bytes≥1`. Audit policy const-trues (log_task_id, log_manifest_id, log_policy_denials) all correct.

**Tool-capability map as security artifact (Sections 5, 6.1, 6.3, 10.3).** Loaded from `axiom/policy/security_artifacts/tool_capability_map.json`, not a Python literal. Validated against `axiom.tool_capability_map.v1` schema in `register_manifests.py` before any manifest is touched. Registered as a third row type in `manifest_fingerprints` with `manifest_id = security.tool_capability_map.v1`, `manifest_type = tool_capability_map`. `ManifestBinder._bootstrap()` fails closed at boot if the map row is missing. Cross-field semantic validation (`required_command` matches tool suffix) is enforced. Loader caches once per process (binding condition 8).

**Gap 3 implementation (Sections 6.2, 7, 8).** Correct. `_infer_thinking_mode()` inspects `parameters` only with regex `(?i)^\s*think\s+false\s*$` and `re.MULTILINE`, returns `disabled` or `unknown`. `register_model_fingerprint.py` rejects unless `thinking_mode == "disabled"` (the v1.11.4 §9.3 invariant). `ModelGateway.call_local_ollama()` rejects caller `think=true` and unconditionally injects `think=false` after the override check.

**Seven-step authorization (Section 10.2).** All seven steps present. Step 6 includes both the v1.11.3 manifest_type guard and the cross-field `command_name ∈ allowed_commands` equality check. Stateless boot-time-cached `_valid_tool_ids`. `PolicyEngine.validate_manifest_completeness()` (Section 10.4) fails closed on missing required policy fields per v1.11.4 §5.

**Initial fingerprint registration workflow.** `register_model_fingerprint.py` correctly: verifies calibration_run_id exists and `passed = 1`, queries `/api/show` via `requests.post`, extracts `quantization` from `details.quantization_level` (not from a literal), atomically supersedes the prior `is_current = 1` row, inserts new row + `security_events` entry, and rolls back on any error.

**Sequencing safety.** Task 1 is reversible: it creates only the directory tree, `db.py`, and `requirements.txt`. `init_db()` raises `RuntimeError` when `schema.sql` is missing — gate is real, not advisory. Task 2 is gated on `schema.sql` being on disk. Manifest and tool-capability-map registration are gated on schemas being written before `register_manifests.py` runs.

**Deferred items honestly flagged (Sections 1 and 13).** All four carry-forward items — Brave Search confirmation, calibration test set authoring, Windows Job Object specifics, cloud cascade configuration, Telegram operator whitelist — are explicitly listed as deferred with their blocking phase. v1.12 does not silently consume work product from any of them; classifier safe-pass remains disabled, sandbox enforcement is acknowledged as TBD, cloud paths are flagged as Phase 4, and the operator-whitelist field is enforced as a const-true schema requirement without claiming the storage mechanism exists.

**Constraints conditions (Section 2).** All twelve binding conditions from `AXIOM_Constraints_v1.11.3.md` are mapped to enforcement locations. Schema enforces `sandbox_policy.max_ram_mb ≤ 256` and `max_wall_clock_seconds ≤ 60`. The `additional_check` enum in the tool-capability map matches the binding-condition surface.

---

## What Fails

### Failure 1 — `manifest_id` regex is malformed (CRITICAL)

**Location:** Section 4, line 915.

**Canonical (v1.11.1 §2.5):**
```
"pattern": "^(role|operator)\\.[a-z0-9_]+\\.v[0-9]+$"
```
Unescaped: `^(role|operator)\.[a-z0-9_]+\.v[0-9]+$` — matches `role.goal_planner.v1` or `operator.status.v1`.

**Kimi v1.12:**
```
"pattern": "^(role|operator\\.)[a-z0-9_]+\\.v[0-9]+$"
```
Unescaped: `^(role|operator\.)[a-z0-9_]+\.v[0-9]+$`. The dot was moved *inside* the alternation, attached only to `operator`.

**Effect:**
- `role.goal_planner.v1` → REJECTED. The "role" branch matches the literal `role`, then expects `[a-z0-9_]+`, but the next char is `.`.
- `rolegoal_planner.v1` → ACCEPTED (incorrectly).
- `operator.status.v1` → ACCEPTED (still works, by coincidence).

This is a transcription error, not a design choice. Every canonically-formed role manifest fails JSON Schema validation at registration, which means `register_manifests.py` cannot ever populate the role rows, and Test #8 ("Manifest schema validates a correctly formed role manifest") fails on first run unless the test fixture itself uses the malformed identifier — which would be a cascading error.

### Failure 2 — `PlanInjectionScanner` safe-pass-disabled return contract diverges from v1.11.1 §1.3 (CRITICAL)

**Location:** Section 9, lines 2198–2212.

**Canonical (v1.11.1 §1.3) for ordinary risk class:**
```json
{
  "scanner_result": "safe_pass_disabled",
  "risk_class": "ordinary",
  "artifact_status": "checkpoint_blocked",
  "parent_task_status": "needs_human_input",
  "reason": "...",
  "details": {}
}
```

**Kimi v1.12 implementation:**
```python
{
  "scanner_result": ScannerResult.SAFE_PASS_DISABLED,
  "risk_class": RiskClass.ORDINARY,
  "artifact_status": ArtifactStatus.DRAFT,            # WRONG
  "parent_task_status": ParentTaskStatus.BLOCKED,     # WRONG and unpersistable
  "reason": (...),
  "details": {...},
}
```

This is the exact scanner-decision/artifact-state/task-state conflation that v1.11.1 §1.3 was authored to fix. v1.11.1's verbatim instruction: *"Kimi v1.11 conflated scanner decision, artifact state, and task state. That is incompatible with v1.10.2's two-tier lifecycle table. Kimi v1.12 must implement this explicit return contract."*

The acceptance test at row 47 is currently coded to assert the wrong values — line 2985: `assert result['parent_task_status'] == 'blocked'`. So the test "passes" only because both scanner and test are wrong in the same direction. Test #48 ("dict contains scanner_result, risk_class, artifact_status, parent_task_status, reason") passes structurally but is silent on whether the values are canonical.

There is also a **missing high-risk return path**. v1.11.1 §1.3 specifies a distinct return for high-risk artifacts:
```json
{ "artifact_status": "quarantined", "parent_task_status": "quarantined", ... }
```
Kimi's `scan()` has no high-risk safe-pass-disabled branch. The scanner method does not even take `risk_class` as input, so it cannot emit the high-risk disposition. Any caller that passes a high-risk artifact when safe-pass is disabled will receive an ordinary disposition — a silent privilege downgrade in the wrong direction (under-quarantines rather than over-quarantines).

### Failure 3 — `ArtifactStatus` and `ParentTaskStatus` enums are incomplete and contain invalid values (CRITICAL)

**Location:** Section 9, lines 2167–2178.

**Schema CHECK constraint (Section 3) for `plan_artifacts.artifact_status`:**
```
'draft', 'scanner_passed', 'checkpoint_passed', 'checkpoint_failed',
'checkpoint_blocked', 'quarantined', 'committed'
```

**Kimi `ArtifactStatus` enum:**
```
DRAFT, SCANNER_PASSED, QUARANTINED
```
Missing: `checkpoint_passed`, `checkpoint_failed`, `checkpoint_blocked`, `committed`. This is what makes Failure 2 unfixable in place — `checkpoint_blocked` (the canonical safe-pass-disabled artifact_status) is not even an enum member.

**Schema CHECK constraint (Section 3) for `tasks.status`:**
```
'pending', 'running', 'completed', 'failed', 'quarantined',
'needs_human_input', 'blocked_resource_limit', 'cancelled'
```

**Kimi `ParentTaskStatus` enum:**
```
PENDING, RUNNING, BLOCKED, NEEDS_HUMAN_INPUT
```
Contains the invalid value `BLOCKED` (no such state in the schema). Missing: `completed`, `failed`, `quarantined`, `blocked_resource_limit`, `cancelled`.

The scanner emits values that cannot be persisted. The string value `"blocked"` violates the `tasks.status` CHECK constraint. Any code path that writes the scanner's `parent_task_status` into the database raises `sqlite3.IntegrityError: CHECK constraint failed`.

---

## Other Concerns (non-blocking, flag for the record)

**Step 6 partial redundancy.** Step 2 of `authorize_tool_use()` already denies on `requires_manifest_type` mismatch. By the time Step 6 runs, `manifest_type == "operator_control"` is guaranteed for `session_controller.*` tools, so the inner `if manifest_type != "operator_control"` clause in Step 6 is dead code. The cross-field equality check (`command_name in allowed_commands`) remains useful. Defense in depth, not a defect, but worth noting.

**Ambiguity #2 in Section 13 has live consequences.** `register_model_fingerprint.py` does `str(show_json.get("parameters", ""))`. If Ollama returns `parameters` as a dict, `str(dict)` produces `"{'think': False}"` — which does not match `(?i)^\s*think\s+false\s*$`, so registration fails closed. That is acceptable behavior, but the §12.3.2 unit tests only exercise string inputs and never see this case. Recommend the Arbiter rule on the actual `parameters` shape and that the test suite cover both string and dict response variants.

**Test row 47/48/49 needs rewrite.** Once Failure 2 is fixed, the assertion `result['parent_task_status'] == 'blocked'` becomes wrong. Update to assert `'needs_human_input'` for ordinary and `'quarantined'` for high-risk.

---

## Must Be Resolved Before This Plan Enters the Implementation Queue

1. **Fix the `manifest_id` regex** in Section 4 to `^(role|operator)\\.[a-z0-9_]+\\.v[0-9]+$`. Add a test that `role.goal_planner.v1` validates and `rolegoal_planner.v1` does not.

2. **Reimplement `PlanInjectionScanner.scan()` to take `risk_class` as input** and emit the canonical v1.11.1 §1.3 contract for both ordinary and high-risk safe-pass-disabled paths:
   - ordinary → `artifact_status="checkpoint_blocked"`, `parent_task_status="needs_human_input"`
   - high_risk → `artifact_status="quarantined"`, `parent_task_status="quarantined"`

3. **Expand the enums** to cover the full schema CHECK domains:
   - `ArtifactStatus`: add `checkpoint_passed`, `checkpoint_failed`, `checkpoint_blocked`, `committed`.
   - `ParentTaskStatus`: remove the invalid `BLOCKED`; add `completed`, `failed`, `quarantined`, `blocked_resource_limit`, `cancelled`.

4. **Update tests #47–#49** to assert the canonical contract values, and add a test that exercises the high-risk safe-pass-disabled return path.

These are not stylistic. Items 1–3 each cause a hard runtime failure on first execution against the canonical schema, and item 2 reintroduces the exact failure mode v1.11.1 §1.3 was authored to eliminate. The plan does not enter the implementation queue with these defects. Return to Kimi for revision; no re-architecture is required, and v1.11.1 §1.3 already provides the exact contract to copy.