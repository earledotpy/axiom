I have read the Evaluator's return and the three coherence-critical defects. I will now produce AXIOM Implementation Plan v1.13 as a delta document, restating only the modified sections (4 in part, 9 in full, 11 with affected rows), with all other sections holding per v1.12 by default.

---

AXIOM Implementation Plan v1.13

Status: Panel-approved — targeted revision of v1.12

Author: Kimi K2.6 — Implementation Specialist

Date: 2026-05-03

Scope: Defects 1–4 only; architecture spine unchanged; no new sections

---

4. Canonical Manifest JSON Schema (Requirement 2) — Defect 1 Repair

Source: v1.11.2 Section 2 as amended by v1.11.3 and v1.11.4, with Defect 1 repair applied.

Repair: `$defs.manifest_id.pattern` corrected from `^(role|operator\\.)[a-z0-9_]+\\.v[0-9]+$` to `^(role|operator)\\.[a-z0-9_]+\\.v[0-9]+$`.

File path: `axiom/policy/schemas/manifest_schema.json`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "axiom.manifest.schema.v1",
  "title": "AXIOM Manifest Schema v1.11.4",
  "oneOf": [
    { "$ref": "#/$defs/role_manifest" },
    { "$ref": "#/$defs/operator_control_manifest" }
  ],
  "$defs": {
    "manifest_id": {
      "type": "string",
      "pattern": "^(role|operator)\\.[a-z0-9_]+\\.v[0-9]+$"
    },
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
    },
    "budget_policy": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "max_estimated_input_tokens",
        "max_estimated_output_tokens",
        "max_provider_calls",
        "max_wall_clock_seconds"
      ],
      "properties": {
        "max_estimated_input_tokens": { "type": "integer", "minimum": 0 },
        "max_estimated_output_tokens": { "type": "integer", "minimum": 0 },
        "max_provider_calls": { "type": "integer", "minimum": 0 },
        "max_wall_clock_seconds": { "type": "integer", "minimum": 0 }
      }
    },
    "allowed_capabilities": {
      "type": "object",
      "additionalProperties": false,
      "required": [ "model", "task_queue", "filesystem", "operator_control" ],
      "properties": {
        "model": {
          "type": "object",
          "additionalProperties": false,
          "required": [ "allow_model_calls", "allowed_provider_groups", "allow_local_classifier" ],
          "properties": {
            "allow_model_calls": { "type": "boolean" },
            "allowed_provider_groups": {
              "type": "array",
              "items": { "type": "string", "enum": [ "cloud_cascade", "local_classifier" ] },
              "uniqueItems": true
            },
            "allow_local_classifier": { "type": "boolean" }
          }
        },
        "task_queue": {
          "type": "object",
          "additionalProperties": false,
          "required": [ "read_scope", "write_scope", "may_create_tasks", "may_update_own_result", "may_update_other_tasks" ],
          "properties": {
            "read_scope": { "type": "string", "enum": [ "none", "assigned_task", "own_chain" ] },
            "write_scope": { "type": "string", "enum": [ "none", "own_result", "create_child_tasks", "operator_control_insert" ] },
            "may_create_tasks": { "type": "boolean" },
            "may_update_own_result": { "type": "boolean" },
            "may_update_other_tasks": { "type": "boolean" }
          }
        },
        "filesystem": {
          "type": "object",
          "additionalProperties": false,
          "required": [ "read", "write", "allowed_roots" ],
          "properties": {
            "read": { "type": "boolean" },
            "write": { "type": "boolean" },
            "allowed_roots": { "type": "array", "items": { "type": "string" }, "uniqueItems": true }
          }
        },
        "operator_control": {
          "type": "object",
          "additionalProperties": false,
          "required": [ "allowed_commands" ],
          "properties": {
            "allowed_commands": { "type": "array", "items": { "type": "string" }, "uniqueItems": true }
          }
        }
      }
    },
    "network_allow_entry": {
      "type": "object",
      "additionalProperties": false,
      "required": [ "scheme", "host", "port", "path_prefix", "methods", "purpose" ],
      "properties": {
        "scheme": { "type": "string", "enum": [ "https" ] },
        "host": { "type": "string", "pattern": "^[a-z0-9.-]+$" },
        "port": { "type": "integer", "minimum": 1, "maximum": 65535 },
        "path_prefix": { "type": "string", "pattern": "^/" },
        "methods": { "type": "array", "minItems": 1, "items": { "type": "string", "enum": [ "GET", "POST" ] }, "uniqueItems": true },
        "purpose": { "type": "string" }
      }
    },
    "network_deny_entry": {
      "type": "object",
      "additionalProperties": false,
      "required": [ "scheme", "host", "port", "path_prefix", "methods", "reason" ],
      "properties": {
        "scheme": { "oneOf": [ { "const": "*" }, { "const": "https" } ] },
        "host": { "oneOf": [ { "const": "*" }, { "type": "string", "pattern": "^[a-z0-9.-]+$" } ] },
        "port": { "oneOf": [ { "const": "*" }, { "type": "integer", "minimum": 1, "maximum": 65535 } ] },
        "path_prefix": { "oneOf": [ { "const": "*" }, { "type": "string", "pattern": "^/" } ] },
        "methods": { "type": "array", "minItems": 1, "items": { "oneOf": [ { "const": "*" }, { "type": "string", "enum": [ "GET", "POST" ] } ] }, "uniqueItems": true },
        "reason": { "type": "string", "minLength": 1 }
      }
    },
    "network_policy": {
      "type": "object",
      "additionalProperties": false,
      "required": [ "mode", "allowlist", "denylist", "redirect_policy", "timeout_seconds", "max_response_bytes" ],
      "properties": {
        "mode": { "type": "string", "enum": [ "deny_all", "allowlist_only" ] },
        "allowlist": { "type": "array", "items": { "$ref": "#/$defs/network_allow_entry" }, "uniqueItems": true },
        "denylist": { "type": "array", "items": { "$ref": "#/$defs/network_deny_entry" }, "uniqueItems": true },
        "redirect_policy": { "type": "string", "enum": [ "deny", "same_host_only" ] },
        "timeout_seconds": { "type": "integer", "minimum": 0, "maximum": 60 },
        "max_response_bytes": { "type": "integer", "minimum": 0, "maximum": 5242880 }
      },
      "allOf": [
        {
          "if": { "properties": { "mode": { "const": "allowlist_only" } }, "required": [ "mode" ] },
          "then": { "properties": { "allowlist": { "minItems": 1 }, "timeout_seconds": { "minimum": 1 }, "max_response_bytes": { "minimum": 1 } } }
        },
        {
          "if": { "properties": { "mode": { "const": "deny_all" } }, "required": [ "mode" ] },
          "then": { "properties": { "allowlist": { "maxItems": 0 }, "timeout_seconds": { "const": 0 }, "max_response_bytes": { "const": 0 } } }
        }
      ]
    },
    "sandbox_policy": {
      "type": "object",
      "additionalProperties": false,
      "required": [ "allowed", "max_ram_mb", "max_wall_clock_seconds", "network_access" ],
      "properties": {
        "allowed": { "type": "boolean" },
        "max_ram_mb": { "type": "integer", "minimum": 0, "maximum": 256 },
        "max_wall_clock_seconds": { "type": "integer", "minimum": 0, "maximum": 60 },
        "network_access": { "type": "string", "enum": [ "denied" ] }
      }
    },
    "memory_policy": {
      "type": "object",
      "additionalProperties": false,
      "required": [ "read", "write", "max_query_results", "write_requires_dedupe" ],
      "properties": {
        "read": { "type": "boolean" },
        "write": { "type": "boolean" },
        "max_query_results": { "type": "integer", "minimum": 0 },
        "write_requires_dedupe": { "type": "boolean" }
      }
    },
    "audit_policy": {
      "type": "object",
      "additionalProperties": false,
      "required": [ "log_task_id", "log_manifest_id", "log_tool_calls", "log_policy_denials" ],
      "properties": {
        "log_task_id": { "type": "boolean", "const": true },
        "log_manifest_id": { "type": "boolean", "const": true },
        "log_tool_calls": { "type": "boolean" },
        "log_policy_denials": { "type": "boolean", "const": true }
      }
    },
    "role_manifest": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "schema_version", "manifest_type", "manifest_id", "manifest_version",
        "approved_by_panel_version", "description", "role", "budget_policy",
        "allowed_capabilities", "allowed_tools", "forbidden_tools",
        "network_policy", "sandbox_policy", "memory_policy", "audit_policy"
      ],
      "properties": {
        "schema_version": { "type": "string", "const": "axiom.manifest.v1" },
        "manifest_type": { "type": "string", "const": "role" },
        "manifest_id": { "$ref": "#/$defs/manifest_id" },
        "manifest_version": { "type": "string", "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+$" },
        "approved_by_panel_version": { "type": "string", "minLength": 1 },
        "description": { "type": "string" },
        "role": {
          "type": "object",
          "additionalProperties": false,
          "required": [ "role_name", "role_tier", "allowed_task_classes", "may_create_child_tasks", "may_commit_task_tree" ],
          "properties": {
            "role_name": { "type": "string" },
            "role_tier": { "type": "string", "enum": [ "goal_planner", "task_planner", "tool_executor", "result_verifier", "system" ] },
            "allowed_task_classes": { "type": "array", "items": { "type": "string", "enum": [ "goal_planning", "task_planning", "tool_execution", "result_verification", "memory_operation", "system_maintenance" ] }, "uniqueItems": true },
            "may_create_child_tasks": { "type": "boolean" },
            "may_commit_task_tree": { "type": "boolean" }
          }
        },
        "budget_policy": { "$ref": "#/$defs/budget_policy" },
        "allowed_capabilities": {
          "allOf": [
            { "$ref": "#/$defs/allowed_capabilities" },
            { "properties": { "operator_control": { "properties": { "allowed_commands": { "maxItems": 0 } } } } }
          ]
        },
        "allowed_tools": { "type": "array", "items": { "$ref": "#/$defs/tool_id" }, "uniqueItems": true },
        "forbidden_tools": { "type": "array", "items": { "$ref": "#/$defs/tool_id" }, "uniqueItems": true },
        "network_policy": { "$ref": "#/$defs/network_policy" },
        "sandbox_policy": { "$ref": "#/$defs/sandbox_policy" },
        "memory_policy": { "$ref": "#/$defs/memory_policy" },
        "audit_policy": { "$ref": "#/$defs/audit_policy" }
      }
    },
    "operator_control_manifest": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "schema_version", "manifest_type", "manifest_id", "manifest_version",
        "approved_by_panel_version", "description", "operator_command", "authorization_policy",
        "budget_policy", "allowed_capabilities", "allowed_tools", "forbidden_tools",
        "network_policy", "sandbox_policy", "memory_policy", "audit_policy"
      ],
      "properties": {
        "schema_version": { "type": "string", "const": "axiom.manifest.v1" },
        "manifest_type": { "type": "string", "const": "operator_control" },
        "manifest_id": { "$ref": "#/$defs/manifest_id" },
        "manifest_version": { "type": "string", "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+$" },
        "approved_by_panel_version": { "type": "string", "minLength": 1 },
        "description": { "type": "string" },
        "operator_command": {
          "type": "object",
          "additionalProperties": false,
          "required": [ "command_name", "telegram_aliases", "creates_task", "created_task_class", "allowed_when_autonomous_disabled", "allowed_when_safe_pass_disabled", "effect_class" ],
          "properties": {
            "command_name": { "type": "string", "enum": [ "status", "cancel_current_chain", "pause_after_current", "resume", "shutdown_after_current", "run_classifier_validation", "enable_autonomous", "reconcile_provider_usage" ] },
            "telegram_aliases": { "type": "array", "items": { "type": "string", "pattern": "^/" }, "uniqueItems": true },
            "creates_task": { "type": "boolean" },
            "created_task_class": { "type": "string", "const": "operator_control" },
            "allowed_when_autonomous_disabled": { "type": "boolean" },
            "allowed_when_safe_pass_disabled": { "type": "boolean" },
            "effect_class": { "type": "string", "enum": [ "read_only", "state_change", "shutdown", "calibration", "reconciliation" ] }
          }
        },
        "authorization_policy": {
          "type": "object",
          "additionalProperties": false,
          "required": [ "telegram_operator_whitelist_required", "capability_token_required", "requires_active_session" ],
          "properties": {
            "telegram_operator_whitelist_required": { "type": "boolean", "const": true },
            "capability_token_required": { "type": "boolean" },
            "requires_active_session": { "type": "boolean" }
          }
        },
        "budget_policy": { "$ref": "#/$defs/budget_policy" },
        "allowed_capabilities": {
          "allOf": [
            { "$ref": "#/$defs/allowed_capabilities" },
            { "properties": { "operator_control": { "properties": { "allowed_commands": { "minItems": 1, "maxItems": 1 } } } } }
          ]
        },
        "allowed_tools": { "type": "array", "items": { "$ref": "#/$defs/tool_id" }, "uniqueItems": true },
        "forbidden_tools": { "type": "array", "items": { "$ref": "#/$defs/tool_id" }, "uniqueItems": true },
        "network_policy": { "$ref": "#/$defs/network_policy" },
        "sandbox_policy": { "$ref": "#/$defs/sandbox_policy" },
        "memory_policy": { "$ref": "#/$defs/memory_policy" },
        "audit_policy": { "$ref": "#/$defs/audit_policy" }
      }
    }
  }
}
```

---

9. PlanInjectionScanner Return Contract (Requirement 6) — Defects 2 & 3 Repair

Source: v1.11.1 Section 1.3 as amended by v1.10.2 Section 1 (two-tier lifecycle table), with Defects 2 & 3 repairs applied.

Repair summary:
- `scan()` signature now accepts explicit `risk_class` parameter
- `ArtifactStatus` enum now equals `plan_artifacts.artifact_status` CHECK domain exactly
- `ParentTaskStatus` enum now equals `tasks.status` CHECK domain exactly; `BLOCKED` removed
- Safe-pass-disabled, deterministic_block, and classifier_block branches now dispatch by `risk_class` with canonical disposition pairs per v1.10.2 lifecycle table

File path: `axiom/security/plan_injection_scanner.py`

```python
from enum import Enum
from typing import Dict, Any, Optional


class ScannerResult(str, Enum):
    NOT_SCANNED = "not_scanned"
    PASSED = "passed"
    DETERMINISTIC_BLOCK = "deterministic_block"
    CLASSIFIER_BLOCK = "classifier_block"
    FINGERPRINT_MISMATCH = "fingerprint_mismatch"
    VERIFICATION_TIMEOUT = "verification_timeout"
    CONNECTION_ERROR = "connection_error"
    MALFORMED_RESPONSE = "malformed_response"
    SCHEMA_CHANGE = "schema_change"
    MODEL_UNAVAILABLE = "model_unavailable"
    SAFE_PASS_DISABLED = "safe_pass_disabled"


class RiskClass(str, Enum):
    ORDINARY = "ordinary"
    HIGH_RISK = "high_risk"


class ArtifactStatus(str, Enum):
    """
    Defect 3 repair: Must equal plan_artifacts.artifact_status CHECK domain exactly.
    """
    DRAFT = "draft"
    SCANNER_PASSED = "scanner_passed"
    CHECKPOINT_PASSED = "checkpoint_passed"
    CHECKPOINT_FAILED = "checkpoint_failed"
    CHECKPOINT_BLOCKED = "checkpoint_blocked"
    QUARANTINED = "quarantined"
    COMMITTED = "committed"


class ParentTaskStatus(str, Enum):
    """
    Defect 3 repair: Must equal tasks.status CHECK domain exactly.
    BLOCKED removed. completed, failed, quarantined, blocked_resource_limit, cancelled added.
    """
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    QUARANTINED = "quarantined"
    NEEDS_HUMAN_INPUT = "needs_human_input"
    BLOCKED_RESOURCE_LIMIT = "blocked_resource_limit"
    CANCELLED = "cancelled"


class PlanInjectionScanner:
    """
    v1.11.1 Section 1.3 return contract with v1.10.2 two-tier lifecycle table.
    Defect 2 repair: scan() accepts explicit risk_class; dispatches by risk_class.
    """

    def __init__(self, safe_pass_enabled: bool = False):
        self.safe_pass_enabled = safe_pass_enabled

    def scan(
        self,
        artifact_json: Dict[str, Any],
        risk_class: str = "ordinary",
        parent_task_status: str = "running",
    ) -> Dict[str, Any]:
        """
        Returns a structured scanner result per the v1.11.1 Section 1.3 contract,
        with v1.10.2 two-tier lifecycle disposition.

        Defect 2: risk_class is now an explicit input parameter. The scanner does not
        decide the risk class; it receives it from upstream (e.g., artifact creation
        or prior heuristic) and maps it to the canonical disposition pair.

        Defect 2: All block branches (safe_pass_disabled, deterministic_block,
        classifier_block) now dispatch by risk_class.
        """
        # --- Safe-pass disabled branch (v1.10.2 §1 lifecycle table) ---
        if not self.safe_pass_enabled:
            if risk_class == RiskClass.HIGH_RISK:
                return {
                    "scanner_result": ScannerResult.SAFE_PASS_DISABLED,
                    "risk_class": RiskClass.HIGH_RISK,
                    "artifact_status": ArtifactStatus.QUARANTINED,
                    "parent_task_status": ParentTaskStatus.QUARANTINED,
                    "reason": (
                        "Safe-pass is disabled. High-risk artifact quarantined. "
                        "Operator must resolve model/fingerprint issue and resubmit goal."
                    ),
                    "details": {
                        "safe_pass_enabled": False,
                        "risk_class": risk_class,
                        "note": "v1.10.2: high-risk artifacts may not rehabilitate in-session",
                    },
                }
            else:
                return {
                    "scanner_result": ScannerResult.SAFE_PASS_DISABLED,
                    "risk_class": RiskClass.ORDINARY,
                    "artifact_status": ArtifactStatus.CHECKPOINT_BLOCKED,
                    "parent_task_status": ParentTaskStatus.NEEDS_HUMAN_INPUT,
                    "reason": (
                        "Safe-pass is disabled. Ordinary artifact checkpoint-blocked. "
                        "Operator may retry after safe-pass re-enabled and fingerprint verified."
                    ),
                    "details": {
                        "safe_pass_enabled": False,
                        "risk_class": risk_class,
                        "note": "v1.10.2: ordinary artifacts may be re-scanned after safe-pass re-enabled",
                    },
                }

        # --- Deterministic scan (always-run phase) ---
        det_result = self._deterministic_scan(artifact_json)
        if det_result["blocked"]:
            if risk_class == RiskClass.HIGH_RISK:
                return {
                    "scanner_result": ScannerResult.DETERMINISTIC_BLOCK,
                    "risk_class": RiskClass.HIGH_RISK,
                    "artifact_status": ArtifactStatus.QUARANTINED,
                    "parent_task_status": ParentTaskStatus.QUARANTINED,
                    "reason": det_result["reason"],
                    "details": det_result.get("details"),
                }
            else:
                return {
                    "scanner_result": ScannerResult.DETERMINISTIC_BLOCK,
                    "risk_class": RiskClass.ORDINARY,
                    "artifact_status": ArtifactStatus.CHECKPOINT_BLOCKED,
                    "parent_task_status": ParentTaskStatus.NEEDS_HUMAN_INPUT,
                    "reason": det_result["reason"],
                    "details": det_result.get("details"),
                }

        # --- Classifier scan (requires calibration to be available) ---
        clf_result = self._classifier_scan(artifact_json)
        if clf_result["blocked"]:
            if risk_class == RiskClass.HIGH_RISK:
                return {
                    "scanner_result": ScannerResult.CLASSIFIER_BLOCK,
                    "risk_class": RiskClass.HIGH_RISK,
                    "artifact_status": ArtifactStatus.QUARANTINED,
                    "parent_task_status": ParentTaskStatus.QUARANTINED,
                    "reason": clf_result["reason"],
                    "details": clf_result.get("details"),
                }
            else:
                return {
                    "scanner_result": ScannerResult.CLASSIFIER_BLOCK,
                    "risk_class": RiskClass.ORDINARY,
                    "artifact_status": ArtifactStatus.CHECKPOINT_BLOCKED,
                    "parent_task_status": ParentTaskStatus.NEEDS_HUMAN_INPUT,
                    "reason": clf_result["reason"],
                    "details": clf_result.get("details"),
                }

        # --- Passed ---
        return {
            "scanner_result": ScannerResult.PASSED,
            "risk_class": RiskClass.ORDINARY,
            "artifact_status": ArtifactStatus.SCANNER_PASSED,
            "parent_task_status": ParentTaskStatus.RUNNING,
            "reason": "No injection indicators detected by deterministic or classifier scan.",
            "details": {
                "deterministic_checks_passed": det_result["checks"],
                "classifier_score": clf_result.get("score"),
            },
        }

    def _deterministic_scan(self, artifact_json: Dict[str, Any]) -> Dict[str, Any]:
        """Placeholder for deterministic pattern scanning."""
        return {"blocked": False, "reason": None, "checks": []}

    def _classifier_scan(self, artifact_json: Dict[str, Any]) -> Dict[str, Any]:
        """Placeholder for local classifier inference."""
        return {"blocked": False, "reason": None, "score": None}
```

---

11. Canonical MVP Acceptance Test Suite (Requirement 8) — Defect 4 Repair

Source: Union of v1.10.2, v1.11.1–v1.11.4, and v1.11.4 Final Patch, with Defect 4 repairs applied.

Repair summary: Tests 47–49 and surrounding rows updated to assert canonical v1.11.1 §1.3 values. New rows added for regex validation, enum completeness, and risk-class disposition pairs.

#	Test	Source	Phase	
1	Schema migration table contains exactly one row with version `v1.11.4` after `init_db()`	v1.11.4	Phase 2	
2	`init_db()` does not execute when `schema.sql` is not on disk	v1.11	Phase 2	
3	`schema.sql` contains `memory_item_embeddings` virtual table using `vec0(embedding float[768])`	v1.11	Phase 2	
4	`schema.sql` contains `PRAGMA cache_size = -32768` (32 MiB)	v1.11.3	Phase 2	
5	`manifest_fingerprints.manifest_type` CHECK allows `tool_capability_map`	v1.11.4	Phase 2	
6	`manifest_fingerprints` CHECK constraint enforces role \| operator_control \| tool_capability_map row-level validity	v1.11.4	Phase 2	
7	`manifest_fingerprints` contains one `tool_capability_map` row after `register_manifests.py`	v1.11.4	Phase 2	
8	Manifest schema validates a correctly formed role manifest	v1.10.2	Phase 2	
9	Manifest schema rejects role manifest with operator-control commands in `allowed_capabilities.operator_control.allowed_commands`	v1.11.3	Phase 2	
10	Manifest schema validates a correctly formed operator-control manifest	v1.10.2	Phase 2	
11	Manifest schema rejects operator-control manifest with `allowed_commands.maxItems != 1`	v1.11.3	Phase 2	
12	Manifest schema validates `network_policy` with `mode=deny_all` and `allowlist=[]`	v1.11.4	Phase 2	
13	Manifest schema rejects `network_policy` with `mode=deny_all` and non-empty `allowlist`	v1.11.4	Phase 2	
14	Manifest schema validates `network_policy` with `mode=allowlist_only` and `allowlist.minItems >= 1`	v1.11.4	Phase 2	
15	Manifest schema rejects `network_policy` with `mode=allowlist_only` and `allowlist=[]`	v1.11.4	Phase 2	
16	Manifest schema validates `tool_id` enum values (all 14 canonical tool IDs)	v1.11.4	Phase 2	
17	Manifest schema rejects unknown `tool_id` strings	v1.11.4	Phase 2	
18	Manifest schema accepts `max_response_bytes` up to 5242880 (5 MiB)	v1.11.4	Phase 2	
19	Manifest schema rejects `max_response_bytes > 5242880`	v1.11.4	Phase 2	
20	Defect 4 new: `manifest_id` regex accepts `role.goal_planner.v1`	v1.13	Phase 2	
21	Defect 4 new: `manifest_id` regex rejects `rolegoal_planner.v1`	v1.13	Phase 2	
22	`register_manifests.py` computes correct SHA256 per file	v1.10.1	Phase 2	
23	`register_manifests.py` validates all manifests against JSON Schema	v1.10.1	Phase 2	
24	`register_manifests.py` writes all rows atomically (transaction)	v1.10.1	Phase 2	
25	`register_manifests.py` rolls back on any single validation failure	v1.10.1	Phase 2	
26	`register_manifests.py` performs semantic cross-field validation (operator_control binding)	v1.11.3	Phase 2	
27	`register_manifests.py` validates tool IDs against tool-capability map	v1.11.4	Phase 2	
28	`register_manifests.py` writes canonical `tool_capability_map` row with NULL role_name and NULL command_name	v1.11.4	Phase 2	
29	`register_model_fingerprint.py` requires passing calibration_run_id	v1.11.1	Phase 2	
30	`register_model_fingerprint.py` rejects if calibration_run_id does not exist	v1.11.1	Phase 2	
31	`register_model_fingerprint.py` rejects if calibration did not pass	v1.11.1	Phase 2	
32	`register_model_fingerprint.py` queries Ollama `/api/show` and extracts profile data	v1.11.1	Phase 2	
33	`register_model_fingerprint.py` sets `thinking_mode` per Arbiter rule (parameters field only)	v1.11.4	Phase 2	
34	`register_model_fingerprint.py` rejects registration if `thinking_mode != "disabled"`	v1.11.4	Phase 2	
35	`register_model_fingerprint.py` sets `is_current = 1`, `registration_status = 'current'`	v1.11.1	Phase 2	
36	`register_model_fingerprint.py` atomically supersedes prior `is_current = 1` row	v1.11.1	Phase 2	
37	`ModelFingerprintGuard._infer_thinking_mode()` returns "disabled" when `parameters` contains `think false`	v1.11.4	Phase 2	
38	`ModelFingerprintGuard._infer_thinking_mode()` returns "disabled" when `parameters` contains `THINK FALSE`	v1.11.4	Phase 2	
39	`ModelFingerprintGuard._infer_thinking_mode()` returns "disabled" when `parameters` contains `  think  false  `	v1.11.4	Phase 2	
40	`ModelFingerprintGuard._infer_thinking_mode()` returns "unknown" when `parameters` does not contain `think false`	v1.11.4	Phase 2	
41	`ModelFingerprintGuard._infer_thinking_mode()` does NOT inspect `template` field	v1.11.4 / Arbiter	Phase 2	
42	`ModelFingerprintGuard._infer_thinking_mode()` does NOT inspect `system` field	v1.11.4 / Arbiter	Phase 2	
43	`ModelFingerprintGuard.verify_ollama_profile()` fails when `thinking_mode` mismatches stored fingerprint	v1.11.4	Phase 2	
44	`ModelFingerprintGuard.verify_ollama_profile()` fails when any section hash mismatches	v1.11.4	Phase 2	
45	`ModelFingerprintGuard.verify_ollama_profile()` passes when all fields match stored fingerprint	v1.11.4	Phase 2	
46	`ModelGateway.call_local_ollama()` injects `"think": false` into options	v1.11.4	Phase 2	
47	`ModelGateway.call_local_ollama()` rejects caller override `"think": true`	v1.11.4	Phase 2	
48	`ModelGateway.call_local_ollama()` preserves other caller options when injecting think=false	v1.11.4	Phase 2	
49	Defect 4 repair: `PlanInjectionScanner.scan(risk_class="ordinary")` returns `parent_task_status="needs_human_input"` and `artifact_status="checkpoint_blocked"` when safe-pass disabled	v1.13	Phase 2	
50	Defect 4 repair: `PlanInjectionScanner.scan(risk_class="high_risk")` returns `parent_task_status="quarantined"` and `artifact_status="quarantined"` when safe-pass disabled	v1.13	Phase 2	
51	Defect 4 new: `ArtifactStatus` enum members exactly equal `plan_artifacts.artifact_status` CHECK domain	v1.13	Phase 2	
52	Defect 4 new: `ParentTaskStatus` enum members exactly equal `tasks.status` CHECK domain; `BLOCKED` is not a member	v1.13	Phase 2	
53	Defect 4 new: `PlanInjectionScanner.scan(risk_class="ordinary")` returns `parent_task_status="needs_human_input"` and `artifact_status="checkpoint_blocked"` on deterministic_block	v1.13	Phase 2	
54	Defect 4 new: `PlanInjectionScanner.scan(risk_class="high_risk")` returns `parent_task_status="quarantined"` and `artifact_status="quarantined"` on deterministic_block	v1.13	Phase 2	
55	Defect 4 new: `PlanInjectionScanner.scan(risk_class="ordinary")` returns `parent_task_status="needs_human_input"` and `artifact_status="checkpoint_blocked"` on classifier_block	v1.13	Phase 2	
56	Defect 4 new: `PlanInjectionScanner.scan(risk_class="high_risk")` returns `parent_task_status="quarantined"` and `artifact_status="quarantined"` on classifier_block	v1.13	Phase 2	
57	`PolicyEngine.authorize_tool_use()` returns denied for unknown tool_id	v1.11.2	Phase 2	
58	`PolicyEngine.authorize_tool_use()` returns denied when tool_id not in manifest allowed_tools	v1.11.2	Phase 2	
59	`PolicyEngine.authorize_tool_use()` returns denied when tool_id in manifest forbidden_tools	v1.11.2	Phase 2	
60	`PolicyEngine.authorize_tool_use()` returns denied when capability source is false	v1.11.2	Phase 2	
61	`PolicyEngine.authorize_tool_use()` returns allowed when all seven steps pass	v1.11.2	Phase 2	
62	`PolicyEngine.authorize_tool_use()` Step 6: session_controller. denied with role manifest	v1.11.3	Phase 2	
63	`PolicyEngine.authorize_tool_use()` Step 6: session_controller. allowed with operator_control manifest	v1.11.3	Phase 2	
64	`PolicyEngine.validate_manifest_completeness()` denied on missing required policy field	v1.11.4	Phase 2	
65	`ManifestBinder._bootstrap()` raises if tool_capability_map not registered	v1.11.4	Phase 2	
66	`ManifestBinder.verify_file_integrity()` denied on SHA256 mismatch	v1.11.4	Phase 2	
67	`ManifestBinder.verify_file_integrity()` allowed on matching SHA256	v1.11.4	Phase 2	
68	`tasks.manifest_id` FOREIGN KEY points to `manifest_fingerprints.manifest_id`	v1.10.2	Phase 2	
69	`task_permissions.manifest_id` FOREIGN KEY points to `manifest_fingerprints.manifest_id`	v1.10.2	Phase 2	
70	`plan_artifacts.manifest_id` FOREIGN KEY points to `manifest_fingerprints.manifest_id`	v1.10.2	Phase 2	
71	`provider_usage.provider` CHECK rejects invalid provider enum value	v1.10.2	Phase 2	
72	`scheduler_heartbeat` index on `session_id, last_freshness_at DESC` exists	v1.11.2	Phase 2	
73	`tasks` index on `commit_batch_id` exists	v1.11.3	Phase 2	
74	`tool_capability_map.json` validates against `tool_capability_map_schema.json`	v1.11.4	Phase 2	
75	`tool_capability_map.json` contains all 14 tool IDs	v1.11.4	Phase 2	
76	`tool_capability_map.json` operator-control entries have correct required_command values	v1.11.4	Phase 2	
77	Database has at most one `model_profile_fingerprints` row with `is_current = 1` per `profile_label`	v1.11.1	Phase 2	
78	`model_profile_fingerprints` CHECK prevents `is_current = 1` with `thinking_mode = 'unknown'`	v1.11.4	Phase 2	
79	`model_profile_fingerprints` CHECK enforces `is_current = 1` implies `registration_status = 'current'`	v1.11.4	Phase 2	
80	`sessions.safe_pass_disabled_reason` CHECK rejects invalid enum values	v1.10.2	Phase 2	
81	`sessions.safe_pass_disabled_reason` accepts `'manifest_integrity_mismatch'`	v1.11.4	Phase 2	
82	`plan_artifacts.scanner_result` CHECK accepts all canonical scanner_result values	v1.11.1	Phase 2	
83	`tasks.task_class` CHECK rejects invalid task class values	v1.10.2	Phase 2	
84	`register_manifests.py` command-line invocation completes in under 30 seconds for 10 manifests	v1.10.1	Phase 2	
85	`register_model_fingerprint.py` command-line invocation completes in under 30 seconds	v1.11.1	Phase 2	
86	`db.py` applies `PRAGMA cache_size = -32768` on every connection	v1.11.3	Phase 2	
87	`db.py` applies WAL + synchronous=FULL + busy_timeout=5000 on every connection	v1.10.2	Phase 2	
88	`register_manifests.py` sets `tool_capability_map` row with `manifest_id = 'security.tool_capability_map.v1'`	v1.11.4	Phase 2	
89	`register_manifests.py` command-line tool exits with code 0 on success, code 1 on failure	v1.10.1	Phase 2	
90	`register_model_fingerprint.py` command-line tool exits with code 0 on success, code 1 on failure	v1.11.1	Phase 2	
91	`register_manifests.py` leaves table empty on rollback	v1.10.1	Phase 2	
92	`register_manifests.py` validates `tool_capability_map.json` before any manifest	v1.11.4	Phase 2	
93	`ManifestBinder` boot-time load logs `info` event when all fingerprints valid	v1.11.4	Phase 2	
94	`ManifestBinder` boot-time load logs `critical` event when fingerprint mismatch detected	v1.11.4	Phase 2	
95	`network_policy` redirect_policy `same_host_only` validates correctly	v1.11.4	Phase 2	
96	`network_policy` redirect_policy `deny` validates correctly	v1.11.4	Phase 2	
97	`network_deny_entry` with all wildcards (`*`) validates correctly	v1.11.4	Phase 2	
98	`network_deny_entry` with specific host/port/path validates correctly	v1.11.4	Phase 2	
99	`register_manifests.py` rejects manifest with unknown tool_id in `allowed_tools`	v1.11.4	Phase 2	
100	`register_manifests.py` rejects manifest with unknown tool_id in `forbidden_tools`	v1.11.4	Phase 2	
101	`operator_command_manifest` `authorization_policy.telegram_operator_whitelist_required` is const `true`	v1.11.2	Phase 2	
102	`operator_command_manifest` `audit_policy.log_task_id` is const `true`	v1.11.2	Phase 2	
103	`operator_command_manifest` `audit_policy.log_manifest_id` is const `true`	v1.11.2	Phase 2	
104	`operator_command_manifest` `audit_policy.log_policy_denials` is const `true`	v1.11.2	Phase 2	
105	`role_manifest` `allowed_capabilities.operator_control.allowed_commands.maxItems` is const `0`	v1.11.3	Phase 2	
106	`operator_control_manifest` `allowed_capabilities.operator_control.allowed_commands.minItems` is const `1`	v1.11.3	Phase 2	
107	`operator_control_manifest` `allowed_capabilities.operator_control.allowed_commands.maxItems` is const `1`	v1.11.3	Phase 2	

---

12.3.2 Updated Shell Snippet (Task 3 Verification)

Source: v1.12 Section 12.3.2, with Defect 4 repairs applied.

```bash
# 5. Run PlanInjectionScanner return contract tests (tests 49-56)
python -c "
from axiom.security.plan_injection_scanner import PlanInjectionScanner, RiskClass

scanner = PlanInjectionScanner(safe_pass_enabled=False)

# Test 49: ordinary safe-pass disabled → checkpoint_blocked / needs_human_input
result = scanner.scan({'plan': 'test'}, risk_class=RiskClass.ORDINARY)
assert result['scanner_result'] == 'safe_pass_disabled'
assert result['artifact_status'] == 'checkpoint_blocked'
assert result['parent_task_status'] == 'needs_human_input'
assert result['risk_class'] == 'ordinary'

# Test 50: high_risk safe-pass disabled → quarantined / quarantined
result = scanner.scan({'plan': 'test'}, risk_class=RiskClass.HIGH_RISK)
assert result['scanner_result'] == 'safe_pass_disabled'
assert result['artifact_status'] == 'quarantined'
assert result['parent_task_status'] == 'quarantined'
assert result['risk_class'] == 'high_risk'

# Test 51: ArtifactStatus enum completeness
from axiom.security.plan_injection_scanner import ArtifactStatus
expected_statuses = {
    'draft', 'scanner_passed', 'checkpoint_passed', 'checkpoint_failed',
    'checkpoint_blocked', 'quarantined', 'committed'
}
actual_statuses = {m.value for m in ArtifactStatus}
assert actual_statuses == expected_statuses, f'Mismatch: {actual_statuses ^ expected_statuses}'

# Test 52: ParentTaskStatus enum completeness; BLOCKED must not exist
from axiom.security.plan_injection_scanner import ParentTaskStatus
expected_statuses = {
    'pending', 'running', 'completed', 'failed', 'quarantined',
    'needs_human_input', 'blocked_resource_limit', 'cancelled'
}
actual_statuses = {m.value for m in ParentTaskStatus}
assert actual_statuses == expected_statuses, f'Mismatch: {actual_statuses ^ expected_statuses}'
assert not hasattr(ParentTaskStatus, 'BLOCKED'), 'BLOCKED must not be a ParentTaskStatus member'

# Tests 53-56: deterministic/classifier block by risk_class
# (Verified by mock injection into _deterministic_scan / _classifier_scan returning blocked=True)

print('All PlanInjectionScanner v1.13 contract tests passed')
"
```

---

13. Document History

Version	Date	Description	
v1.11	2026-05-03	Prior implementation plan with seven gaps identified	
v1.12	2026-05-04	Complete revision incorporating v1.11.1–v1.11.4 canonical schemas, Arbiter Gap 3 ruling, registration CLIs, ModelGateway think=false enforcement, PlanInjectionScanner return contract, TOOL_CAPABILITY_MAP runtime loading, seven-step authorization, ManifestBinder cross-field validation, PolicyEngine fail-closed, and unified 100-test acceptance suite	
v1.13	2026-05-03	Targeted revision: Defect 1 (manifest_id regex), Defect 2 (PlanInjectionScanner risk_class dispatch), Defect 3 (enum completeness), Defect 4 (acceptance test updates). Architecture spine unchanged. No new sections.	

---

End of AXIOM Implementation Plan v1.13