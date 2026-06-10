from pathlib import Path

from axiom.core.orchestrator.integration import (
    deterministic_report_json,
    run_offline_integration_file,
)


FIXTURE_PATH = Path("tests/level2a/orchestrator/fixtures/integration_scenarios.json")


def test_deterministic_report_output_is_stable_across_repeated_runs():
    first = deterministic_report_json(run_offline_integration_file(FIXTURE_PATH))
    second = deterministic_report_json(run_offline_integration_file(FIXTURE_PATH))

    assert first == second
    assert "offline_fixture_evidence_only" in first
    assert "verified_commit_emitted" in first


def test_carry_forward_items_remain_explicitly_classified():
    report = run_offline_integration_file(FIXTURE_PATH)

    assert report["carry_forward"] == {
        "T04_cryptographic_tamper": "pending_until_signature_verification_exists",
        "canonical_json_bytes": "deterministic_local_canonicalization_not_true_rfc8785_jcs",
        "rule_failure_audit_event": "inert_substrate_placeholder",
    }
