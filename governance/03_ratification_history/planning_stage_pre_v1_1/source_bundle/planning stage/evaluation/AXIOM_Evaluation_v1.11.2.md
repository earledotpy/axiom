# Evaluation of AXIOM_Proposal_v1.11.2 (Chief Architect)

## Verdict

**Approve with one targeted Architect fix before sending to Critic.** The proposal addresses all ten items I flagged on v1.11.1 and resolves the central capability/policy ambiguity by elimination rather than precedence, which is the right architectural choice. One new privilege-escalation surface remains in the schema and should be closed at the JSON Schema layer before adversarial review. Several smaller items are flag-worthy but properly Critic or Constraints Reviewer territory.

---

## What Holds

**The capability/policy resolution is the strongest move in this revision.** The Architect didn't just define precedence — they removed `network`, `sandbox`, and `memory` branches from `allowed_capabilities` entirely. With `additionalProperties: false`, any manifest attempting to express resource permission in both places fails JSON Schema validation before registration. There is no runtime "which wins?" question because the duplication is impossible to author. This aligns with CV3 (zero-trust at every agent boundary) and CV1 (security baked in) at the highest possible leverage point.

The remaining `allowed_capabilities` branches (`model`, `task_queue`, `filesystem`, `operator_control`) are authoritative for concerns that don't have top-level policy objects. No duplication remains.

**Wildcard semantics are now schema-enforced.** `"*"` is the only legal wildcard string; `"all"`, `"any"`, etc. fail validation. The `oneOf: [{const: "*"}, {actual type}]` pattern at the schema level is the right place — typos cannot reach the runtime. The matching rules in §2.2 are unambiguous: field equality OR `"*"`, with explicit ordering for path_prefix and methods.

**Allowlist non-empty rule is implemented as JSON Schema `if/then`.** When `mode == "allowlist_only"`, `allowlist.minItems = 1`, `timeout_seconds.minimum = 1`, `max_response_bytes.minimum = 1`. When `mode == "deny_all"`, `allowlist.maxItems = 0`, `timeout_seconds.const = 0`, `max_response_bytes.const = 0`. This is *more* than I asked for and is correct — a stale allowlist entry in deny_all mode would have been a privilege-leak vector.

**TOOL_CAPABILITY_MAP gives PolicyEngine a single source of truth** for tool→permission resolution. Adding a new tool requires panel approval, map entry, schema compatibility check, and PolicyEngine test. Good governance discipline. The four-step authorization rule (in `allowed_tools` AND not in `forbidden_tools` AND in MAP AND mapped check passes AND additional checks pass) provides defense-in-depth that is consistent across all tools.

**Task state lifecycle is well-specified.** The `tasks.manifest_id` lifecycle table at §4.2 is precise. The state-machine enforcement function is correct.

**Sparse vec0 invariant is well-modeled.** The transactional write sequence (insert items row → compute → atomic insert vec0 row + update embedding_status) is correct. Soft-delete preserves audit history while removing the embedding from retrieval. CV1-aligned.

**All 10 Evaluator-flagged items are addressed.** The summary table in §8 maps cleanly to my v1.11.1 evaluation.

---

## What Fails

### One issue should be resolved before Critic review

**Role manifests can declare arbitrary `allowed_capabilities.operator_control.allowed_commands`.** This is a privilege-escalation surface that the schema does not close.

Walk the path: a role manifest (e.g., `role.goal_planner.v1`) declares `allowed_commands: ["shutdown_after_current"]` and adds `session_controller.shutdown_after_current` to `allowed_tools`. The schema accepts this — `allowed_commands` is a free-form array of strings with `uniqueItems: true` and no other constraints. ManifestBinder computes effective capabilities, sees `allowed_commands` includes the command, sees `allowed_tools` includes the tool, and per `TOOL_CAPABILITY_MAP[session_controller.shutdown_after_current]` the authorization check is "manifest's allowed_commands contains 'shutdown_after_current'." It passes. The goal planner can now shut down AXIOM.

The example role manifest happens to set `allowed_commands: []`, but example correctness is not enforcement. CV1 says security is baked in, not bolted on; this gate currently lives in the manifest author's discipline rather than the schema.

This is structurally the same kind of issue the Architect just resolved for network/sandbox/memory: an authorization that should be impossible to express across role boundaries is currently expressible. The fix is the same shape — schema-level enforcement.

**Required fix:** Add `if/then` constraints to the manifest schema:

- For role manifests (`manifest_type == "role"`): `allowed_capabilities.operator_control.allowed_commands.maxItems = 0`.
- For operator control manifests (`manifest_type == "operator_control"`): `allowed_capabilities.operator_control.allowed_commands` must equal exactly `[operator_command.command_name]`. JSON Schema 2020-12 supports this via `$ref` to `operator_command.command_name` or a runtime ManifestBinder validator if pure schema doesn't compose. If the schema cannot enforce the cross-field equality, ManifestBinder must enforce it at registration.

Add corresponding tests:
- `test_role_manifest_rejects_nonempty_allowed_commands.py`
- `test_operator_control_manifest_allowed_commands_matches_command_name.py`

---

### Items to flag for Critic and Constraints Reviewer (not blocking)

**`redirect_policy: "same_host_only"` host-matching semantics.** §2.2 defines evaluation order ("redirect policy is evaluated after initial allowlist match") but does not define what "same host" means. Is it the originally requested URL's host, or the matched allowlist entry's host? The two are usually identical, but for an allowlist entry like `host: "*.example.com"` (which the schema does not currently support but might later) the distinction matters. Specify before Brave Search NetworkGateway implementation.

**Operator control manifest redundancy.** An operator control manifest names its command twice: `operator_command.command_name = "status"` and `allowed_capabilities.operator_control.allowed_commands = ["status"]`. The pair is consistent in the example but the schema does not enforce equality. ManifestBinder should validate. The fix above subsumes this.

**`scheduler_heartbeat` unbounded growth.** Log-table model writes a row per scheduler tick. At one tick per few seconds over multi-day autonomous sessions, this becomes hundreds of thousands of rows. The latest-read query is fast (covered by the new index), but disk space on a constrained SATA SSD machine is a real concern. Constraints Reviewer (Qwen) should weigh in on retention. Possible mitigation: periodic prune of heartbeats older than N days, or session-end archival.

**`memory_items` soft-deleted unbounded growth.** Same retention concern. Soft-deleted rows accumulate forever per the RESTRICT-only deletion model. For MVP this is fine; for multi-month operation it is not. Defer to Constraints Reviewer.

**`tasks.manifest_id` could be DB-CHECK enforced in addition to state-machine enforcement.** A `CHECK (status NOT IN ('running', 'completed', 'blocked_resource_limit') OR manifest_id IS NOT NULL)` would make the invariant database-level rather than code-level. CV1 leans toward this; the Architect chose code-level only. Defensible either way, but worth raising.

**`tool_capability_map.py` is part of the security boundary but is not fingerprinted.** Manifests are SHA256-registered; the TOOL_CAPABILITY_MAP that interprets them is not. If the map drifts from the panel-approved version (unintentional commit, merge error), the entire authorization layer is silently changed. Either fingerprint it like manifests, or reference its panel-approved version in `schema_migrations`. This is a CV1 hygiene item.

**`commit_batch_id` on the tasks table** is declared in the schema but its lifecycle is not documented in v1.11.1 or v1.11.2. Probably written by TaskCommitter for atomic batch inserts. Document in the next revision or in Kimi's implementation plan.

---

## Conflicts with Core Values

**CV1 (security baked in):** Strong overall. JSON Schema validation rejects ambiguous manifests at registration time. State machine enforces manifest binding before execution. Sparse vec0 invariant preserved. Provider enum prevents typo-based budget evasion. **Partially compromised** by the operator_control privilege surface above — security is process-baked rather than schema-baked there.

**CV3 (zero-trust at every agent boundary):** The capability/policy precedence resolution removes the major ambiguity. The operator_control schema gap is the only remaining boundary issue.

**CV2, CV4, CV5, CV6:** No conflicts identified. CV6 specifically: `sandbox_policy.network_access` retains the const "denied" lock, and the network policy mode enum still admits only `deny_all` or `allowlist_only`.

---

## What Must Be Resolved

**Before Critic review:**

1. **Schema-level constraint preventing role manifests from declaring non-empty `allowed_commands`, and constraining operator control manifests to exactly `[command_name]`.** Add corresponding tests.

**Should resolve in same revision (small):**

2. Define `redirect_policy: "same_host_only"` host-matching semantics.
3. ManifestBinder validation that operator control manifests have `allowed_commands == [command_name]` (subsumed by #1 if implemented).
4. Document `commit_batch_id` lifecycle.

**Defer to Critic and Constraints Reviewer:**

5. `scheduler_heartbeat` retention (Constraints).
6. `memory_items` soft-deleted retention (Constraints).
7. DB-CHECK constraint on `tasks.manifest_id` (defense-in-depth choice; either Critic or Architect can rule).
8. `tool_capability_map.py` fingerprinting (Critic — privilege-escalation hygiene).

---

## Recommended Next Step

Return v1.11.2 to the Architect with item #1 above as a required fix and items #2–#4 as same-revision cleanup. The fix is small — a few JSON Schema if/then clauses analogous to the network mode work the Architect already produced in this revision.

After v1.11.3 (or whatever the Architect names the patched version), proceed to Critic for full privilege-escalation review including items #5–#8. The Critic is the right reviewer for the retention and fingerprinting concerns; flagging them now ensures DeepSeek has the right ammunition.

If the Architect agrees that #1 is structurally identical to the resolved capability/policy issue and prefers to fold it into the v1.11.2 record rather than producing v1.11.3, that is also acceptable — the proposal's overall direction is correct and one schema-level patch should not require a full panel cycle restart.