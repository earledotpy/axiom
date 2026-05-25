AXIOM Proposal v1.11.4 — Security Artifact Integrity, Network Limits, Tool ID Constraints, and Gap 3 Integration

Status

Proposal version: v1.11.4
Type: Targeted approval patch
Scope: DeepSeek-driven schema/security fixes, documentation carry-forwards, and Gemini Gap 3 ruling integration
Architecture spine changed: No
Implementation plan changed: Not yet — this proposal is for Kimi to consume in v1.12 after delta-confirmation

This revision incorporates the panel synthesis requiring three schema-level fixes, four documentation/implementation notes, and the separate Arbiter ruling on Ollama thinking-mode verification.  


---

1. Tool-Capability Map Becomes a Registered Security Artifact

1.1 Problem

tool_capability_map.py defines the authorization interpretation layer. v1.11.3 fingerprinted manifests but not the file that interprets their tool permissions. That leaves a clean privilege-escalation path: modify the map and the same manifest now authorizes different behavior.

1.2 Decision

Replace the Python-defined canonical map with a registered JSON security artifact:

axiom/policy/security_artifacts/tool_capability_map.json

The Python module:

axiom/core/tool_capability_map.py

must only load, validate, and expose the registered JSON artifact. It must not contain the authoritative map inline.

1.3 Fingerprint Table Revision

Extend manifest_fingerprints.manifest_type:

manifest_type TEXT NOT NULL
    CHECK (manifest_type IN (
        'role',
        'operator_control',
        'tool_capability_map'
    )),

Revise the table-level type check:

CHECK (
    (manifest_type = 'role'
        AND role_name IS NOT NULL
        AND command_name IS NULL)
    OR
    (manifest_type = 'operator_control'
        AND command_name IS NOT NULL
        AND role_name IS NULL)
    OR
    (manifest_type = 'tool_capability_map'
        AND role_name IS NULL
        AND command_name IS NULL)
)

Canonical row:

manifest_id = "security.tool_capability_map.v1"
manifest_type = "tool_capability_map"
relative_path = "policy/security_artifacts/tool_capability_map.json"

1.4 Boot-Time Verification

ManifestIntegrityVerifier.verify_all() must verify:

role manifests
operator-control manifests
tool_capability_map.json

Failure behavior is identical to manifest mismatch:

autonomous_operation_enabled = false
scheduler_status = "safe_disabled"
security_events.event_type = "manifest_integrity_mismatch"
Telegram alert emitted once

1.5 Canonical Tool-Capability Map JSON

{
  "schema_version": "axiom.tool_capability_map.v1",
  "artifact_type": "tool_capability_map",
  "artifact_id": "security.tool_capability_map.v1",
  "artifact_version": "1.0.0",
  "approved_by_panel_version": "v1.11.4",
  "tools": {
    "model_gateway.call": {
      "source": "allowed_capabilities.model.allow_model_calls",
      "additional_checks": [
        "provider_group_allowed",
        "budget_policy_not_exceeded"
      ]
    },
    "memory_gateway.query": {
      "source": "memory_policy.read",
      "additional_checks": [
        "memory_policy.max_query_results"
      ]
    },
    "memory_gateway.write": {
      "source": "memory_policy.write",
      "additional_checks": [
        "memory_policy.write_requires_dedupe"
      ]
    },
    "network_gateway.fetch": {
      "source": "network_policy",
      "additional_checks": [
        "mode_allowlist_only",
        "request_matches_allowlist",
        "request_does_not_match_denylist",
        "redirect_policy",
        "timeout_seconds",
        "max_response_bytes"
      ]
    },
    "sandbox_gateway.execute": {
      "source": "sandbox_policy.allowed",
      "additional_checks": [
        "sandbox_policy.max_ram_mb",
        "sandbox_policy.max_wall_clock_seconds",
        "sandbox_policy.network_access_denied"
      ]
    },
    "filesystem.read": {
      "source": "allowed_capabilities.filesystem.read",
      "additional_checks": [
        "path_under_allowed_roots"
      ]
    },
    "filesystem.write": {
      "source": "allowed_capabilities.filesystem.write",
      "additional_checks": [
        "path_under_allowed_roots"
      ]
    },
    "session_controller.status": {
      "source": "allowed_capabilities.operator_control.allowed_commands",
      "required_command": "status",
      "requires_manifest_type": "operator_control"
    },
    "session_controller.cancel_current_chain": {
      "source": "allowed_capabilities.operator_control.allowed_commands",
      "required_command": "cancel_current_chain",
      "requires_manifest_type": "operator_control"
    },
    "session_controller.pause_after_current": {
      "source": "allowed_capabilities.operator_control.allowed_commands",
      "required_command": "pause_after_current",
      "requires_manifest_type": "operator_control"
    },
    "session_controller.resume": {
      "source": "allowed_capabilities.operator_control.allowed_commands",
      "required_command": "resume",
      "requires_manifest_type": "operator_control"
    },
    "session_controller.shutdown_after_current": {
      "source": "allowed_capabilities.operator_control.allowed_commands",
      "required_command": "shutdown_after_current",
      "requires_manifest_type": "operator_control"
    },
    "session_controller.run_classifier_validation": {
      "source": "allowed_capabilities.operator_control.allowed_commands",
      "required_command": "run_classifier_validation",
      "requires_manifest_type": "operator_control"
    },
    "session_controller.enable_autonomous": {
      "source": "allowed_capabilities.operator_control.allowed_commands",
      "required_command": "enable_autonomous",
      "requires_manifest_type": "operator_control"
    },
    "session_controller.reconcile_provider_usage": {
      "source": "allowed_capabilities.operator_control.allowed_commands",
      "required_command": "reconcile_provider_usage",
      "requires_manifest_type": "operator_control"
    }
  }
}


---

2. Canonical Tool ID Constraint

2.1 Decision

Manifest JSON Schema must reject unknown tool IDs at schema validation time.

Replace the previous pattern-only tool_id definition with:

{
  "tool_id": {
    "type": "string",
    "enum": [
      "model_gateway.call",
      "memory_gateway.query",
      "memory_gateway.write",
      "network_gateway.fetch",
      "sandbox_gateway.execute",
      "filesystem.read",
      "filesystem.write",
      "session_controller.status",
      "session_controller.cancel_current_chain",
      "session_controller.pause_after_current",
      "session_controller.resume",
      "session_controller.shutdown_after_current",
      "session_controller.run_classifier_validation",
      "session_controller.enable_autonomous",
      "session_controller.reconcile_provider_usage"
    ]
  }
}

allowed_tools and forbidden_tools both use:

{
  "items": {
    "$ref": "#/$defs/tool_id"
  },
  "uniqueItems": true
}

2.2 ManifestBinder Defense-in-Depth

Even though schema validation rejects unknown IDs, ManifestBinder must also reject any manifest where:

tool_id ∉ loaded tool_capability_map.tools.keys()

This prevents schema/map drift.

Failure blocks registration.


---

3. Network Response Size Ceiling

3.1 Decision

Set schema-level maximum:

network_policy.max_response_bytes <= 5,242,880

That is 5 MiB.

Rationale: AXIOM’s Phase 1 network gateway is for controlled fetches such as search API responses, not bulk document ingestion. A 5 MiB cap is generous for structured search results while preventing RAM exhaustion on the 2.0–2.3 GB runtime headroom machine.

3.2 Schema Patch

{
  "max_response_bytes": {
    "type": "integer",
    "minimum": 0,
    "maximum": 5242880
  }
}

Carry forward the v1.11.2 conditional rule:

deny_all:
    max_response_bytes = 0

allowlist_only:
    1 <= max_response_bytes <= 5242880

Anything above 5 MiB requires panel approval and a revised manifest schema.


---

4. Full Required Manifest Field Sets Restated

To avoid ambiguity from diff-only revisions, the canonical manifest required arrays are restated here.

4.1 Role Manifest Required Fields

{
  "required": [
    "schema_version",
    "manifest_type",
    "manifest_id",
    "manifest_version",
    "approved_by_panel_version",
    "description",
    "role",
    "budget_policy",
    "allowed_capabilities",
    "allowed_tools",
    "forbidden_tools",
    "network_policy",
    "sandbox_policy",
    "memory_policy",
    "audit_policy"
  ]
}

Role manifests must not include:

operator_command
authorization_policy

Role manifests must have:

"allowed_capabilities": {
  "operator_control": {
    "allowed_commands": []
  }
}

4.2 Operator-Control Manifest Required Fields

{
  "required": [
    "schema_version",
    "manifest_type",
    "manifest_id",
    "manifest_version",
    "approved_by_panel_version",
    "description",
    "operator_command",
    "authorization_policy",
    "budget_policy",
    "allowed_capabilities",
    "allowed_tools",
    "forbidden_tools",
    "network_policy",
    "sandbox_policy",
    "memory_policy",
    "audit_policy"
  ]
}

Operator-control manifests must not include:

role

Operator-control manifests must satisfy:

allowed_capabilities.operator_control.allowed_commands
==
[operator_command.command_name]

ManifestBinder enforces that equality before registration.


---

5. PolicyEngine Fail-Closed Rule

Even though schema validation should catch missing fields, PolicyEngine must fail closed if any required policy object is absent at runtime.

Required behavior:

def require_policy(manifest: dict, policy_name: str) -> dict:
    policy = manifest.get(policy_name)
    if not isinstance(policy, dict):
        raise PolicyDeniedError(
            f"Missing or invalid required policy object: {policy_name}"
        )
    return policy

Mandatory fail-closed policy fields:

budget_policy
allowed_capabilities
network_policy
sandbox_policy
memory_policy
audit_policy

For operator-control manifests, also mandatory:

operator_command
authorization_policy

For role manifests, also mandatory:

role

Missing policy fields do not degrade to defaults. They deny execution and log a policy-denial security event.


---

6. Retention Policy Deferral

6.1 Decision

Retention for these append-heavy records is deferred to Phase 2:

scheduler_heartbeat
memory_items where embedding_status = "soft_deleted"

6.2 Phase 1 Rule

Phase 1 operates with append-only audit storage.

No autonomous retention job exists in MVP.

6.3 Manual Maintenance Rule

If disk pressure occurs before Phase 2 retention design:

1. Stop AXIOM.
2. Back up the full SQLite database.
3. Perform manual SQLite maintenance during downtime.
4. On next boot, write a session_event documenting maintenance.

No agent may autonomously prune audit or memory rows in Phase 1.


---

7. Telegram Whitelist Concentration Tradeoff

7.1 Decision

/status and a minimal recovery command set intentionally rely on the Telegram operator whitelist even when capability-token systems or safe-pass are disabled.

This is a conscious recoverability tradeoff, not an oversight.

7.2 Binding Rule

The Telegram operator whitelist:

may not be deactivated
may not be made empty
may not be modified silently

Any whitelist modification requires:

1. Full panel consent.
2. Explicit operator action.
3. session_event recording:
   - previous whitelist hash
   - new whitelist hash
   - timestamp
   - reason

7.3 Minimal Recovery Commands

Commands allowed when autonomous operation is disabled or safe-pass is disabled must remain minimal:

/status
/shutdown_after_current

Other recovery commands require their own operator-control manifests and panel approval.


---

8. Redirect Enforcement Implementation Note

8.1 Decision

NetworkGateway must not rely on HTTP client automatic redirect handling.

Kimi must configure:

allow_redirects=False

for requests, or the equivalent setting for any other HTTP client.

8.2 Manual Redirect Traversal

NetworkGateway must manually evaluate every redirect hop:

1. Original request must match allowlist.
2. Original request must not match denylist.
3. If response is redirect:
   a. If redirect_policy = "deny", reject.
   b. If redirect_policy = "same_host_only":
        redirected URL scheme must be https
        redirected URL host must exactly equal original request host
        redirected URL port must equal original request port
        redirected URL path must still match original allowlist path_prefix
        redirected request must not match denylist
4. Repeat for each redirect hop up to a hard maximum of 3 hops.
5. Any ambiguity denies the request.

Redirect hop cap:

max_redirect_hops = 3


---

9. Gap 3 Integration — Ollama Thinking-Mode Verification

9.1 Arbiter Ruling Incorporated

Gemini ruled that Kimi’s previous /no_think template heuristic is obsolete. The authoritative boot-time signal is the Ollama /api/show response’s parameters field, specifically a Modelfile directive matching think false. Template and system fields are non-authoritative for thinking-mode verification. 

9.2 Canonical Inference Function

Use the existing three-state schema:

disabled
enabled
unknown

But this ruling only authorizes returning:

disabled
unknown

enabled remains reserved for a future Arbiter ruling that identifies an explicit positive signal.

import re

THINK_FALSE_PATTERN = re.compile(
    r"(?i)^\s*think\s+false\s*$",
    re.MULTILINE,
)

def infer_thinking_mode_from_arbiter_rule(show_json: dict) -> str:
    """
    Authoritative for qwen3:4b via Ollama /api/show.

    Returns:
        "disabled" if parameters contains a native `think false` directive.
        "unknown" otherwise.

    Non-authoritative for this determination:
        template
        system
    """
    params = str(show_json.get("parameters", ""))

    if THINK_FALSE_PATTERN.search(params):
        return "disabled"

    return "unknown"

9.3 Registration Rule

register_model_fingerprint.py must reject unless:

thinking_mode == "disabled"

This replaces the weaker earlier phrasing “reject if unknown.”

Canonical rule:

thinking_mode = infer_thinking_mode_from_arbiter_rule(show_json)

if thinking_mode != "disabled":
    raise FingerprintRegistrationError(
        "Cannot register model fingerprint: Ollama profile does not prove think=false"
    )

9.4 Fields Still Hashed

Although template and system are ignored for thinking-mode determination, they remain part of the broader profile fingerprint:

template_sha256
system_sha256
parameters_sha256
details_sha256

This preserves profile integrity while avoiding obsolete thinking-mode inference.


---

10. Runtime Enforcement — Force think: false

10.1 Decision

ModelGateway must inject:

"think": false

into every local Ollama request made through:

/api/chat
/api/generate

10.2 Caller Override Rule

If a caller supplies:

"think": true

ModelGateway must reject the request.

If a caller supplies:

"think": false

ModelGateway may accept it but must still overwrite it with the canonical value.

If a caller omits think, ModelGateway inserts it.

10.3 Canonical Enforcement Snippet

def prepare_local_ollama_payload(payload: dict) -> dict:
    if payload.get("think") is True:
        raise PolicyDeniedError(
            "Caller may not override local Ollama thinking mode"
        )

    prepared = dict(payload)
    prepared["think"] = False
    return prepared

This is defense-in-depth: boot-time verification confirms the model profile, and runtime enforcement confirms every local call.


---

11. Schema Version

Initial schema version is now:

v1.11.4

Migration ledger row:

INSERT OR IGNORE INTO schema_migrations (schema_version, notes)
VALUES (
    'v1.11.4',
    'Initial AXIOM MVP canonical schema with manifest schemas, tool-capability security artifact, network response ceiling, and Ollama think=false verification.'
);


---

12. Added Tests for v1.11.4

Kimi v1.12 must add these tests.

12.1 Tool-Capability Map Integrity

test_tool_capability_map_sha256_verified_at_boot.py
test_tool_capability_map_modification_blocks_autonomous_operation.py
test_tool_capability_map_registered_as_security_artifact.py

12.2 Tool ID Constraints

test_manifest_rejects_unknown_tool_id_in_allowed_tools.py
test_manifest_rejects_unknown_tool_id_in_forbidden_tools.py
test_manifest_binder_rejects_tool_id_not_in_loaded_map.py

12.3 Network Limits

test_manifest_rejects_max_response_bytes_above_ceiling.py
test_network_timeout_zero_only_valid_for_deny_all.py
test_network_gateway_disables_automatic_redirects.py
test_redirect_chain_limited_to_three_hops.py

12.4 Policy Fail-Closed

test_policy_engine_fails_closed_on_missing_network_policy.py
test_policy_engine_fails_closed_on_missing_sandbox_policy.py
test_policy_engine_fails_closed_on_missing_memory_policy.py
test_policy_engine_logs_missing_policy_denial.py

12.5 Telegram Whitelist Governance

test_telegram_whitelist_cannot_be_empty.py
test_telegram_whitelist_change_records_session_event.py

12.6 Thinking-Mode Verification

test_infer_thinking_mode_disabled_when_directive_present.py
test_infer_thinking_mode_unknown_when_directive_absent.py
test_infer_thinking_mode_ignores_template_and_system.py
test_register_model_fingerprint_rejects_non_disabled_thinking_mode.py
test_model_gateway_local_requests_force_think_false.py
test_model_gateway_rejects_caller_override_of_think_parameter.py

Carry forward all v1.11.3 tests unchanged.


---

13. Final v1.11.4 Position

v1.11.4 resolves the required synthesis items:

Required item	v1.11.4 resolution

tool_capability_map.py not integrity-verified	Replaced authoritative Python map with registered JSON security artifact; verified at boot.
max_response_bytes unbounded	Added 5 MiB schema ceiling.
Unknown tool IDs pass schema	Replaced pattern-only tool IDs with canonical enum and ManifestBinder map validation.
Required manifest fields unclear across revisions	Restated role and operator-control required arrays.
Missing policy field behavior	PolicyEngine fails closed and logs denial.
Heartbeat / soft-delete retention	Deferred to Phase 2; Phase 1 append-only.
Telegram whitelist tradeoff	Documented as conscious recovery boundary; whitelist modification requires panel consent and session event.
Redirect implementation caveat	Requires allow_redirects=False and manual redirect traversal.
Gap 3 thinking-mode inference	Integrated Arbiter ruling: inspect parameters only for think false.
Runtime thinking-mode enforcement	ModelGateway injects "think": false and rejects caller override.


Chief Architect recommendation

Attach v1.11.4 as the final targeted patch to v1.11.3.

Proceed to:

Evaluator delta-confirmation
↓
Return to Kimi for AXIOM_Implementation_v1.12

No re-Critic, re-Arbiter, or re-Constraints cycle is required unless the Evaluator identifies a new issue introduced by this patch.