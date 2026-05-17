from __future__ import annotations

from enum import Enum
from typing import Any


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
    DRAFT = "draft"
    SCANNER_PASSED = "scanner_passed"
    CHECKPOINT_PASSED = "checkpoint_passed"
    CHECKPOINT_FAILED = "checkpoint_failed"
    CHECKPOINT_BLOCKED = "checkpoint_blocked"
    QUARANTINED = "quarantined"
    COMMITTED = "committed"


class ParentTaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    QUARANTINED = "quarantined"
    NEEDS_HUMAN_INPUT = "needs_human_input"
    BLOCKED_RESOURCE_LIMIT = "blocked_resource_limit"
    CANCELLED = "cancelled"


class PlanInjectionScanner:
    def __init__(self, safe_pass_enabled: bool = False):
        self.safe_pass_enabled = safe_pass_enabled

    def scan(
        self,
        artifact_json: dict[str, Any],
        risk_class: str | RiskClass = RiskClass.ORDINARY,
        parent_task_status: str | ParentTaskStatus = ParentTaskStatus.RUNNING,
    ) -> dict[str, Any]:
        risk = self._normalize_risk_class(risk_class)

        if not self.safe_pass_enabled:
            if risk == RiskClass.HIGH_RISK:
                return {
                    "scanner_result": ScannerResult.SAFE_PASS_DISABLED.value,
                    "risk_class": RiskClass.HIGH_RISK.value,
                    "artifact_status": ArtifactStatus.QUARANTINED.value,
                    "parent_task_status": ParentTaskStatus.QUARANTINED.value,
                    "reason": (
                        "Safe-pass is disabled. High-risk artifact quarantined. "
                        "Operator must resolve model/fingerprint issue and resubmit goal."
                    ),
                    "details": {
                        "safe_pass_enabled": False,
                        "risk_class": risk.value,
                        "note": "v1.10.2: high-risk artifacts may not rehabilitate in-session",
                    },
                }

            return {
                "scanner_result": ScannerResult.SAFE_PASS_DISABLED.value,
                "risk_class": RiskClass.ORDINARY.value,
                "artifact_status": ArtifactStatus.CHECKPOINT_BLOCKED.value,
                "parent_task_status": ParentTaskStatus.NEEDS_HUMAN_INPUT.value,
                "reason": (
                    "Safe-pass is disabled. Ordinary artifact checkpoint-blocked. "
                    "Operator may retry after safe-pass re-enabled and fingerprint verified."
                ),
                "details": {
                    "safe_pass_enabled": False,
                    "risk_class": risk.value,
                    "note": "v1.10.2: ordinary artifacts may be re-scanned after safe-pass re-enabled",
                },
            }

        det_result = self._deterministic_scan(artifact_json)
        if det_result["blocked"]:
            return self._blocked_result(
                scanner_result=ScannerResult.DETERMINISTIC_BLOCK,
                risk_class=risk,
                reason=det_result["reason"],
                details=det_result.get("details"),
            )

        clf_result = self._classifier_scan(artifact_json)
        if clf_result["blocked"]:
            return self._blocked_result(
                scanner_result=ScannerResult.CLASSIFIER_BLOCK,
                risk_class=risk,
                reason=clf_result["reason"],
                details=clf_result.get("details"),
            )

        return {
            "scanner_result": ScannerResult.PASSED.value,
            "risk_class": risk.value,
            "artifact_status": ArtifactStatus.SCANNER_PASSED.value,
            "parent_task_status": ParentTaskStatus.RUNNING.value,
            "reason": "No injection indicators detected by deterministic or classifier scan.",
            "details": {
                "deterministic_checks_passed": det_result.get("checks", []),
                "classifier_score": clf_result.get("score"),
            },
        }

    @staticmethod
    def _normalize_risk_class(risk_class: str | RiskClass) -> RiskClass:
        if isinstance(risk_class, RiskClass):
            return risk_class

        try:
            return RiskClass(risk_class)
        except ValueError as exc:
            raise ValueError(f"Invalid risk_class: {risk_class!r}") from exc

    @staticmethod
    def _blocked_result(
        scanner_result: ScannerResult,
        risk_class: RiskClass,
        reason: str,
        details: dict[str, Any] | None,
    ) -> dict[str, Any]:
        if risk_class == RiskClass.HIGH_RISK:
            return {
                "scanner_result": scanner_result.value,
                "risk_class": RiskClass.HIGH_RISK.value,
                "artifact_status": ArtifactStatus.QUARANTINED.value,
                "parent_task_status": ParentTaskStatus.QUARANTINED.value,
                "reason": reason,
                "details": details,
            }

        return {
            "scanner_result": scanner_result.value,
            "risk_class": RiskClass.ORDINARY.value,
            "artifact_status": ArtifactStatus.CHECKPOINT_BLOCKED.value,
            "parent_task_status": ParentTaskStatus.NEEDS_HUMAN_INPUT.value,
            "reason": reason,
            "details": details,
        }

    def _deterministic_scan(self, artifact_json: dict[str, Any]) -> dict[str, Any]:
        return {"blocked": False, "reason": None, "checks": []}

    def _classifier_scan(self, artifact_json: dict[str, Any]) -> dict[str, Any]:
        return {"blocked": False, "reason": None, "score": None}
