from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from axiom.persistence.db import get_connection


ROOT = Path(__file__).resolve().parents[2]
POLICY_ROOT = ROOT / "axiom" / "policy"

MANIFEST_SCHEMA_PATH = POLICY_ROOT / "schemas" / "manifest_schema.json"
TOOL_MAP_SCHEMA_PATH = POLICY_ROOT / "schemas" / "tool_capability_map_schema.json"
TOOL_MAP_PATH = POLICY_ROOT / "security_artifacts" / "tool_capability_map.json"
SCHEMA_SQL_PATH = ROOT / "axiom" / "persistence" / "schema.sql"

EXPECTED_TOOL_MAP_ID = "security.tool_capability_map.v1"

EXPECTED_ARTIFACT_STATUSES = {
    "draft",
    "scanner_passed",
    "checkpoint_passed",
    "checkpoint_failed",
    "checkpoint_blocked",
    "quarantined",
    "committed",
}

EXPECTED_PARENT_TASK_STATUSES = {
    "pending",
    "running",
    "completed",
    "failed",
    "quarantined",
    "needs_human_input",
    "blocked_resource_limit",
    "cancelled",
}

EXPECTED_SECURITY_EVENT_SEVERITIES = {"info", "warning", "critical"}
EXPECTED_SECURITY_EVENT_INDEXES = {
    "idx_security_events_session_created",
    "idx_security_events_task",
    "idx_security_events_type",
}
EXPECTED_SECURITY_EVENT_FK_TABLES = {"sessions", "tasks"}

POLICY_MANIFEST_TYPES = {"role", "operator_control"}
EXPECTED_SESSION_CONTROLLER_TOOL_COMMANDS = {
    "session_controller.status": "status",
    "session_controller.cancel_current_chain": "cancel_current_chain",
    "session_controller.pause_after_current": "pause_after_current",
    "session_controller.resume": "resume",
    "session_controller.shutdown_after_current": "shutdown_after_current",
    "session_controller.run_classifier_validation": "run_classifier_validation",
    "session_controller.enable_autonomous": "enable_autonomous",
    "session_controller.reconcile_provider_usage": "reconcile_provider_usage",
}
EXPECTED_STANDARD_TOOL_IDS = {
    "model_gateway.call",
    "memory_gateway.query",
    "memory_gateway.write",
    "network_gateway.fetch",
    "sandbox_gateway.execute",
    "filesystem.read",
    "filesystem.write",
}
EXPECTED_TOOL_IDS = (
    EXPECTED_STANDARD_TOOL_IDS | set(EXPECTED_SESSION_CONTROLLER_TOOL_COMMANDS)
)
EXPECTED_STANDARD_TOOL_CONTRACTS = {
    "model_gateway.call": {
        "source": "allowed_capabilities.model.allow_model_calls",
        "additional_checks": {
            "provider_group_allowed",
            "budget_policy_not_exceeded",
        },
    },
    "memory_gateway.query": {
        "source": "memory_policy.read",
        "additional_checks": {"memory_policy.max_query_results"},
    },
    "memory_gateway.write": {
        "source": "memory_policy.write",
        "additional_checks": {"memory_policy.write_requires_dedupe"},
    },
    "network_gateway.fetch": {
        "source": "network_policy",
        "additional_checks": {
            "mode_allowlist_only",
            "request_matches_allowlist",
            "request_does_not_match_denylist",
            "redirect_policy",
            "timeout_seconds",
            "max_response_bytes",
        },
    },
    "sandbox_gateway.execute": {
        "source": "sandbox_policy.allowed",
        "additional_checks": {
            "sandbox_policy.max_ram_mb",
            "sandbox_policy.max_wall_clock_seconds",
            "sandbox_policy.network_access_denied",
        },
    },
    "filesystem.read": {
        "source": "allowed_capabilities.filesystem.read",
        "additional_checks": {"path_under_allowed_roots"},
    },
    "filesystem.write": {
        "source": "allowed_capabilities.filesystem.write",
        "additional_checks": {"path_under_allowed_roots"},
    },
}
OPERATOR_CONTROL_COMMAND_SOURCE = (
    "allowed_capabilities.operator_control.allowed_commands"
)


@dataclass(frozen=True)
class PolicySecurityAuditViolation:
    check: str
    reason: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "check": self.check,
            "reason": self.reason,
            "details": self.details,
        }


@dataclass(frozen=True)
class PolicySecurityAuditResult:
    passed: bool
    checked: list[str]
    violations: list[PolicySecurityAuditViolation]

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "checked": self.checked,
            "violation_count": len(self.violations),
            "violations": [violation.to_dict() for violation in self.violations],
        }


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_policy_path(relative_path: str) -> Path:
    return POLICY_ROOT / relative_path.removeprefix("policy/")


def _add_violation(
    violations: list[PolicySecurityAuditViolation],
    check: str,
    reason: str,
    **details: Any,
) -> None:
    violations.append(
        PolicySecurityAuditViolation(
            check=check,
            reason=reason,
            details=details,
        )
    )


def _extract_check_domain(sql: str, column_name: str) -> set[str]:
    pattern = re.compile(
        rf"{re.escape(column_name)}\s+TEXT\s+[^,]*?CHECK\s*\(\s*"
        rf"{re.escape(column_name)}\s+IN\s*\((.*?)\)\s*\)",
        re.IGNORECASE | re.DOTALL,
    )
    match = pattern.search(sql)
    if not match:
        return set()

    return set(re.findall(r"'([^']+)'", match.group(1)))


def _extract_operator_command_domain(manifest_schema: dict[str, Any]) -> set[str]:
    try:
        return set(
            manifest_schema["$defs"]["operator_control_manifest"]["properties"][
                "operator_command"
            ]["properties"]["command_name"]["enum"]
        )
    except KeyError:
        return set()


def _audit_tool_capability_map_semantics(
    *,
    tool_map: dict[str, Any],
    manifest_schema: dict[str, Any],
    violations: list[PolicySecurityAuditViolation],
) -> None:
    check = "tool_capability_map_semantic_contracts"
    tools = tool_map.get("tools")
    if not isinstance(tools, dict):
        _add_violation(violations, check, "tools_object_missing_or_invalid")
        return

    actual_tool_ids = set(tools)
    missing_tool_ids = EXPECTED_TOOL_IDS - actual_tool_ids
    unexpected_tool_ids = actual_tool_ids - EXPECTED_TOOL_IDS

    if missing_tool_ids:
        _add_violation(
            violations,
            check,
            "tool_capability_map_missing_required_tools",
            missing=sorted(missing_tool_ids),
        )

    if unexpected_tool_ids:
        _add_violation(
            violations,
            check,
            "tool_capability_map_declares_unexpected_tools",
            unexpected=sorted(unexpected_tool_ids),
        )

    operator_command_domain = _extract_operator_command_domain(manifest_schema)
    expected_commands = set(EXPECTED_SESSION_CONTROLLER_TOOL_COMMANDS.values())

    if operator_command_domain and operator_command_domain != expected_commands:
        _add_violation(
            violations,
            check,
            "operator_command_domain_mismatch",
            expected=sorted(expected_commands),
            actual=sorted(operator_command_domain),
        )

    observed_required_commands: dict[str, str] = {}

    for tool_id, entry in tools.items():
        if not isinstance(entry, dict):
            _add_violation(
                violations,
                check,
                "tool_capability_entry_invalid",
                tool_id=tool_id,
            )
            continue

        required_command = entry.get("required_command")
        requires_manifest_type = entry.get("requires_manifest_type")
        source = entry.get("source")

        if tool_id.startswith("session_controller."):
            expected_command = EXPECTED_SESSION_CONTROLLER_TOOL_COMMANDS.get(tool_id)
            if expected_command is None:
                _add_violation(
                    violations,
                    check,
                    "unexpected_session_controller_tool",
                    tool_id=tool_id,
                )
                continue

            if source != OPERATOR_CONTROL_COMMAND_SOURCE:
                _add_violation(
                    violations,
                    check,
                    "session_controller_source_mismatch",
                    tool_id=tool_id,
                    expected_source=OPERATOR_CONTROL_COMMAND_SOURCE,
                    actual_source=source,
                )

            if required_command != expected_command:
                _add_violation(
                    violations,
                    check,
                    "session_controller_required_command_mismatch",
                    tool_id=tool_id,
                    expected_command=expected_command,
                    actual_command=required_command,
                )

            if requires_manifest_type != "operator_control":
                _add_violation(
                    violations,
                    check,
                    "session_controller_manifest_type_mismatch",
                    tool_id=tool_id,
                    expected_manifest_type="operator_control",
                    actual_manifest_type=requires_manifest_type,
                )

            additional_checks = entry.get("additional_checks", [])
            if additional_checks not in ([], None):
                _add_violation(
                    violations,
                    check,
                    "session_controller_declares_additional_checks",
                    tool_id=tool_id,
                    additional_checks=additional_checks,
                )

            if isinstance(required_command, str):
                if required_command not in operator_command_domain:
                    _add_violation(
                        violations,
                        check,
                        "session_controller_command_not_in_schema_domain",
                        tool_id=tool_id,
                        required_command=required_command,
                        operator_command_domain=sorted(operator_command_domain),
                    )
                elif required_command in observed_required_commands:
                    _add_violation(
                        violations,
                        check,
                        "duplicate_operator_control_command_binding",
                        command_name=required_command,
                        first_tool_id=observed_required_commands[required_command],
                        duplicate_tool_id=tool_id,
                    )
                else:
                    observed_required_commands[required_command] = tool_id

            continue

        if required_command is not None:
            _add_violation(
                violations,
                check,
                "standard_tool_declares_required_command",
                tool_id=tool_id,
                required_command=required_command,
            )

        if requires_manifest_type is not None:
            _add_violation(
                violations,
                check,
                "standard_tool_declares_manifest_type",
                tool_id=tool_id,
                requires_manifest_type=requires_manifest_type,
            )

        expected_contract = EXPECTED_STANDARD_TOOL_CONTRACTS.get(tool_id)
        if expected_contract is None:
            continue

        if source != expected_contract["source"]:
            _add_violation(
                violations,
                check,
                "standard_tool_source_mismatch",
                tool_id=tool_id,
                expected_source=expected_contract["source"],
                actual_source=source,
            )

        additional_checks = set(entry.get("additional_checks", []))
        expected_additional_checks = expected_contract["additional_checks"]
        if additional_checks != expected_additional_checks:
            _add_violation(
                violations,
                check,
                "standard_tool_additional_checks_mismatch",
                tool_id=tool_id,
                expected_additional_checks=sorted(expected_additional_checks),
                actual_additional_checks=sorted(additional_checks),
            )

    if operator_command_domain:
        missing_command_bindings = operator_command_domain - set(
            observed_required_commands
        )
        if missing_command_bindings:
            _add_violation(
                violations,
                check,
                "operator_commands_missing_session_controller_binding",
                missing=sorted(missing_command_bindings),
            )


def audit_policy_security() -> PolicySecurityAuditResult:
    checked: list[str] = []
    violations: list[PolicySecurityAuditViolation] = []
    active_manifest_payloads: list[tuple[Any, Path, dict[str, Any]]] = []

    checked.append("required_policy_files_exist")
    for path in (
        MANIFEST_SCHEMA_PATH,
        TOOL_MAP_SCHEMA_PATH,
        TOOL_MAP_PATH,
        SCHEMA_SQL_PATH,
    ):
        if not path.exists():
            _add_violation(
                violations,
                "required_policy_files_exist",
                "missing_file",
                path=str(path),
            )

    checked.append("policy_json_files_parse")
    for path in (MANIFEST_SCHEMA_PATH, TOOL_MAP_SCHEMA_PATH, TOOL_MAP_PATH):
        if path.exists():
            try:
                _load_json(path)
            except Exception as exc:
                _add_violation(
                    violations,
                    "policy_json_files_parse",
                    "invalid_json",
                    path=str(path),
                    error=str(exc),
                )

    checked.append("active_tool_capability_map_row_exists")
    tool_map_row = None
    with get_connection() as conn:
        tool_map_row = conn.execute(
            """
            SELECT manifest_id, manifest_type, relative_path, sha256, active
            FROM manifest_fingerprints
            WHERE manifest_id = ?
              AND manifest_type = 'tool_capability_map'
              AND active = 1
            """,
            (EXPECTED_TOOL_MAP_ID,),
        ).fetchone()

        active_manifest_rows = conn.execute(
            """
            SELECT manifest_id, manifest_type, relative_path, sha256, active,
                   role_name, command_name
            FROM manifest_fingerprints
            WHERE active = 1
            ORDER BY manifest_type, manifest_id
            """
        ).fetchall()

        security_event_columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(security_events)").fetchall()
        }
        security_event_indexes = {
            row["name"]
            for row in conn.execute("PRAGMA index_list(security_events)").fetchall()
        }
        security_event_fk_tables = {
            row["table"]
            for row in conn.execute(
                "PRAGMA foreign_key_list(security_events)"
            ).fetchall()
        }

    if tool_map_row is None:
        _add_violation(
            violations,
            "active_tool_capability_map_row_exists",
            "missing_active_tool_capability_map",
            manifest_id=EXPECTED_TOOL_MAP_ID,
        )

    checked.append("active_manifest_files_exist_and_match_sha")
    for row in active_manifest_rows:
        relative_path = str(row["relative_path"])
        file_path = _resolve_policy_path(relative_path)

        if not file_path.exists():
            _add_violation(
                violations,
                "active_manifest_files_exist_and_match_sha",
                "registered_file_missing",
                manifest_id=row["manifest_id"],
                relative_path=relative_path,
                resolved_path=str(file_path),
            )
            continue

        actual_sha = _sha256_file(file_path)
        expected_sha = row["sha256"]

        if actual_sha != expected_sha:
            _add_violation(
                violations,
                "active_manifest_files_exist_and_match_sha",
                "sha256_mismatch",
                manifest_id=row["manifest_id"],
                relative_path=relative_path,
                expected_sha256=expected_sha,
                actual_sha256=actual_sha,
            )

    binder = None
    checked.append("manifest_binder_initializes")
    try:
        from axiom.core.manifest_binder import ManifestBinder

        binder = ManifestBinder(
            MANIFEST_SCHEMA_PATH,
            TOOL_MAP_SCHEMA_PATH,
            TOOL_MAP_PATH,
        )
    except Exception as exc:
        _add_violation(
            violations,
            "manifest_binder_initializes",
            "manifest_binder_failed",
            error=repr(exc),
        )

    policy_engine = None
    checked.append("policy_engine_initializes")
    try:
        from axiom.core.policy_engine import PolicyEngine

        policy_engine = PolicyEngine()
    except Exception as exc:
        _add_violation(
            violations,
            "policy_engine_initializes",
            "policy_engine_failed",
            error=repr(exc),
        )

    checked.append("tool_capability_map_semantic_contracts")
    try:
        tool_map = _load_json(TOOL_MAP_PATH)
        manifest_schema = _load_json(MANIFEST_SCHEMA_PATH)
        _audit_tool_capability_map_semantics(
            tool_map=tool_map,
            manifest_schema=manifest_schema,
            violations=violations,
        )
    except Exception as exc:
        _add_violation(
            violations,
            "tool_capability_map_semantic_contracts",
            "tool_capability_map_semantic_check_failed",
            error=repr(exc),
        )

    checked.append("active_policy_manifests_validate_schema_and_policy")
    for row in active_manifest_rows:
        manifest_type = str(row["manifest_type"])
        if manifest_type not in POLICY_MANIFEST_TYPES:
            continue

        relative_path = str(row["relative_path"])
        file_path = _resolve_policy_path(relative_path)
        if not file_path.exists():
            continue

        try:
            manifest = _load_json(file_path)
        except Exception as exc:
            _add_violation(
                violations,
                "active_policy_manifests_validate_schema_and_policy",
                "active_manifest_invalid_json",
                manifest_id=row["manifest_id"],
                relative_path=relative_path,
                error=str(exc),
            )
            continue

        active_manifest_payloads.append((row, file_path, manifest))

        if binder is None:
            _add_violation(
                violations,
                "active_policy_manifests_validate_schema_and_policy",
                "manifest_binder_unavailable",
                manifest_id=row["manifest_id"],
            )
        else:
            try:
                binder.validate_manifest(manifest)
            except Exception as exc:
                _add_violation(
                    violations,
                    "active_policy_manifests_validate_schema_and_policy",
                    "manifest_binder_validation_failed",
                    manifest_id=row["manifest_id"],
                    relative_path=relative_path,
                    error=repr(exc),
                )

        if policy_engine is None:
            _add_violation(
                violations,
                "active_policy_manifests_validate_schema_and_policy",
                "policy_engine_unavailable",
                manifest_id=row["manifest_id"],
            )
        else:
            decision = policy_engine.validate_manifest_completeness(manifest)
            if not decision.allowed:
                _add_violation(
                    violations,
                    "active_policy_manifests_validate_schema_and_policy",
                    "policy_manifest_incomplete",
                    manifest_id=row["manifest_id"],
                    relative_path=relative_path,
                    decision_reason=decision.reason,
                    decision_details=decision.details or {},
                )

    checked.append("active_policy_manifest_rows_match_payload_identity")
    for row, file_path, manifest in active_manifest_payloads:
        manifest_type = str(row["manifest_type"])
        relative_path = str(row["relative_path"])

        if manifest.get("manifest_id") != row["manifest_id"]:
            _add_violation(
                violations,
                "active_policy_manifest_rows_match_payload_identity",
                "manifest_id_row_payload_mismatch",
                registered_manifest_id=row["manifest_id"],
                payload_manifest_id=manifest.get("manifest_id"),
                relative_path=relative_path,
            )

        if manifest.get("manifest_type") != manifest_type:
            _add_violation(
                violations,
                "active_policy_manifest_rows_match_payload_identity",
                "manifest_type_row_payload_mismatch",
                manifest_id=row["manifest_id"],
                registered_manifest_type=manifest_type,
                payload_manifest_type=manifest.get("manifest_type"),
                relative_path=relative_path,
            )

        if manifest_type == "role":
            expected_prefix = "policy/role_manifests/"
            payload_role_name = manifest.get("role", {}).get("role_name")
            if not relative_path.startswith(expected_prefix):
                _add_violation(
                    violations,
                    "active_policy_manifest_rows_match_payload_identity",
                    "role_manifest_registered_outside_role_directory",
                    manifest_id=row["manifest_id"],
                    relative_path=relative_path,
                    expected_prefix=expected_prefix,
                )

            if row["role_name"] != payload_role_name:
                _add_violation(
                    violations,
                    "active_policy_manifest_rows_match_payload_identity",
                    "role_name_row_payload_mismatch",
                    manifest_id=row["manifest_id"],
                    registered_role_name=row["role_name"],
                    payload_role_name=payload_role_name,
                    relative_path=relative_path,
                )

            if row["command_name"] is not None:
                _add_violation(
                    violations,
                    "active_policy_manifest_rows_match_payload_identity",
                    "role_manifest_row_declares_command_name",
                    manifest_id=row["manifest_id"],
                    command_name=row["command_name"],
                    relative_path=relative_path,
                )

        if manifest_type == "operator_control":
            expected_prefix = "policy/operator_control_manifests/"
            payload_command_name = manifest.get("operator_command", {}).get(
                "command_name"
            )
            if not relative_path.startswith(expected_prefix):
                _add_violation(
                    violations,
                    "active_policy_manifest_rows_match_payload_identity",
                    "operator_manifest_registered_outside_operator_directory",
                    manifest_id=row["manifest_id"],
                    relative_path=relative_path,
                    expected_prefix=expected_prefix,
                )

            if row["command_name"] != payload_command_name:
                _add_violation(
                    violations,
                    "active_policy_manifest_rows_match_payload_identity",
                    "command_name_row_payload_mismatch",
                    manifest_id=row["manifest_id"],
                    registered_command_name=row["command_name"],
                    payload_command_name=payload_command_name,
                    relative_path=relative_path,
                )

            if row["role_name"] is not None:
                _add_violation(
                    violations,
                    "active_policy_manifest_rows_match_payload_identity",
                    "operator_manifest_row_declares_role_name",
                    manifest_id=row["manifest_id"],
                    role_name=row["role_name"],
                    relative_path=relative_path,
                )

    checked.append("role_manifests_do_not_declare_operator_control_commands")
    for row, file_path, manifest in active_manifest_payloads:
        if manifest.get("manifest_type") != "role":
            continue

        allowed_commands = (
            manifest.get("allowed_capabilities", {})
            .get("operator_control", {})
            .get("allowed_commands")
        )
        if allowed_commands != []:
            _add_violation(
                violations,
                "role_manifests_do_not_declare_operator_control_commands",
                "role_manifest_declares_operator_control_commands",
                manifest_id=row["manifest_id"],
                relative_path=str(file_path.relative_to(POLICY_ROOT)),
                allowed_commands=allowed_commands,
            )

    checked.append("operator_control_manifests_bind_single_command")
    for row, file_path, manifest in active_manifest_payloads:
        if manifest.get("manifest_type") != "operator_control":
            continue

        command_name = manifest.get("operator_command", {}).get("command_name")
        allowed_commands = (
            manifest.get("allowed_capabilities", {})
            .get("operator_control", {})
            .get("allowed_commands")
        )
        if allowed_commands != [command_name]:
            _add_violation(
                violations,
                "operator_control_manifests_bind_single_command",
                "operator_control_command_binding_mismatch",
                manifest_id=row["manifest_id"],
                relative_path=str(file_path.relative_to(POLICY_ROOT)),
                command_name=command_name,
                allowed_commands=allowed_commands,
            )

    checked.append("plan_injection_scanner_enum_domains_match_schema")
    try:
        from axiom.security.plan_injection_scanner import (
            ArtifactStatus,
            ParentTaskStatus,
        )

        artifact_values = {member.value for member in ArtifactStatus}
        parent_values = {member.value for member in ParentTaskStatus}

        if artifact_values != EXPECTED_ARTIFACT_STATUSES:
            _add_violation(
                violations,
                "plan_injection_scanner_enum_domains_match_schema",
                "artifact_status_enum_mismatch",
                expected=sorted(EXPECTED_ARTIFACT_STATUSES),
                actual=sorted(artifact_values),
            )

        if parent_values != EXPECTED_PARENT_TASK_STATUSES:
            _add_violation(
                violations,
                "plan_injection_scanner_enum_domains_match_schema",
                "parent_task_status_enum_mismatch",
                expected=sorted(EXPECTED_PARENT_TASK_STATUSES),
                actual=sorted(parent_values),
            )

        if hasattr(ParentTaskStatus, "BLOCKED"):
            _add_violation(
                violations,
                "plan_injection_scanner_enum_domains_match_schema",
                "blocked_status_must_not_exist",
            )
    except Exception as exc:
        _add_violation(
            violations,
            "plan_injection_scanner_enum_domains_match_schema",
            "scanner_enum_import_failed",
            error=repr(exc),
        )

    checked.append("plan_injection_scanner_return_contract_is_stable")
    try:
        from axiom.security.plan_injection_scanner import (
            SCAN_RESULT_CONTRACT_KEYS,
            PlanInjectionScanner,
            RiskClass,
            ScannerResult,
        )

        scanner_result_values = {member.value for member in ScannerResult}
        risk_values = {member.value for member in RiskClass}
        scanner_results = [
            PlanInjectionScanner(safe_pass_enabled=False).scan(
                {"plan": "audit"},
                risk_class=RiskClass.ORDINARY,
            ),
            PlanInjectionScanner(safe_pass_enabled=False).scan(
                {"plan": "audit"},
                risk_class=RiskClass.HIGH_RISK,
            ),
            PlanInjectionScanner(safe_pass_enabled=True).scan(
                {"plan": "audit"},
                risk_class=RiskClass.ORDINARY,
            ),
        ]

        for index, scanner_result in enumerate(scanner_results):
            result_keys = set(scanner_result)
            if result_keys != SCAN_RESULT_CONTRACT_KEYS:
                _add_violation(
                    violations,
                    "plan_injection_scanner_return_contract_is_stable",
                    "scanner_result_keys_mismatch",
                    result_index=index,
                    expected=sorted(SCAN_RESULT_CONTRACT_KEYS),
                    actual=sorted(result_keys),
                )

            if scanner_result.get("scanner_result") not in scanner_result_values:
                _add_violation(
                    violations,
                    "plan_injection_scanner_return_contract_is_stable",
                    "scanner_result_value_outside_enum",
                    result_index=index,
                    scanner_result=scanner_result.get("scanner_result"),
                )

            if scanner_result.get("risk_class") not in risk_values:
                _add_violation(
                    violations,
                    "plan_injection_scanner_return_contract_is_stable",
                    "risk_class_value_outside_enum",
                    result_index=index,
                    risk_class=scanner_result.get("risk_class"),
                )

            if scanner_result.get("artifact_status") not in EXPECTED_ARTIFACT_STATUSES:
                _add_violation(
                    violations,
                    "plan_injection_scanner_return_contract_is_stable",
                    "artifact_status_value_outside_schema_domain",
                    result_index=index,
                    artifact_status=scanner_result.get("artifact_status"),
                )

            if (
                scanner_result.get("parent_task_status")
                not in EXPECTED_PARENT_TASK_STATUSES
            ):
                _add_violation(
                    violations,
                    "plan_injection_scanner_return_contract_is_stable",
                    "parent_task_status_value_outside_schema_domain",
                    result_index=index,
                    parent_task_status=scanner_result.get("parent_task_status"),
                )

            reason = scanner_result.get("reason")
            if not isinstance(reason, str) or not reason:
                _add_violation(
                    violations,
                    "plan_injection_scanner_return_contract_is_stable",
                    "scanner_result_reason_missing_or_invalid",
                    result_index=index,
                    reason=reason,
                )
    except Exception as exc:
        _add_violation(
            violations,
            "plan_injection_scanner_return_contract_is_stable",
            "scanner_contract_check_failed",
            error=repr(exc),
        )

    checked.append("schema_domains_match_phase3_expectations")
    if SCHEMA_SQL_PATH.exists():
        sql = SCHEMA_SQL_PATH.read_text(encoding="utf-8")
        artifact_domain = _extract_check_domain(sql, "artifact_status")
        task_status_domain = _extract_check_domain(sql, "status")

        if artifact_domain and artifact_domain != EXPECTED_ARTIFACT_STATUSES:
            _add_violation(
                violations,
                "schema_domains_match_phase3_expectations",
                "artifact_status_schema_domain_mismatch",
                expected=sorted(EXPECTED_ARTIFACT_STATUSES),
                actual=sorted(artifact_domain),
            )

        if EXPECTED_PARENT_TASK_STATUSES - task_status_domain:
            _add_violation(
                violations,
                "schema_domains_match_phase3_expectations",
                "task_status_schema_domain_missing_values",
                expected=sorted(EXPECTED_PARENT_TASK_STATUSES),
                actual=sorted(task_status_domain),
                missing=sorted(EXPECTED_PARENT_TASK_STATUSES - task_status_domain),
            )

    checked.append("security_events_table_supports_audit_coverage")
    required_security_event_columns = {
        "event_id",
        "session_id",
        "task_id",
        "event_type",
        "reason",
        "severity",
        "details_json",
        "created_at",
    }

    missing_security_event_columns = (
        required_security_event_columns - security_event_columns
    )

    if missing_security_event_columns:
        _add_violation(
            violations,
            "security_events_table_supports_audit_coverage",
            "security_events_missing_columns",
            missing=sorted(missing_security_event_columns),
            actual=sorted(security_event_columns),
        )

    missing_security_event_indexes = (
        EXPECTED_SECURITY_EVENT_INDEXES - security_event_indexes
    )
    if missing_security_event_indexes:
        _add_violation(
            violations,
            "security_events_table_supports_audit_coverage",
            "security_events_missing_indexes",
            missing=sorted(missing_security_event_indexes),
            actual=sorted(security_event_indexes),
        )

    missing_security_event_fk_tables = (
        EXPECTED_SECURITY_EVENT_FK_TABLES - security_event_fk_tables
    )
    if missing_security_event_fk_tables:
        _add_violation(
            violations,
            "security_events_table_supports_audit_coverage",
            "security_events_missing_foreign_keys",
            missing=sorted(missing_security_event_fk_tables),
            actual=sorted(security_event_fk_tables),
        )

    if SCHEMA_SQL_PATH.exists():
        sql = SCHEMA_SQL_PATH.read_text(encoding="utf-8")
        severity_domain = _extract_check_domain(sql, "severity")
        if severity_domain != EXPECTED_SECURITY_EVENT_SEVERITIES:
            _add_violation(
                violations,
                "security_events_table_supports_audit_coverage",
                "security_events_severity_domain_mismatch",
                expected=sorted(EXPECTED_SECURITY_EVENT_SEVERITIES),
                actual=sorted(severity_domain),
            )

    return PolicySecurityAuditResult(
        passed=not violations,
        checked=checked,
        violations=violations,
    )
