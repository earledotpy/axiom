from axiom.security.plan_injection_scanner import (
    ArtifactStatus,
    ParentTaskStatus,
    PlanInjectionScanner,
    RiskClass,
)


def test_safe_pass_disabled_ordinary_blocks_for_human_input():
    scanner = PlanInjectionScanner(safe_pass_enabled=False)

    result = scanner.scan({"plan": "test"}, risk_class=RiskClass.ORDINARY)

    assert result["scanner_result"] == "safe_pass_disabled"
    assert result["risk_class"] == "ordinary"
    assert result["artifact_status"] == "checkpoint_blocked"
    assert result["parent_task_status"] == "needs_human_input"


def test_safe_pass_disabled_high_risk_quarantines():
    scanner = PlanInjectionScanner(safe_pass_enabled=False)

    result = scanner.scan({"plan": "test"}, risk_class=RiskClass.HIGH_RISK)

    assert result["scanner_result"] == "safe_pass_disabled"
    assert result["risk_class"] == "high_risk"
    assert result["artifact_status"] == "quarantined"
    assert result["parent_task_status"] == "quarantined"


def test_artifact_status_enum_matches_schema_domain():
    expected_statuses = {
        "draft",
        "scanner_passed",
        "checkpoint_passed",
        "checkpoint_failed",
        "checkpoint_blocked",
        "quarantined",
        "committed",
    }

    assert {member.value for member in ArtifactStatus} == expected_statuses


def test_parent_task_status_enum_matches_schema_domain_and_has_no_blocked():
    expected_statuses = {
        "pending",
        "running",
        "completed",
        "failed",
        "quarantined",
        "needs_human_input",
        "blocked_resource_limit",
        "cancelled",
    }

    assert {member.value for member in ParentTaskStatus} == expected_statuses
    assert not hasattr(ParentTaskStatus, "BLOCKED")


def test_deterministic_block_ordinary_blocks_for_human_input():
    scanner = PlanInjectionScanner(safe_pass_enabled=True)
    scanner._deterministic_scan = lambda artifact: {
        "blocked": True,
        "reason": "deterministic hit",
        "details": {"rule": "test"},
    }

    result = scanner.scan({"plan": "test"}, risk_class="ordinary")

    assert result["scanner_result"] == "deterministic_block"
    assert result["risk_class"] == "ordinary"
    assert result["artifact_status"] == "checkpoint_blocked"
    assert result["parent_task_status"] == "needs_human_input"


def test_deterministic_block_high_risk_quarantines():
    scanner = PlanInjectionScanner(safe_pass_enabled=True)
    scanner._deterministic_scan = lambda artifact: {
        "blocked": True,
        "reason": "deterministic hit",
        "details": {"rule": "test"},
    }

    result = scanner.scan({"plan": "test"}, risk_class="high_risk")

    assert result["scanner_result"] == "deterministic_block"
    assert result["risk_class"] == "high_risk"
    assert result["artifact_status"] == "quarantined"
    assert result["parent_task_status"] == "quarantined"


def test_classifier_block_ordinary_blocks_for_human_input():
    scanner = PlanInjectionScanner(safe_pass_enabled=True)
    scanner._deterministic_scan = lambda artifact: {
        "blocked": False,
        "reason": None,
        "checks": [],
    }
    scanner._classifier_scan = lambda artifact: {
        "blocked": True,
        "reason": "classifier hit",
        "details": {"score": 0.99},
    }

    result = scanner.scan({"plan": "test"}, risk_class="ordinary")

    assert result["scanner_result"] == "classifier_block"
    assert result["risk_class"] == "ordinary"
    assert result["artifact_status"] == "checkpoint_blocked"
    assert result["parent_task_status"] == "needs_human_input"


def test_classifier_block_high_risk_quarantines():
    scanner = PlanInjectionScanner(safe_pass_enabled=True)
    scanner._deterministic_scan = lambda artifact: {
        "blocked": False,
        "reason": None,
        "checks": [],
    }
    scanner._classifier_scan = lambda artifact: {
        "blocked": True,
        "reason": "classifier hit",
        "details": {"score": 0.99},
    }

    result = scanner.scan({"plan": "test"}, risk_class="high_risk")

    assert result["scanner_result"] == "classifier_block"
    assert result["risk_class"] == "high_risk"
    assert result["artifact_status"] == "quarantined"
    assert result["parent_task_status"] == "quarantined"


def test_scanner_passes_when_safe_pass_enabled_and_no_blocks():
    scanner = PlanInjectionScanner(safe_pass_enabled=True)

    result = scanner.scan({"plan": "test"}, risk_class="ordinary")

    assert result["scanner_result"] == "passed"
    assert result["risk_class"] == "ordinary"
    assert result["artifact_status"] == "scanner_passed"
    assert result["parent_task_status"] == "running"
