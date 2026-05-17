# Evaluation of AXIOM_Proposal_v1.11.1 (Chief Architect)

## Verdict

**Return for targeted Architect revision before sending to Critic and Constraints Reviewer.** The bulk of the proposal is rigorous spec completion that addresses Gap 1, Gap 2, and the fingerprint registration omission cleanly. But the manifest schema contains a real coherence problem — duplicated authorization surfaces with unspecified precedence — that cannot be resolved by adversarial review alone. It needs an Architect ruling first.

---

## What Holds

The proposal correctly preserves the architecture spine and addresses every item the Evaluator flagged on v1.11:

**Gap 1 — Schema work is largely well-executed.** Concrete CREATE TABLE statements with explicit CHECK constraints, RESTRICT on every audit-critical relationship, named foreign keys, indexes matching the documented query patterns. The migration ledger (`schema_migrations`) is a forward-looking addition that costs nothing and supports future versioning.

**The `manifest_id` naming collision is correctly resolved.** Row PK becomes `fingerprint_id`, logical identifier remains `manifest_id TEXT NOT NULL UNIQUE`. Task and permission rows reference the logical identifier. This was Evaluator concern #3; resolved.

**`tasks.status` and `plan_artifacts.artifact_status` are properly separated.** `checkpoint_blocked` is correctly placed at the artifact tier, not the task tier. Decision C's distinction between `checkpoint_failed` (semantic verdict) and `checkpoint_blocked` (security prerequisite missing) is a clean separation that matches v1.10.2 §1.

**sqlite-vec virtual table is correctly modeled.** `memory_item_embeddings USING vec0(embedding float[768])` with the rowid invariant `memory_item_embeddings.rowid == memory_items.memory_item_id` is the canonical sqlite-vec pattern. Replaces Kimi's incorrect BLOB column.

**Scanner return contract correction (§1.3).** Explicit four-field return — `scanner_result`, `risk_class`, `artifact_status`, `parent_task_status`, `reason` — matches the v1.10.2 §1 two-tier lifecycle. Resolves Evaluator concern #3.

**Initial fingerprint registration mechanism (§3).** CLI tool analogous to `register_manifests.py`. The calibration → register → boot sequencing dissolves the circular dependency. Transactional supersede+insert with partial unique index `idx_model_profile_one_current` enforces "exactly one current profile per label" at the database layer rather than at the application layer. Quantization extracted from the Ollama response, not hardcoded. Fail-closed on `thinking_mode = "unknown"`. Resolves Evaluator concerns #1 and #2.

**Profile hashing rule (§3.5).** Smart approach — explicit selected-profile object with field-level SHA256 components rather than blind-hashing the full `/api/show` response. This sidesteps the volatility problem (Ollama might add fields between releases) without weakening the security boundary.

**Gap 3 explicitly held back.** `infer_thinking_mode_from_arbiter_rule()` is left as an interface stub. Architect does not guess. Correct discipline.

**Manifest schema deny-by-default principles.** Decision B (forbidden wins) and Decision C (missing capability = deny) are correct security defaults. `additionalProperties: false` everywhere. `audit_policy.log_policy_denials: const true` and `log_task_id: const true` prevent manifests from disabling audit at the schema level. `authorization_policy.telegram_operator_whitelist_required: const true` prevents an operator command manifest from skipping the whitelist check. These hardcoded truths align with CV1.

**Network allowlist uses structured endpoint objects, not URL strings.** Decision D is meaningfully more secure than string matching — explicit scheme, host, port, path_prefix, methods, purpose. Aligns with CV6. The `redirect_policy: deny | same_host_only` enum forecloses a common bypass class.

**`manifest_id` regex pattern.** `^(role|operator)\.[a-z0-9_]+\.v[0-9]+$` enforces canonical naming and prevents typo-aliasing.

---

## What Fails

### Major: capability/policy duplication with unspecified precedence

This is the issue that needs an Architect ruling before the proposal advances.

The manifest schema defines authorization for several resources in **two places** with overlapping but non-identical fields:

| Resource | `allowed_capabilities.X` field | Top-level `X_policy` field |
|---|---|---|
| Network | `allowed_capabilities.network.fetch` (boolean) | `network_policy.mode` + allowlist + denylist + redirect_policy + timeout + max_response_bytes |
| Sandbox | `allowed_capabilities.sandbox.execute_code` (boolean) | `sandbox_policy.allowed` + max_ram_mb + max_wall_clock_seconds + network_access |
| Memory | `allowed_capabilities.memory` (read, write, max_results, dedupe_required_on_write) | `memory_policy` (read, write, **max_query_results**, **write_requires_dedupe**) |

The memory case is especially concerning — the field names differ between the two representations (`max_results` vs `max_query_results`, `dedupe_required_on_write` vs `write_requires_dedupe`). This is not "summary plus parameters"; it is the same boolean stated twice with different keys.

What happens when they disagree? `allowed_capabilities.memory.write = false` but `memory_policy.write = true` — which wins? The proposal does not say. The PolicyEngine and ManifestBinder need a single source of truth, and the schema as written gives them two.

This violates CV3 (zero-trust at every agent boundary): an ambiguous permission boundary is no permission boundary. It also creates a privilege-escalation seam — an attacker (or a buggy author) can produce a manifest that passes JSON Schema validation but means different things to different consumers.

**Required Architect ruling:** Pick one model.

- *Option A:* `allowed_capabilities` is the binary "is this capability available at all" gate; `X_policy` carries the parameters when it is. Memory has no boolean, just `memory_policy`. Network has no `allowed_capabilities.network.fetch` — it is implied by `network_policy.mode != "deny_all"`.
- *Option B:* The capability layer is summary/derived from `X_policy`; ManifestBinder computes capabilities from policies and rejects manifests where the two disagree.
- *Option C:* Both are authoritative and must agree; manifest validation fails if they disagree.

Whichever the Architect picks, the proposal must explicitly state precedence rules and ManifestBinder behavior on disagreement.

### Major: wildcard semantics in denylist are undefined

The `network_deny_entry` schema permits:

- `port: ["integer", "string"]`
- `scheme: "string"` (no enum)
- `path_prefix: "string"` (no pattern)

The example role manifest in §2.6 uses `"port": "*"`, `"scheme": "*"`, `"path_prefix": "*"`. But nowhere in the proposal is `"*"` defined as a wildcard string. Could just as easily be `"any"` or `"wildcard"`. NetworkGateway implementation must know which strings match what — and right now Kimi has to guess.

This is a correctness problem (different implementations will diverge) and a security problem (a manifest author writing `"port": "all"` thinking it means wildcard will silently match nothing in the denylist).

**Required:** Define wildcard semantics explicitly in the JSON Schema and the proposal text. Either:
- Add a `"wildcard": true/false` flag to deny entries, or
- Use a sentinel like `"port": -1` for wildcards, or
- Define `"*"` as the only legal wildcard string and add `pattern` constraints to the schema.

### Major: `allowlist_only` mode with empty allowlist is a silent footgun

The schema permits `network_policy.mode = "allowlist_only"` with `allowlist: []`. This is fail-secure — nothing is allowed — but it is also a misconfiguration that the schema does not catch. A manifest author intending to allow Brave Search but who forgets to populate the allowlist gets a manifest that validates, registers, and silently blocks all network calls.

**Required:** Add a JSON Schema conditional: `if mode == "allowlist_only" then allowlist minItems: 1`. JSON Schema 2020-12 supports `if/then/else` keywords. This makes the misconfiguration impossible to register.

### Minor: tool-to-capability mapping is unspecified

Decision B says: *"tool allowed only if: tool ∈ allowed_tools AND required capability branch allows operation AND tool ∉ forbidden_tools."* But there is no canonical mapping from `tool_id` (e.g., `network_gateway.fetch`) to `required capability branch` (e.g., `allowed_capabilities.network.fetch`). The PolicyEngine has to know that mapping, but the proposal leaves it for Kimi to invent.

This is acceptable as an implementation note, but should be stated explicitly: *"PolicyEngine maintains a static tool→capability mapping table. Adding a new tool requires a panel-approved entry in that table."* Otherwise it drifts.

### Minor: schema-level items to clean up

- **`scheduler_heartbeat` write pattern.** Schema is a log (no UNIQUE on session_id). v1.9 implied a single "current" row. Either intent is workable, but the read pattern (`SupervisorMonitor reads last_freshness_at`) needs a `created_at DESC LIMIT 1` query and a matching index. Document which is the read pattern.
- **`tasks.manifest_id` is nullable** but every executable task must have one. Specify the lifecycle: when is it null vs set, what state transitions imply binding.
- **`schema_version`** for the initial migration row is unspecified. Pin a value, e.g., `"v1.11.1"`.
- **`provider_usage.provider`** is free-text. A typo creates a phantom provider silently. Add a CHECK constraint with the cascade enum (`cerebras, groq, openrouter, sambanova`) or document that it's intentionally open for future providers.
- **`memory_items.embedding_status = 'pending'`** has no defined relationship to `memory_item_embeddings`. Does ManifestBinder/MemoryGateway write a placeholder vec0 row, or does the virtual table stay sparse until indexing completes? Document.
- **`network_policy.timeout_seconds: 0`** in the deny_all status example. Define whether `0 = unlimited` or `0 = immediate timeout`. For deny_all manifests it's moot, but the convention matters.

---

## Conflicts with Core Values

**CV1 (security baked in).** Generally upheld. Audit fields are hardcoded const true; manifests are SHA256-fingerprinted; model fingerprints are tied to passing calibration runs. The capability/policy duplication issue partially undermines this — security designed-in requires unambiguous boundaries.

**CV3 (zero-trust at every agent boundary).** Largely upheld by deny-by-default and forbidden-wins rules. **Partially compromised** by the duplicated authorization surface (#1 above). Cannot pass for Kimi until resolved.

**CV6 (sandbox and network never directly connected).** Upheld. `sandbox_policy.network_access: const "denied"` and structured allowlist endpoints are stronger than the legacy build's posture.

**CV2, CV4, CV5.** No conflicts identified.

---

## What Must Be Resolved

**Architect must rule on, before this proposal advances:**

1. **Capability/policy precedence.** Pick Option A, B, or C above (or another) and state ManifestBinder behavior when the two layers disagree. Update the JSON Schema accordingly.
2. **Wildcard semantics in denylist.** Define `"*"` (or replace with a structured wildcard mechanism) and add schema constraints.
3. **Allowlist non-empty when `mode = "allowlist_only"`.** Add JSON Schema `if/then` constraint.

**Architect should clean up in same revision:**

4. Tool-to-capability mapping note (where it lives, how it is updated).
5. `scheduler_heartbeat` read pattern and matching index.
6. `tasks.manifest_id` lifecycle documentation.
7. Initial `schema_version` value.
8. `provider_usage.provider` constraint or explicit-open documentation.
9. `memory_items.embedding_status` ↔ `memory_item_embeddings` invariant.
10. `network_policy.timeout_seconds: 0` semantics.

**Defer to Critic and Constraints Reviewer after revision:**

The Critic (DeepSeek) should attack the revised manifest schema for privilege-escalation paths, particularly around `granted_capabilities_json` storage in `task_permissions` and any remaining ambiguity in tool/capability resolution. The Constraints Reviewer (Qwen) should confirm that 17 tables + WAL + indexes + the vec0 virtual table fit comfortably in the 2.0–2.3 GB headroom (almost certainly yes — SQLite is small in RAM, and nomic-embed-text 768-dim is already part of the observed baseline). Gap 3 remains routed to Gemini separately.

---

## Recommended Next Step

Return v1.11.1 to the Architect with the three required rulings (capability/policy precedence, wildcard semantics, allowlist-non-empty) plus the seven cleanup items. After the Architect produces v1.11.2, run the standard panel cycle: Evaluator delta-confirm → Critic → Arbiter (only if new factual claims arise) → Constraints Reviewer. If all pass, fold in Gemini's separate Gap 3 ruling and route to Kimi for v1.12.

The schema work and fingerprint registration mechanism are solid enough that I do not expect the second revision to be large. The capability/policy ruling is the only item that could plausibly reshape parts of the manifest schema; the rest are edits.