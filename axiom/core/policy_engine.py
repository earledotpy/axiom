from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
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
        handlers = {
            "provider_group_allowed": self._check_provider_group_allowed,
            "budget_policy_not_exceeded": self._check_budget_policy_not_exceeded,
            "memory_policy.max_query_results": self._check_memory_max_query_results,
            "memory_policy.write_requires_dedupe": self._check_memory_write_requires_dedupe,
            "mode_allowlist_only": self._check_network_mode_allowlist_only,
            "request_matches_allowlist": self._check_network_request_matches_allowlist,
            "request_does_not_match_denylist": self._check_network_request_does_not_match_denylist,
            "redirect_policy": self._check_network_redirect_policy,
            "timeout_seconds": self._check_network_timeout_seconds,
            "max_response_bytes": self._check_network_max_response_bytes,
            "sandbox_policy.max_ram_mb": self._check_sandbox_max_ram_mb,
            "sandbox_policy.max_wall_clock_seconds": self._check_sandbox_max_wall_clock_seconds,
            "sandbox_policy.network_access_denied": self._check_sandbox_network_access_denied,
            "path_under_allowed_roots": self._check_path_under_allowed_roots,
        }
        handler = handlers.get(check_name)
        if handler is None:
            return {"passed": False, "info": "unknown_additional_check"}

        return handler(manifest, task_context)

    @staticmethod
    def _passed(info: Any = None) -> dict[str, Any]:
        return {"passed": True, "info": info}

    @staticmethod
    def _failed(info: Any) -> dict[str, Any]:
        return {"passed": False, "info": info}

    def _check_provider_group_allowed(
        self,
        manifest: dict[str, Any],
        task_context: dict[str, Any],
    ) -> dict[str, Any]:
        model_policy = manifest.get("allowed_capabilities", {}).get("model", {})
        allowed_groups = model_policy.get("allowed_provider_groups", [])
        requested_group = task_context.get("provider_group")

        if requested_group in allowed_groups:
            return self._passed({"provider_group": requested_group})

        return self._failed(
            {
                "provider_group": requested_group,
                "allowed_provider_groups": allowed_groups,
            }
        )

    def _check_budget_policy_not_exceeded(
        self,
        manifest: dict[str, Any],
        task_context: dict[str, Any],
    ) -> dict[str, Any]:
        budget = manifest.get("budget_policy", {})
        comparisons = {
            "estimated_input_tokens": "max_estimated_input_tokens",
            "estimated_output_tokens": "max_estimated_output_tokens",
            "estimated_provider_calls": "max_provider_calls",
            "estimated_wall_clock_seconds": "max_wall_clock_seconds",
        }

        missing = [
            value_name
            for value_name in comparisons
            if value_name not in task_context
        ]
        if missing:
            return self._failed({"missing_estimates": missing})

        exceeded = {}
        for value_name, limit_name in comparisons.items():
            value = task_context[value_name]
            limit = budget.get(limit_name)
            if not isinstance(value, int) or not isinstance(limit, int):
                return self._failed(
                    {
                        "invalid_budget_value": value_name,
                        "value": value,
                        "limit_name": limit_name,
                        "limit": limit,
                    }
                )
            if value > limit:
                exceeded[value_name] = {"value": value, "limit": limit}

        if exceeded:
            return self._failed({"exceeded": exceeded})

        return self._passed({"checked": sorted(comparisons)})

    def _check_memory_max_query_results(
        self,
        manifest: dict[str, Any],
        task_context: dict[str, Any],
    ) -> dict[str, Any]:
        requested = task_context.get("requested_query_results")
        limit = manifest.get("memory_policy", {}).get("max_query_results")
        if isinstance(requested, int) and isinstance(limit, int) and requested <= limit:
            return self._passed({"requested_query_results": requested, "limit": limit})
        return self._failed({"requested_query_results": requested, "limit": limit})

    def _check_memory_write_requires_dedupe(
        self,
        manifest: dict[str, Any],
        task_context: dict[str, Any],
    ) -> dict[str, Any]:
        requires_dedupe = manifest.get("memory_policy", {}).get(
            "write_requires_dedupe"
        )
        dedupe_performed = task_context.get("dedupe_performed")
        if requires_dedupe is True and dedupe_performed is True:
            return self._passed({"dedupe_performed": True})
        return self._failed(
            {
                "write_requires_dedupe": requires_dedupe,
                "dedupe_performed": dedupe_performed,
            }
        )

    def _check_network_mode_allowlist_only(
        self,
        manifest: dict[str, Any],
        task_context: dict[str, Any],
    ) -> dict[str, Any]:
        mode = manifest.get("network_policy", {}).get("mode")
        if mode == "allowlist_only":
            return self._passed({"mode": mode})
        return self._failed({"mode": mode})

    def _check_network_request_matches_allowlist(
        self,
        manifest: dict[str, Any],
        task_context: dict[str, Any],
    ) -> dict[str, Any]:
        request = task_context.get("network_request")
        if not isinstance(request, dict):
            return self._failed({"network_request": request})

        for entry in manifest.get("network_policy", {}).get("allowlist", []):
            if self._network_rule_matches(entry, request):
                return self._passed({"matched_allowlist_entry": entry})

        return self._failed({"network_request": request})

    def _check_network_request_does_not_match_denylist(
        self,
        manifest: dict[str, Any],
        task_context: dict[str, Any],
    ) -> dict[str, Any]:
        request = task_context.get("network_request")
        if not isinstance(request, dict):
            return self._failed({"network_request": request})

        for entry in manifest.get("network_policy", {}).get("denylist", []):
            if self._network_rule_matches(entry, request):
                return self._failed({"matched_denylist_entry": entry})

        return self._passed({"network_request": request})

    def _check_network_redirect_policy(
        self,
        manifest: dict[str, Any],
        task_context: dict[str, Any],
    ) -> dict[str, Any]:
        redirected = task_context.get("redirected", False)
        if redirected is False:
            return self._passed({"redirected": False})

        policy = manifest.get("network_policy", {}).get("redirect_policy")
        request = task_context.get("network_request", {})
        redirect_host = task_context.get("redirect_host")
        if (
            policy == "same_host_only"
            and isinstance(request, dict)
            and redirect_host == request.get("host")
        ):
            return self._passed({"redirect_policy": policy, "redirect_host": redirect_host})

        return self._failed(
            {"redirect_policy": policy, "redirect_host": redirect_host}
        )

    def _check_network_timeout_seconds(
        self,
        manifest: dict[str, Any],
        task_context: dict[str, Any],
    ) -> dict[str, Any]:
        requested = task_context.get("timeout_seconds")
        limit = manifest.get("network_policy", {}).get("timeout_seconds")
        if isinstance(requested, int) and isinstance(limit, int) and requested <= limit:
            return self._passed({"timeout_seconds": requested, "limit": limit})
        return self._failed({"timeout_seconds": requested, "limit": limit})

    def _check_network_max_response_bytes(
        self,
        manifest: dict[str, Any],
        task_context: dict[str, Any],
    ) -> dict[str, Any]:
        requested = task_context.get("max_response_bytes")
        limit = manifest.get("network_policy", {}).get("max_response_bytes")
        if isinstance(requested, int) and isinstance(limit, int) and requested <= limit:
            return self._passed({"max_response_bytes": requested, "limit": limit})
        return self._failed({"max_response_bytes": requested, "limit": limit})

    def _check_sandbox_max_ram_mb(
        self,
        manifest: dict[str, Any],
        task_context: dict[str, Any],
    ) -> dict[str, Any]:
        requested = task_context.get("sandbox_ram_mb")
        limit = manifest.get("sandbox_policy", {}).get("max_ram_mb")
        if isinstance(requested, int) and isinstance(limit, int) and requested <= limit:
            return self._passed({"sandbox_ram_mb": requested, "limit": limit})
        return self._failed({"sandbox_ram_mb": requested, "limit": limit})

    def _check_sandbox_max_wall_clock_seconds(
        self,
        manifest: dict[str, Any],
        task_context: dict[str, Any],
    ) -> dict[str, Any]:
        requested = task_context.get("sandbox_wall_clock_seconds")
        limit = manifest.get("sandbox_policy", {}).get("max_wall_clock_seconds")
        if isinstance(requested, int) and isinstance(limit, int) and requested <= limit:
            return self._passed(
                {"sandbox_wall_clock_seconds": requested, "limit": limit}
            )
        return self._failed(
            {"sandbox_wall_clock_seconds": requested, "limit": limit}
        )

    def _check_sandbox_network_access_denied(
        self,
        manifest: dict[str, Any],
        task_context: dict[str, Any],
    ) -> dict[str, Any]:
        network_access = manifest.get("sandbox_policy", {}).get("network_access")
        if network_access == "denied":
            return self._passed({"network_access": network_access})
        return self._failed({"network_access": network_access})

    def _check_path_under_allowed_roots(
        self,
        manifest: dict[str, Any],
        task_context: dict[str, Any],
    ) -> dict[str, Any]:
        requested_path = task_context.get("filesystem_path")
        allowed_roots = manifest.get("allowed_capabilities", {}).get(
            "filesystem", {}
        ).get("allowed_roots", [])

        if not isinstance(requested_path, str):
            return self._failed({"filesystem_path": requested_path})

        try:
            requested = Path(requested_path).resolve(strict=False)
            roots = [
                Path(root).resolve(strict=False)
                for root in allowed_roots
                if isinstance(root, str)
            ]
        except OSError as exc:
            return self._failed({"error": str(exc)})

        for root in roots:
            if requested == root or root in requested.parents:
                return self._passed(
                    {"filesystem_path": str(requested), "matched_root": str(root)}
                )

        return self._failed(
            {
                "filesystem_path": str(requested),
                "allowed_roots": [str(root) for root in roots],
            }
        )

    @staticmethod
    def _network_rule_matches(rule: dict[str, Any], request: dict[str, Any]) -> bool:
        method = request.get("method")
        request_path = request.get("path", "")
        methods = rule.get("methods", [])

        return (
            (rule.get("scheme") == "*" or rule.get("scheme") == request.get("scheme"))
            and (rule.get("host") == "*" or rule.get("host") == request.get("host"))
            and (rule.get("port") == "*" or rule.get("port") == request.get("port"))
            and (
                rule.get("path_prefix") == "*"
                or (
                    isinstance(request_path, str)
                    and request_path.startswith(rule.get("path_prefix", ""))
                )
            )
            and ("*" in methods or method in methods)
        )
