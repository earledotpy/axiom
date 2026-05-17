# Evaluation of AXIOM_Proposal_v1.11.4 (Chief Architect)

## Verdict

**Approve with one targeted addition before Kimi.** The proposal cleanly resolves all twelve required items from my prior synthesis. The schema-level work is structurally sound and the Gap 3 integration is correct. One specification gap was introduced by this revision and should be filled in v1.11.4 in place rather than producing v1.11.5. After that single addition, advance directly to Kimi.

---

## What Holds

All twelve required items are resolved. Highlights of the strongest moves:

**Tool-capability map as a registered security artifact (§1).** The Architect chose the cleaner of the two options I offered — generating from a fingerprinted JSON file rather than hashing the .py file. The Python module becomes a loader and validator over a registered JSON artifact. Adding `tool_capability_map` as a third `manifest_type` reuses the existing `manifest_fingerprints` table and `ManifestIntegrityVerifier.verify_all()` boot path. This is the architecturally correct location — security artifacts get the same lifecycle as manifests. CV1 is upheld at the right leverage point.

**Tool ID enum constraint with defense-in-depth (§2).** Schema-level enum from the canonical tool list, plus ManifestBinder validation against the loaded map. Either layer alone would prevent typo-based drift; both layers together prevent schema/map drift in either direction.

**5 MiB `max_response_bytes` ceiling (§3).** Appropriately conservative for Phase 1's intended use (search API responses), generous enough not to constrain legitimate use, well below the 2.0–2.3 GB headroom even under adversarial single-task allocation. The conditional rules from v1.11.2 carry forward correctly.

**PolicyEngine fail-closed (§5).** The `require_policy()` helper specifies the deny-execution-and-log behavior cleanly. Making missing fields a `PolicyDeniedError` rather than a `KeyError` means the failure mode is observable and audited rather than crash-or-silently-default.

**Telegram whitelist binding (§7).** The recovery command set is explicitly limited to `/status` and `/shutdown_after_current`. Other recovery commands require their own operator-control manifests and panel approval. Whitelist modification requires session_event logging with previous and new hashes — the audit chain captures the only authentication boundary that protects recovery commands.

**Redirect implementation (§8).** Better than my ask. The Architect added a 3-hop maximum on top of the `allow_redirects=False` and manual traversal requirements I requested. Redirect chains beyond 3 hops are unusual for legitimate APIs and a common signature of redirect-loop attacks or open-redirector abuse. CV6 is strengthened.

**Gap 3 integration (§9, §10).** The thinking-mode inference function correctly preserves the three-state schema. The "reject unless disabled" phrasing in §9.3 is forward-compatible — the older "reject if unknown" phrasing would have permitted a future "enabled" state to register, which is the wrong invariant. The runtime enforcement at §10 with caller-override rejection is the correct defense-in-depth complement to boot-time verification. The `prepare_local_ollama_payload` snippet correctly distinguishes between rejecting `"think": true` (caller intent to override) and tolerating `"think": false` (caller redundancy).

**Test coverage (§12).** All ten tests I requested are present, plus twelve additional tests the Architect added that I would have flagged for Kimi anyway. The test list is comprehensive.

---

## What Fails

### One item must be added before Kimi consumes this proposal

**The tool-capability map JSON has no specified JSON Schema.** §1.5 declares `"schema_version": "axiom.tool_capability_map.v1"` and §1.2 specifies that `tool_capability_map.py` must "load, validate, and expose the registered JSON artifact" — but no schema for that artifact is defined. The map entries in §1.5 are structurally heterogeneous: some have `required_command`, some have `requires_manifest_type`, some have `additional_checks`, and the value types of these fields vary across entries.

Without a JSON Schema specification:
- ManifestBinder has to validate the map structurally via implicit Python knowledge, which is exactly the kind of implicit security knowledge the proposal stack has been steadily eliminating.
- Two `tool_capability_map.json` files with different entry shapes could both pass SHA256 integrity verification (because integrity only checks bytes match a registered hash) but mean different things to ManifestBinder.
- A future panel-approved tool addition that is structurally malformed in some subtle way would not be caught at registration time — it would surface as a runtime PolicyEngine bug.

This is the same reasoning that drove v1.11.1's explicit JSON Schema for manifests. The tool-capability map is now a peer security artifact and should receive the same treatment.

**Required addition for v1.11.4:** A JSON Schema definition for `axiom.tool_capability_map.v1`. The schema needs to express:
- Top-level required fields (`schema_version`, `artifact_type`, `artifact_id`, `artifact_version`, `approved_by_panel_version`, `tools`)
- The `tools` object with `additionalProperties: false` and entries keyed by canonical tool IDs
- For each tool entry, a structural definition with required `source`, optional `additional_checks` (array of strings), optional `required_command` (string), optional `requires_manifest_type` (enum constrained to `"operator_control"`)
- Cross-field constraint: tools whose `source` references `allowed_capabilities.operator_control.allowed_commands` must have `required_command` and `requires_manifest_type: "operator_control"`

The Architect can fold this into v1.11.4 §1 as a new sub-section §1.6 without producing v1.11.5. The change is additive specification.

Add one test:
- `test_tool_capability_map_json_schema_validates_canonical_artifact.py`

### One smaller item to flag — registration workflow ambiguity

**Who writes the tool-capability map JSON to `manifest_fingerprints`?** §1.4 specifies that `ManifestIntegrityVerifier.verify_all()` checks the artifact at boot, but the registration path is not specified. The existing `tools/register_manifests.py` CLI per v1.10.1 §4 was scoped to `/policy/role_manifests/` and `/policy/operator_control_manifests/`. The new artifact lives in `/policy/security_artifacts/`.

Two acceptable resolutions:
- Extend `tools/register_manifests.py` to also scan `/policy/security_artifacts/`
- Add `tools/register_security_artifacts.py` as a parallel CLI

Either is fine architecturally. This is small enough that Kimi can address it in v1.12 with the panel's awareness — flag it as an item Kimi should explicitly resolve in their plan rather than invent silently. If the Architect wants to specify in v1.11.4, even better, but it is not strictly required.

---

## Conflicts with Core Values

**CV1 (security baked in):** Strongly upheld. The tool-capability map now lives at the same security tier as manifests. Defense-in-depth at the schema enum + ManifestBinder layer. Runtime enforcement of `"think": false` complements boot-time verification.

**CV3 (zero-trust at every agent boundary):** Upheld. Schema-level rejection of unknown tool IDs eliminates a configuration drift surface. Policy fail-closed on missing fields removes the ambiguous-permission failure mode.

**CV6 (sandbox and network never directly connected):** Upheld and strengthened. 5 MiB response ceiling, manual redirect traversal, 3-hop cap, `allow_redirects=False`.

**CV2, CV4, CV5:** No conflicts identified.

---

## What Must Be Resolved

**Before sending to Kimi:**

1. Add JSON Schema for `axiom.tool_capability_map.v1` security artifact (fold into v1.11.4 §1 in place as §1.6).
2. Add `test_tool_capability_map_json_schema_validates_canonical_artifact.py` to §12.1 test list.

**Should clarify in same revision (small):**

3. Specify the registration workflow for the new security artifact — either extend `register_manifests.py` or add a parallel CLI.

---

## Recommended Next Step

Return v1.11.4 to the Architect with item #1 as a required addition and item #3 as a same-revision clarification. The required addition is small — an additive `$defs` section in JSON Schema form, analogous to the manifest schema work the Architect already produced. No new version number needed; the Architect can publish the patched v1.11.4 in place.

Once the patched v1.11.4 is in hand, no further panel cycle is needed. Advance directly to Kimi for `AXIOM_Implementation_v1.12` per the prompt I provided in the prior turn. Update that prompt to reference the now-final v1.11.4 (with the schema addition) and include the patched proposal in Kimi's file uploads.