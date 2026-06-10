from pathlib import Path

from axiom.core.orchestrator.integration import run_offline_integration_file


FIXTURE_PATH = Path("tests/level2a/orchestrator/fixtures/integration_scenarios.json")


def test_command_peer_route_and_console_execution_fixtures_are_rejected():
    report = run_offline_integration_file(FIXTURE_PATH)
    rejected = {item["name"]: item for item in report["negative_results"]}

    assert rejected["command_envelope_rejected"]["rejected"] is True
    assert "ERR_RELAY_BLOCKED_ACTION" in rejected["command_envelope_rejected"]["reason"]
    assert rejected["peer_to_peer_route_rejected"]["rejected"] is True
    assert "peer-to-peer routing" in rejected["peer_to_peer_route_rejected"]["reason"]
    assert rejected["console_execution_rejected"]["rejected"] is True
    assert "ERR_RELAY_BLOCKED_ACTION" in rejected["console_execution_rejected"]["reason"]


def test_verified_commit_and_state_root_write_are_rejected_or_absent_by_design():
    report = run_offline_integration_file(FIXTURE_PATH)
    rejected = {item["name"]: item for item in report["negative_results"]}

    assert report["verified_commit_emitted"] is False
    assert rejected["verified_commit_rejected"]["rejected"] is True
    assert "verified_commit emission is outside offline harness authority" in rejected["verified_commit_rejected"]["reason"]
    assert rejected["axiom_state_root_write_rejected"]["rejected"] is True
    assert "approved workspace token" in rejected["axiom_state_root_write_rejected"]["reason"]
