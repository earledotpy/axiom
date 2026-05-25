# Panel Synthesis — AXIOM v1.11.3 Review

## Verdict

**Return to the Architect for v1.11.4.** Three of DeepSeek's six objections are substantive schema-level fixes that must be resolved before implementation. The other three are valid observations that can be folded into the same revision as documentation/notes. Constraints approved with carry-forward conditions only; Arbiter cleared all factual claims with one implementation caveat for Kimi. The required revision is small enough to delta-confirm without a full panel re-cycle.

---

## (1) Valid Objections — Must Be Resolved

**DeepSeek #1 — `tool_capability_map.py` is not integrity-verified.** This is the strongest objection. The map IS the authorization layer — manifests SHA256-fingerprinted but the file that interprets them is not. An attacker with filesystem access (or a buggy merge, or a code-review miss) can silently change the security boundary. The Architect explicitly invited DeepSeek to attack this in §9 of v1.11.3; the attack lands cleanly. This violates CV1 (security baked in) at the same level the manifest fingerprinting addressed.

*Required fix:* Treat `tool_capability_map.py` as a security artifact. Either (a) SHA256 the .py file and add to `manifest_fingerprints` with a new `manifest_type = "tool_capability_map"`, verified at boot by ManifestIntegrityVerifier, or (b) generate the map from a JSON file already covered by the existing manifest fingerprinting. Option (b) is cleaner architecturally; option (a) is smaller in implementation scope. Architect picks.

**DeepSeek #3 — No upper bound on `max_response_bytes`.** Real RAM exhaustion vector. The schema permits `max_response_bytes: 1073741824` (1 GB), which would consume nearly half the available system RAM and force SATA SSD paging. This bypasses Qwen's binding condition #1 (no architectural change may drive system into paging). The 1 MB Brave Search example is a reasonable convention, but conventions aren't enforcement.

*Required fix:* Add `maximum: 10485760` (10 MB) or similar to the schema for `max_response_bytes`. The Architect picks the exact ceiling — Brave Search responses are typically <1 MB, so 5–10 MB is generous. Anything above that should require explicit panel approval.

**DeepSeek #5 — `allowed_tools` not constrained to canonical tool IDs.** Defense-in-depth gap. The schema's `tool_id` pattern `^[a-z_]+\.[a-z_]+$` catches syntax typos but not semantic ones — a manifest can declare `network_gatewat.fetch` and pass schema validation. Currently safe because the runtime denies unmapped tools, but as DeepSeek correctly notes, this couples correctness to a runtime check that future code changes could relax.

*Required fix:* Either (a) the manifest schema's `allowed_tools` and `forbidden_tools` items use an enum derived from `TOOL_CAPABILITY_MAP` keys, or (b) ManifestBinder rejects manifests at registration if any tool ID is not in the map. Option (a) fails earlier and is more visible; option (b) is slightly less coupled. Either is acceptable.

---

## (2) Valid Observations — Documentation / Notes Only

**DeepSeek #2 — Top-level resource policies required.** Substantively addressed in v1.11.1 §2.5, which lists `network_policy`, `sandbox_policy`, `memory_policy`, `audit_policy` in the `required` arrays for both manifest types. v1.11.2 said "all unchanged portions of v1.11.1 remain in force." DeepSeek's objection is fair as a documentation criticism — the v1.11.2 excerpts only show diffs and could mislead future readers — but the substantive requirement is met.

*Action:* v1.11.4 should explicitly restate the carried-forward `required` arrays so the schema is readable as a single document. Additionally, PolicyEngine should specify fail-closed behavior on missing policy fields (deny-all) as defensive coding, even though schema validation should catch this at registration.

**DeepSeek #4 — Retention policies for `scheduler_heartbeat` and soft-deleted `memory_items`.** Both Critic and Constraints agree this is not Phase 1 blocking. Constraints explicitly classified it as "acknowledged disk-growth issue, not RAM issue for Phase 1." DeepSeek themselves wrote "this is not a Phase 1 blocking issue for the first autonomous run, but it is a design gap for sustained operation."

*Action:* v1.11.4 should add an explicit Phase 2 deferral note. Suggested phrasing: "Retention policies for `scheduler_heartbeat` and `memory_items.soft_deleted` rows are deferred to Phase 2. MVP operates with append-only audit storage. Operator may manually prune via SQLite during downtime if required." Optionally, a future-state operator command (`/purge_old_audit_state`) can be added with its own manifest when retention is implemented.

**DeepSeek #6 — `/status` relies solely on Telegram whitelist.** DeepSeek doesn't propose a fix — they propose documenting this as a conscious tradeoff. The mechanism is correct: the operator must be able to recover the system even when the capability token system has failed. The Telegram whitelist concentration is the cost of that recoverability.

*Action:* v1.11.4 should explicitly document this tradeoff in the operator-control section. Add a panel-binding note: the Telegram operator whitelist may not be deactivated, made empty, or modified without full panel consent and a recorded session_event.

**Arbiter's HTTP redirect caveat.** Not a Critic objection — an Arbiter implementation note. Standard Python HTTP libraries follow redirects automatically; Kimi must configure `allow_redirects=False` and manually traverse the redirect chain to enforce the same_host_only rule.

*Action:* v1.11.4 should fold this into the redirect policy section (§6 of v1.11.3) so Kimi cannot miss it. One sentence: "NetworkGateway must disable automatic redirect following (`allow_redirects=False` for `requests`, equivalent for other clients) and traverse redirect chains manually to enforce the policy."

---

## Overruled Objections

**None overruled.** Per the Panel Charter, Critic objections are overruled only when both the Arbiter and Constraints Reviewer find them unsupported. Gemini's ruling addressed factual claims about libraries/APIs and did not rule on Critic objections. Qwen approved feasibility with carry-forward conditions and did not contradict Critic's findings — in fact, Qwen's binding condition #1 (no paging) reinforces Objection #3's RAM concern, and Qwen's Section 7 (Brave Search confirmation pending) is consistent with Critic's general theme that gateway-level details remain unspecified.

All six Critic objections cite specific proposal sections and identify concrete failure modes. None are bare assertions. The overrule threshold is not met.

---

## (3) Required Architect Revisions for v1.11.4

Schema-level (must resolve):
1. `tool_capability_map.py` SHA256 fingerprinting and boot-time integrity verification.
2. `network_policy.max_response_bytes` schema-level maximum (Architect picks ceiling, suggest 5–10 MB).
3. `allowed_tools` / `forbidden_tools` constrained to canonical tool IDs (schema enum or ManifestBinder validation).

Documentation / notes (fold in):
4. Restate v1.11.1 §2.5 `required` arrays explicitly so schema reads as single document; specify PolicyEngine fail-closed on missing policy fields.
5. Phase 2 deferral note for `scheduler_heartbeat` and `memory_items.soft_deleted` retention.
6. Document Telegram whitelist concentration tradeoff and bind whitelist modification to panel consent.
7. Fold Arbiter's `allow_redirects=False` implementation note into the redirect policy section.

Tests to add (alongside existing v1.11.3 list):
- `test_tool_capability_map_sha256_verified_at_boot.py`
- `test_tool_capability_map_modification_blocks_autonomous_operation.py`
- `test_manifest_rejects_max_response_bytes_above_ceiling.py`
- `test_manifest_rejects_unknown_tool_id_in_allowed_tools.py`
- `test_policy_engine_fails_closed_on_missing_network_policy.py`

---

## (4) Path Forward

**Return to Architect for v1.11.4.** Do not run another full panel cycle. The required changes are:
- Three schema additions (small, well-scoped)
- Four documentation/note additions
- One implementation note for Kimi

After the Architect produces v1.11.4, Evaluator delta-confirms only. No re-Critic, re-Arbiter, or re-Constraints cycle is needed because:
- DeepSeek already raised these issues; resolving them is not new attack surface
- Arbiter cleared all factual claims; no new factual claims introduced
- Constraints' RAM accounting unchanged; the new ceiling on `max_response_bytes` *strengthens* Qwen's binding conditions rather than altering the runtime budget

**One operational reminder for the Operator:** Gap 3 (qwen3:4b thinking-mode inference for Ollama `/api/show`) is not addressed in this Arbiter ruling. Gemini's response cleared the v1.11.3 factual claims but did not rule on the qwen3:4b thinking-mode pattern. That separate Arbiter task must complete before Kimi can implement `_infer_thinking_mode_from_arbiter_rule()` in v1.12. Confirm the parallel Gap 3 ruling has been requested and received from Gemini.

Once v1.11.4 is delta-confirmed and Gap 3 is ruled on, the proposal stack is ready for Kimi to produce `AXIOM_Implementation_v1.12`.

# Gap 3 Arbiter Ruling — Integration Analysis

Acknowledged. The Gap 3 ruling resolves the qwen3:4b thinking-mode question that was holding Task 3 of Kimi's implementation plan. It does not require a new panel cycle, but it does need to fold into v1.11.4 alongside the items from my prior synthesis. There are two substantive issues with the ruling itself and one hygiene concern.

---

## What the Ruling Establishes

**Factual content is sound.** Gemini's core finding — that Ollama exposes thinking mode as a first-class API parameter (`think: true|false`), not as a template/system convention — is consistent with current Ollama API behavior. This directly overrules v1.10.1 §9's guidance to inspect `template`, `system`, and `parameters` for thinking-mode determination. Per the Charter, Gemini's factual rulings are binding.

**Authoritative locations:**
- **Boot-time verification:** Inspect only the `parameters` field of `/api/show` for the literal `think false` directive. Template and system fields must be ignored *for this specific determination* (they remain part of the broader profile fingerprint via their SHA256 hashes — that's separate).
- **Runtime enforcement:** ModelGateway must explicitly append `"think": false` to every local Ollama request as defense-in-depth.

The boot-time verification regex pattern (`(?i)^\s*think\s+false\s*$` with MULTILINE) is correct.

---

## Issue 1 — Return-Value Schema Mismatch (must reconcile)

The ruling's example function returns `"disabled"` or `"unknown_or_enabled"`. v1.11.1 §1.2 schema constrains `model_profile_fingerprints.thinking_mode` to `IN ('disabled', 'enabled', 'unknown')`. These don't match.

This matters because v1.11.1 §3.4 step 9 specifies "Reject if `thinking_mode = unknown`." If Kimi implements Gemini's function literally, that check never triggers — `"unknown_or_enabled"` is not `"unknown"`, so the registration succeeds when it should fail.

Two reasonable resolutions:

**(a) Preserve the three-state schema, change the function.** Inference returns `"disabled"` (directive present) or `"unknown"` (directive absent). The state `"enabled"` becomes reserved for future rulings — any model where thinking is explicitly enabled would have its own positive directive, which a future Arbiter ruling could specify. v1.11.1 §3.4 step 9 logic stands as written.

**(b) Collapse to two states.** Schema becomes `IN ('disabled', 'not_disabled')`. Step 9 becomes "Reject if `thinking_mode != 'disabled'`." Slightly simpler but loses forward-compatibility.

I recommend (a). It preserves the existing schema, the existing fail-closed logic, and leaves room for future rulings to distinguish "enabled" from "unknown" if Ollama exposes that signal.

---

## Issue 2 — Runtime Enforcement Is a New Architectural Requirement

The ruling adds: *"ModelGateway must also explicitly append `\"think\": false` to all local Ollama API requests at runtime to absolutely guarantee the model does not attempt extended reasoning."*

This is not in any current proposal. It's a defense-in-depth layer that complements the boot-time fingerprint check. CV1 (security baked in) endorses it.

v1.11.4 needs to specify:
- ModelGateway injects `"think": false` into every local Ollama `/api/chat` and `/api/generate` request
- ModelGateway rejects any caller that attempts to override this with `"think": true`
- Test: `test_model_gateway_local_requests_force_think_false.py`
- Test: `test_model_gateway_rejects_caller_override_of_think_parameter.py`

This is small in scope but should be in the proposal record so Kimi doesn't miss it the way the Gap 3 ruling itself was missed.

---

## Issue 3 — Hygiene Concern with the Arbiter Response

The bottom of the ruling contains:

> `https://youtu.be/1W5-SM5DrjA?si=RbgzBUyx3pcIAP7U`
> *For further context on configuring these specific workflows, review the Qwen 3.5 Thinking Mode Tutorial.*

Three problems:

1. The Arbiter's role is binding factual rulings, not tutorial recommendations. External multimedia references are out of scope.
2. The video is described as "Qwen 3.5 Thinking Mode" but AXIOM uses qwen3:4b — different model. The reference may not even be relevant to the actual ruling.
3. A tracking-parameter URL appearing in a panel artifact is a content-injection footprint. I have not followed the link and you should not either. The factual content of the ruling stands on its own; the link is editorial residue.

**Recommendation:** When the operator strips this ruling for circulation to other panel members and to Kimi, omit the YouTube link and the trailing paragraph entirely. Keep §1, §2, and §3 (the actual ruling). Going forward, when you receive Arbiter rulings with non-factual editorial appendages, strip them before propagating — this is a small process hygiene improvement worth adopting.

---

## Updated Path Forward

The Architect's v1.11.4 must now incorporate:

**From my prior synthesis (DeepSeek-driven):**
1. `tool_capability_map.py` SHA256 fingerprinting and boot-time integrity verification
2. `network_policy.max_response_bytes` schema-level maximum (Architect picks ceiling, suggest 5–10 MB)
3. `allowed_tools` / `forbidden_tools` constrained to canonical tool IDs
4. Restate v1.11.1 §2.5 required arrays explicitly
5. PolicyEngine fail-closed on missing policy fields
6. Phase 2 deferral note for `scheduler_heartbeat` and soft-deleted `memory_items` retention
7. Document Telegram whitelist concentration tradeoff
8. HTTP redirect implementation note (`allow_redirects=False`)

**From the Gap 3 ruling:**
9. Replace the `_infer_thinking_mode` algorithm with Gemini's `parameters`-only regex pattern
10. Reconcile function return values with schema enum (recommend Option (a) above)
11. Add ModelGateway runtime enforcement requirement (`"think": false` injection on every local request)
12. Update v1.11.1 §3.4 step 8 ("Determine thinking_mode using the Arbiter-approved inference rule only") to reference this ruling explicitly with the regex pattern documented inline

**Tests to add for Gap 3 specifically:**
- `test_infer_thinking_mode_disabled_when_directive_present.py`
- `test_infer_thinking_mode_unknown_when_directive_absent.py`
- `test_infer_thinking_mode_ignores_template_and_system.py`
- `test_model_gateway_local_requests_force_think_false.py`
- `test_model_gateway_rejects_caller_override_of_think_parameter.py`

**Process:** Architect produces v1.11.4 → Evaluator delta-confirms → advance to Kimi for v1.12. No re-Critic, re-Arbiter, or re-Constraints cycle. The Gap 3 ruling is binding and additive; it does not introduce new attack surface (it removes one — the hardcoded heuristic) and does not change RAM or budget.