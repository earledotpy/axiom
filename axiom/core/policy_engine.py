from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from axiom.core.tool_capability_map import get_all_tool_ids, get_tool_entry


class PolicyDeniedError(RuntimeError):
    pass


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str
    details: dict[str, Any] | None = None

    @classmethod
    def denied(cls, reason: str, details: dict[str, Any] | None = None) -> "PolicyDecision":
        return cls(allowed=False, reason=reason, details=details)

    @classmethod
    def allow(cls, reason: str, details: dict[str, Any] | None = None) -> "PolicyDecision":
        return cls(allowed=True, reason=reason, details=details)


def require_policy(manifest: dict[str, Any], policy_name: str) -> dict[str, Any]:
    policy = manifest.get(policy_name)
    if not isinstance(policy, dict):
        raise PolicyDeniedError(f"Missing or invalid required policy object: {policy_name}")
    return policy


class PolicyEngine:
    """
    Stateless policy evaluator using boot-time cached tool IDs.

    Authorization rule:
    1. tool_id must be known in loaded tool_capability_map.
    2. required manifest type must match.
    3. tool_id must be in manifest.allowed_tools.
    4. tool_id must not be in manifest.forbidden_tools.
    5. mapped capability source must permit the operation.
    6. session_controller.* requires operator_control manifest and command binding.
    7. every additional check must pass.
    """

    REQUIRED_POLICY_OBJECTS = (
        "budget_policy",
        "allowed_capabilities",
        "network_policy",
        "sandbox_policy",
        "memory_policy",
        "audit_policy",
    )

    ROLE_REQUIRED_OBJECTS = ("role",)
    OPERATOR_CONTROL_REQUIRED_OBJECTS = ("operator_command", "authorization_policy")

    def __init__(self) -> None:
        self._valid_tool_ids = get_all_tool_ids()

    def validate_manifest_completeness(self, manifest: dict[str, Any]) -> PolicyDecision:
        try:
            for policy_name in self.REQUIRED_POLICY_OBJECTS:
                require_policy(manifest, policy_name)

            manifest_type = manifest.get("manifest_type")

            if manifest_type == "role":
                for policy_name in self.ROLE_REQUIRED_OBJECTS:
                    require_policy(manifest, policy_name)
            elif manifest_type == "operator_control":
                for policy_name in self.OPERATOR_CONTROL_REQUIRED_OBJECTS:
                    require_policy(manifest, policy_name)
            else:
                return PolicyDecision.denied(
                    reason="unknown_manifest_type",
                    details={"manifest_type": manifest_type},
                )

        except PolicyDeniedError as exc:
            return PolicyDecision.denied(reason="missing_required_policy_object", details={"error": str(exc)})

        return PolicyDecision.allow(reason="manifest_completeness_validated")

    def authorize_tool_use(
        self,
        tool_id: str,
        manifest: dict[str, Any],
        task_context: dict[str, Any] | None = None,
    ) -> PolicyDecision:
        task_context = task_context or {}

        completeness = self.validate_manifest_completeness(manifest)
        if not completeness.allowed:
            return completeness

        if tool_id not in self._valid_tool_ids:
            return PolicyDecision.denied(
                reason="unknown_tool_id",
                details={"tool_id": tool_id, "valid_tools": sorted(self._valid_tool_ids)},
            )

        tool_entry = get_tool_entry(tool_id)
        if not isinstance(tool_entry, dict):
            return PolicyDecision.denied(
                reason="missing_tool_capability_entry",
                details={"tool_id": tool_id},
            )

        required_manifest_type = tool_entry.get("requires_manifest_type")
        manifest_type = manifest.get("manifest_type")

        if required_manifest_type and manifest_type != required_manifest_type:
            return PolicyDecision.denied(
                reason="manifest_type_mismatch",
                details={
                    "tool_id": tool_id,
                    "required_manifest_type": required_manifest_type,
                    "actual_manifest_type": manifest_type,
                },
            )

        allowed_tools = manifest.get("allowed_tools", [])
        if tool_id not in allowed_tools:
            return PolicyDecision.denied(
                reason="tool_not_in_allowed_tools",
                details={"tool_id": tool_id, "allowed_tools": allowed_tools},
            )

        forbidden_tools = manifest.get("forbidden_tools", [])
        if tool_id in forbidden_tools:
            return PolicyDecision.denied(
                reason="tool_in_forbidden_tools",
                details={"tool_id": tool_id, "forbidden_tools": forbidden_tools},
            )

        source_path = tool_entry.get("source")
        source_value = self._resolve_source_path(manifest, source_path)

        if not self._capability_source_permits(tool_entry, source_value):
            return PolicyDecision.denied(
                reason="capability_source_not_granted",
                details={
                    "tool_id": tool_id,
                    "source_path": source_path,
                    "source_value": source_value,
                },
            )

        if tool_id.startswith("session_controller."):
            if manifest_type != "operator_control":
                return PolicyDecision.denied(
                    reason="session_controller_requires_operator_control_manifest",
                    details={"tool_id": tool_id, "manifest_type": manifest_type},
                )

            command_name = manifest.get("operator_command", {}).get("command_name")
            allowed_commands = (
                manifest.get("allowed_capabilities", {})
                .get("operator_control", {})
                .get("allowed_commands", [])
            )
            required_command = tool_entry.get("required_command")

            if command_name not in allowed_commands:
                return PolicyDecision.denied(
                    reason="operator_command_not_in_allowed_commands",
                    details={"command_name": command_name, "allowed_commands": allowed_commands},
                )

            if required_command and command_name != required_command:
                return PolicyDecision.denied(
                    reason="operator_command_does_not_match_tool_requirement",
                    details={
                        "command_name": command_name,
                        "required_command": required_command,
                    },
                )

        additional_checks = tool_entry.get("additional_checks", [])
        for check in additional_checks:
            check_result = self._run_additional_check(check, manifest, task_context)
            if not check_result["passed"]:
                return PolicyDecision.denied(
                    reason=f"additional_check_failed:{check}",
                    details={"check": check, "info": check_result.get("info")},
                )

        return PolicyDecision.allow(
            reason="all_authorization_steps_passed",
            details={"tool_id": tool_id, "steps_executed": 7},
        )

    def _resolve_source_path(self, manifest: dict[str, Any], path: str | None) -> Any:
        if not path:
            return None

        current: Any = manifest
        for part in path.split("."):
            if not isinstance(current, dict):
                return None
            current = current.get(part)

        return current

    def _capability_source_permits(self, tool_entry: dict[str, Any], source_value: Any) -> bool:
        required_command = tool_entry.get("required_command")

        if required_command is not None:
            return isinstance(source_value, list) and required_command in source_value

        return bool(source_value)

    def _run_additional_check(
        self,
        check_name: str,
        manifest: dict[str, Any],
        task_context: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Placeholder for gateway-specific policy checks.

        Later phases should replace these permissive placeholders with concrete
        checks for filesystem roots, network allowlists, sandbox limits, and
        memory constraints.
        """
        return {"passed": True, "info": "check_not_yet_implemented"}
