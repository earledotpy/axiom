AXIOM Proposal v1.11.4 — Patched Final Addendum

Status

Proposal version: v1.11.4, patched in place
Type: Final targeted addition before Kimi
Scope: Tool-capability map JSON Schema, registration workflow, test addition
Architecture spine changed: No
New panel cycle required: No, unless Evaluator identifies a new issue

The Evaluator approved v1.11.4 with one required addition: the newly registered tool_capability_map.json security artifact must itself have a canonical JSON Schema before Kimi consumes the proposal. The Evaluator also requested clarification on how this artifact is registered into manifest_fingerprints. 


---

1. Addition to §1 — Tool-Capability Map JSON Schema

1.6 Canonical JSON Schema for axiom.tool_capability_map.v1

The tool-capability map is now a first-class security artifact. Therefore it requires the same treatment as role and operator-control manifests:

schema validation
↓
SHA256 registration
↓
boot-time integrity verification
↓
fail-closed on mismatch

Integrity alone is insufficient. A malformed map can be faithfully hashed and still create an authorization bug. The schema below defines the only valid structure for tool_capability_map.json.

{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "axiom.tool_capability_map.schema.v1",
  "title": "AXIOM Tool Capability Map Schema v1",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schema_version",
    "artifact_type",
    "artifact_id",
    "artifact_version",
    "approved_by_panel_version",
    "tools"
  ],
  "properties": {
    "schema_version": {
      "type": "string",
      "const": "axiom.tool_capability_map.v1"
    },
    "artifact_type": {
      "type": "string",
      "const": "tool_capability_map"
    },
    "artifact_id": {
      "type": "string",
      "const": "security.tool_capability_map.v1"
    },
    "artifact_version": {
      "type": "string",
      "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+$"
    },
    "approved_by_panel_version": {
      "type": "string",
      "minLength": 1
    },
    "tools": {
      "type": "object",
      "additionalProperties": false,
      "required": [
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
      ],
      "properties": {
        "model_gateway.call": {
          "$ref": "#/$defs/standard_tool_entry"
        },
        "memory_gateway.query": {
          "$ref": "#/$defs/standard_tool_entry"
        },
        "memory_gateway.write": {
          "$ref": "#/$defs/standard_tool_entry"
        },
        "network_gateway.fetch": {
          "$ref": "#/$defs/standard_tool_entry"
        },
        "sandbox_gateway.execute": {
          "$ref": "#/$defs/standard_tool_entry"
        },
        "filesystem.read": {
          "$ref": "#/$defs/standard_tool_entry"
        },
        "filesystem.write": {
          "$ref": "#/$defs/standard_tool_entry"
        },
        "session_controller.status": {
          "$ref": "#/$defs/operator_control_tool_entry"
        },
        "session_controller.cancel_current_chain": {
          "$ref": "#/$defs/operator_control_tool_entry"
        },
        "session_controller.pause_after_current": {
          "$ref": "#/$defs/operator_control_tool_entry"
        },
        "session_controller.resume": {
          "$ref": "#/$defs/operator_control_tool_entry"
        },
        "session_controller.shutdown_after_current": {
          "$ref": "#/$defs/operator_control_tool_entry"
        },
        "session_controller.run_classifier_validation": {
          "$ref": "#/$defs/operator_control_tool_entry"
        },
        "session_controller.enable_autonomous": {
          "$ref": "#/$defs/operator_control_tool_entry"
        },
        "session_controller.reconcile_provider_usage": {
          "$ref": "#/$defs/operator_control_tool_entry"
        }
      }
    }
  },
  "$defs": {
    "source_path": {
      "type": "string",
      "enum": [
        "allowed_capabilities.model.allow_model_calls",
        "allowed_capabilities.filesystem.read",
        "allowed_capabilities.filesystem.write",
        "allowed_capabilities.operator_control.allowed_commands",
        "memory_policy.read",
        "memory_policy.write",
        "network_policy",
        "sandbox_policy.allowed"
      ]
    },
    "additional_check": {
      "type": "string",
      "enum": [
        "provider_group_allowed",
        "budget_policy_not_exceeded",
        "memory_policy.max_query_results",
        "memory_policy.write_requires_dedupe",
        "mode_allowlist_only",
        "request_matches_allowlist",
        "request_does_not_match_denylist",
        "redirect_policy",
        "timeout_seconds",
        "max_response_bytes",
        "sandbox_policy.max_ram_mb",
        "sandbox_policy.max_wall_clock_seconds",
        "sandbox_policy.network_access_denied",
        "path_under_allowed_roots"
      ]
    },
    "standard_tool_entry": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "source",
        "additional_checks"
      ],
      "properties": {
        "source": {
          "$ref": "#/$defs/source_path"
        },
        "additional_checks": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/additional_check"
          },
          "uniqueItems": true
        }
      },
      "not": {
        "anyOf": [
          {
            "required": [
              "required_command"
            ]
          },
          {
            "required": [
              "requires_manifest_type"
            ]
          }
        ]
      }
    },
    "operator_control_tool_entry": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "source",
        "required_command",
        "requires_manifest_type"
      ],
      "properties": {
        "source": {
          "type": "string",
          "const": "allowed_capabilities.operator_control.allowed_commands"
        },
        "required_command": {
          "type": "string",
          "enum": [
            "status",
            "cancel_current_chain",
            "pause_after_current",
            "resume",
            "shutdown_after_current",
            "run_classifier_validation",
            "enable_autonomous",
            "reconcile_provider_usage"
          ]
        },
        "requires_manifest_type": {
          "type": "string",
          "const": "operator_control"
        },
        "additional_checks": {
          "type": "array",
          "maxItems": 0
        }
      }
    }
  }
}


---

2. Cross-Field Validation Beyond JSON Schema

The JSON Schema validates structure, but Kimi must also implement semantic validation for operator-control tool entries.

2.1 Required command must match tool suffix

ManifestBinder must reject a map where the required_command does not match the tool ID suffix.

Canonical validation:

SESSION_CONTROLLER_TOOL_COMMANDS = {
    "session_controller.status": "status",
    "session_controller.cancel_current_chain": "cancel_current_chain",
    "session_controller.pause_after_current": "pause_after_current",
    "session_controller.resume": "resume",
    "session_controller.shutdown_after_current": "shutdown_after_current",
    "session_controller.run_classifier_validation": "run_classifier_validation",
    "session_controller.enable_autonomous": "enable_autonomous",
    "session_controller.reconcile_provider_usage": "reconcile_provider_usage",
}

def validate_tool_capability_map_semantics(tool_map: dict) -> None:
    tools = tool_map["tools"]

    for tool_id, expected_command in SESSION_CONTROLLER_TOOL_COMMANDS.items():
        entry = tools[tool_id]

        if entry["source"] != "allowed_capabilities.operator_control.allowed_commands":
            raise ManifestValidationError(
                f"{tool_id} must use operator_control allowed_commands source"
            )

        if entry["required_command"] != expected_command:
            raise ManifestValidationError(
                f"{tool_id} required_command must be {expected_command}"
            )

        if entry["requires_manifest_type"] != "operator_control":
            raise ManifestValidationError(
                f"{tool_id} must require operator_control manifest type"
            )

This prevents a structurally valid but semantically wrong map such as:

"session_controller.shutdown_after_current": {
  "source": "allowed_capabilities.operator_control.allowed_commands",
  "required_command": "status",
  "requires_manifest_type": "operator_control"
}


---

3. Registration Workflow Clarification

3.1 Decision

Extend the existing CLI:

tools/register_manifests.py

Do not add a separate register_security_artifacts.py.

Reason: role manifests, operator-control manifests, and the tool-capability map are now one security-artifact registration set. Splitting registration across two CLIs increases the chance of partial registration.

3.2 Canonical scan paths

tools/register_manifests.py must scan:

axiom/policy/role_manifests/*.json
axiom/policy/operator_control_manifests/*.json
axiom/policy/security_artifacts/tool_capability_map.json

3.3 Validation sequence

For each file:

1. Load JSON.
2. Select schema by artifact type:
   - manifest_type = role
   - manifest_type = operator_control
   - artifact_type = tool_capability_map
3. Validate against its JSON Schema.
4. Run semantic validation:
   - operator-control command binding
   - role allowed_commands empty
   - tool-capability map command/tool consistency
   - all manifest tool IDs exist in loaded tool-capability map
5. Compute SHA256 of canonical file bytes.
6. Insert or replace row in manifest_fingerprints.

3.4 Registration must be atomic

The registration CLI must operate in one database transaction.

If any artifact fails validation:

no manifest_fingerprints rows are changed

This prevents a half-updated security boundary.

3.5 Canonical registration order

1. Validate tool_capability_map.json first.
2. Load canonical tool ID set from the validated tool-capability map.
3. Validate role manifests against tool ID set.
4. Validate operator-control manifests against tool ID set.
5. Write all fingerprints in one transaction.


---

4. Revised manifest_fingerprints Registration Rows

The registration CLI writes rows with these canonical values.

4.1 Tool-capability map row

manifest_id = "security.tool_capability_map.v1"
manifest_type = "tool_capability_map"
relative_path = "policy/security_artifacts/tool_capability_map.json"
schema_version = "axiom.tool_capability_map.v1"
manifest_version = "1.0.0"
role_name = NULL
command_name = NULL
approved_by_panel_version = "v1.11.4"
active = 1

4.2 Role manifest rows

manifest_id = manifest["manifest_id"]
manifest_type = "role"
relative_path = "policy/role_manifests/<filename>.json"
schema_version = "axiom.manifest.v1"
manifest_version = manifest["manifest_version"]
role_name = manifest["role"]["role_name"]
command_name = NULL
approved_by_panel_version = manifest["approved_by_panel_version"]
active = 1

4.3 Operator-control manifest rows

manifest_id = manifest["manifest_id"]
manifest_type = "operator_control"
relative_path = "policy/operator_control_manifests/<filename>.json"
schema_version = "axiom.manifest.v1"
manifest_version = manifest["manifest_version"]
role_name = NULL
command_name = manifest["operator_command"]["command_name"]
approved_by_panel_version = manifest["approved_by_panel_version"]
active = 1


---

5. Boot-Time Verification Clarification

ManifestIntegrityVerifier.verify_all() must verify the complete registered set:

all active role manifests
all active operator-control manifests
active tool-capability map security artifact

Verification failure cases:

registered file missing
unregistered file present
SHA256 mismatch
schema validation failure
semantic validation failure
tool-capability map missing

Any failure produces:

autonomous_operation_enabled = false
scheduler_status = "safe_disabled"
security_events.event_type = "manifest_integrity_mismatch"
Telegram alert emitted once


---

6. Added Test

Add the Evaluator-requested test to §12.1:

test_tool_capability_map_json_schema_validates_canonical_artifact.py

Also add these registration workflow tests:

test_register_manifests_includes_tool_capability_map.py
test_register_manifests_rolls_back_on_invalid_security_artifact.py
test_tool_capability_map_required_command_matches_tool_suffix.py

These are additive to all v1.11.4 tests already listed.


---

7. Final Patched v1.11.4 Position

This patch resolves the final pre-Kimi addition:

Evaluator item	Resolution

Tool-capability map JSON has no schema	Added canonical axiom.tool_capability_map.v1 JSON Schema.
Map entries structurally heterogeneous	Schema defines standard and operator-control entry shapes.
Operator-control entries need cross-field constraint	Added ManifestBinder semantic validation for tool suffix ↔ required command.
Registration workflow unclear	Extended register_manifests.py to register role manifests, operator-control manifests, and the tool-capability map atomically.
Test missing	Added test_tool_capability_map_json_schema_validates_canonical_artifact.py plus registration workflow tests.


Chief Architect recommendation

Treat this as an in-place patch to v1.11.4, not a new architecture revision.

Proceed directly to:

Kimi → AXIOM_Implementation_v1.12

after Evaluator delta-confirmation.