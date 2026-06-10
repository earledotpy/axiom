from pathlib import Path

from axiom.core.orchestrator.integration import run_offline_integration_file


FIXTURE_PATH = Path("tests/level2a/orchestrator/fixtures/integration_scenarios.json")


def test_valid_static_relay_artifact_is_accepted_by_offline_harness():
    report = run_offline_integration_file(FIXTURE_PATH)

    assert report["authority_status"] == "offline_fixture_evidence_only"
    assert report["runtime_authority_activated"] is False
    assert report["relay_results"] == [
        {
            "name": "valid_static_relay_artifact",
            "accepted": True,
            "envelope_id": "ENV-123e4567-e89b-42d3-a456-426614174000",
            "allowed_action_type": "present_for_review",
        }
    ]


def test_valid_docket_audit_and_path_fixtures_compose_through_substrate():
    report = run_offline_integration_file(FIXTURE_PATH)

    assert report["docket_results"] == [
        {
            "from_state": "verification_pending",
            "event": "record_evidence",
            "to_state": "verified_evidence_recorded",
        }
    ]
    assert report["audit_chain_valid"] is True
    assert report["audit_event_count"] == 2
    assert report["path_results"] == [
        {
            "name": "handoff_report_path",
            "raw_path": "$WORKSPACE_ROOT/governance/05_handoffs/implementation_report.json",
            "normalized_path": "/axiom/governance/05_handoffs/implementation_report.json",
            "allowed": True,
        }
    ]


def test_t01_t22_fixture_set_executes_without_runtime_paths():
    report = run_offline_integration_file(FIXTURE_PATH)
    t_case_results = report["t_case_results"]

    assert [item["id"] for item in t_case_results] == [f"T{index:02d}" for index in range(1, 23)]
    assert next(item for item in t_case_results if item["id"] == "T04")["status"] == "pending"
    assert all(item["status"] == "passed" for item in t_case_results if item["id"] != "T04")
