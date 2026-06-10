from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from axiom.core.autonomous_gate import AutonomousReadinessDecision
from axiom.core.orchestrator.state_machines import DocketState, MandateState, can_transition
from axiom.persistence.level2a.audit_chain import verify_audit_chain
from axiom.security.level2a.verifier import (
    NETWORK_BLOCKED_PYTEST,
    TrustedTestTarget,
    VerifierMandateEnvelope,
    VerificationResult,
    ensure_restricted_pytest_targets,
    execute_verification,
    sha256_file,
)


class MemoryAuditLedger:
    def __init__(self) -> None:
        self.events: list[dict] = []

    def append_event(self, event: dict) -> None:
        self.events.append(event)

    def read_events(self) -> list[dict]:
        return list(self.events)


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True)


def _make_repo(tmp_path: Path, *, risky_source: bool = False) -> tuple[Path, str]:
    repo = tmp_path / "repo"
    (repo / "axiom" / "module").mkdir(parents=True)
    (repo / "tests" / "level2a" / "security").mkdir(parents=True)
    subprocess.run(["git", "init", str(repo)], check=True, capture_output=True, text=True)
    _git(repo, "config", "user.email", "phase7@example.invalid")
    _git(repo, "config", "user.name", "Phase 7 Test")
    source = "import socket\n" if risky_source else "VALUE = 7\n"
    (repo / "axiom" / "module" / "candidate.py").write_text(source, encoding="utf-8")
    (repo / "tests" / "level2a" / "security" / "test_phase7_doctrine_eligibility.py").write_text(
        "def test_acceptance_fixture():\n    assert True\n",
        encoding="utf-8",
    )
    (repo / "artifact.txt").write_text("phase7 artifact\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "seed phase7 fixture")
    commit = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], check=True, capture_output=True, text=True)
    return repo, commit.stdout.strip()


def _trusted_test(repo: Path, *, content_sha256: str | None = None, identifier: str | None = None) -> TrustedTestTarget:
    identifier = identifier or "tests/level2a/security/test_phase7_doctrine_eligibility.py"
    return TrustedTestTarget(identifier, content_sha256 or sha256_file(repo / identifier))


def _envelope(
    repo: Path,
    commit: str,
    tmp_path: Path,
    *,
    authorized_hash: str | None = None,
    trusted_test: TrustedTestTarget | None = None,
) -> VerifierMandateEnvelope:
    return VerifierMandateEnvelope(
        mandate_id="MND-ACCEPTED-2026-0010",
        docket_id="DK-2026-0010",
        source_workspace=repo,
        target_commit=commit,
        artifact_path=repo / "artifact.txt",
        authorized_artifact_sha256=authorized_hash or sha256_file(repo / "artifact.txt"),
        modified_source_paths=(Path("axiom/module/candidate.py"),),
        trusted_tests=(trusted_test or _trusted_test(repo),),
        state_root=tmp_path / "state",
    )


def _passing_runner(args, *, cwd, env, capture_output, text, timeout):
    return subprocess.CompletedProcess(args, 0, stdout="passed", stderr="")


def _failing_runner(args, *, cwd, env, capture_output, text, timeout):
    return subprocess.CompletedProcess(args, 1, stdout="failed", stderr="assertion failed")


def test_acceptance_suite_valid_envelope_completes_with_verified_commit(tmp_path):
    repo, commit = _make_repo(tmp_path)
    ledger = MemoryAuditLedger()

    result = execute_verification(_envelope(repo, commit, tmp_path), audit_ledger=ledger, runner=_passing_runner)

    assert result == VerificationResult(
        success=True,
        docket_state=DocketState.VERIFIED_COMMIT,
        mandate_state=MandateState.COMPLETED,
        diagnostics=(),
        pytest_returncode=0,
    )
    assert verify_audit_chain(ledger.read_events())


def test_verifier_records_non_repudiable_audit_chain_for_all_success_phases(tmp_path):
    repo, commit = _make_repo(tmp_path)
    ledger = MemoryAuditLedger()

    execute_verification(_envelope(repo, commit, tmp_path), audit_ledger=ledger, runner=_passing_runner)

    event_types = [event["event_type"] for event in ledger.read_events()]
    assert event_types == [
        "artifact_hash_validated",
        "worktree_created",
        "ast_scan_completed",
        "pinned_tests_validated",
        "pytest_completed",
        "verified_commit_recorded",
    ]
    for event in ledger.read_events():
        assert event["event_payload_sha256"].startswith("sha256:")
        assert event["audit_chain_hash"].startswith("sha256:")
    assert ledger.read_events()[0].get("prior_audit_hash") is None
    for prior, current in zip(ledger.read_events(), ledger.read_events()[1:]):
        assert current["prior_audit_hash"] == prior["audit_chain_hash"]
    assert verify_audit_chain(ledger.read_events())


@pytest.mark.parametrize(
    ("label", "envelope_mutation", "runner", "expected_event"),
    [
        (
            "hash_mismatch",
            lambda repo, commit, tmp: _envelope(repo, commit, tmp, authorized_hash="sha256:" + "0" * 64),
            _passing_runner,
            "audit_failed",
        ),
        (
            "git_worktree_failure",
            lambda repo, commit, tmp: _envelope(repo, "not-a-commit", tmp),
            _passing_runner,
            "audit_failed",
        ),
        (
            "ast_violation",
            lambda repo, commit, tmp: _envelope(repo, commit, tmp),
            _passing_runner,
            "ast_scan_failed",
        ),
        (
            "pinned_hash_mismatch",
            lambda repo, commit, tmp: _envelope(
                repo,
                commit,
                tmp,
                trusted_test=_trusted_test(repo, content_sha256="sha256:" + "1" * 64),
            ),
            _passing_runner,
            "audit_failed",
        ),
        (
            "broad_collection",
            lambda repo, commit, tmp: _envelope(
                repo,
                commit,
                tmp,
                trusted_test=TrustedTestTarget("tests/level2a/", "sha256:" + "2" * 64),
            ),
            _passing_runner,
            "audit_failed",
        ),
        (
            "pytest_failure",
            lambda repo, commit, tmp: _envelope(repo, commit, tmp),
            _failing_runner,
            "audit_failed",
        ),
    ],
)
def test_verifier_failures_transition_to_failed_and_audit_failed(label, envelope_mutation, runner, expected_event, tmp_path):
    repo, commit = _make_repo(tmp_path, risky_source=(label == "ast_violation"))
    ledger = MemoryAuditLedger()

    result = execute_verification(envelope_mutation(repo, commit, tmp_path), audit_ledger=ledger, runner=runner)

    assert result.success is False
    assert result.docket_state is DocketState.FAILED
    assert result.mandate_state is MandateState.AUDIT_FAILED
    assert expected_event in [event["event_type"] for event in ledger.read_events()]
    assert ledger.read_events()[-1]["event_type"] == "audit_failed"
    assert verify_audit_chain(ledger.read_events())


def test_unpinned_direct_pytest_collection_attempt_fails_closed():
    trusted = [TrustedTestTarget("tests/level2a/security/test_phase7_doctrine_eligibility.py", "sha256:" + "2" * 64)]

    with pytest.raises(ValueError, match="ERR_BROAD_COLLECTION_VIOLATION"):
        ensure_restricted_pytest_targets(["tests/level2a/"], trusted)
    with pytest.raises(ValueError, match="ERR_BROAD_COLLECTION_VIOLATION"):
        ensure_restricted_pytest_targets(["tests/level2a/security/test_unpinned_phase7.py"], trusted)


def test_network_egress_breach_is_blocked_by_socket_monkeypatch():
    namespace: dict = {}
    exec(NETWORK_BLOCKED_PYTEST.split("import pytest", 1)[0], namespace)

    with pytest.raises(RuntimeError, match="ERR_NETWORK_BLOCKED"):
        namespace["socket"].socket()
    with pytest.raises(RuntimeError, match="ERR_NETWORK_BLOCKED"):
        namespace["socket"].create_connection(("127.0.0.1", 9))


def test_direct_verified_commit_transition_is_blocked_without_verifier_evidence():
    assert can_transition(DocketState.VERIFIED_EVIDENCE_RECORDED, "commit", DocketState)
    for state in DocketState:
        if state == DocketState.VERIFIED_EVIDENCE_RECORDED:
            continue
        assert not can_transition(state, "commit", DocketState)


def test_doctrine_shift_proof_uses_existing_fail_closed_invariants():
    decision = AutonomousReadinessDecision(allowed=False, blocking_reasons=["phase7_doctrine_not_eligible"])

    assert decision.allowed is False
    assert not can_transition(DocketState.CREATED, "commit", DocketState)
    assert not can_transition(DocketState.VERIFICATION_PENDING, "commit", DocketState)


def test_acceptance_tests_use_only_tmp_path_state(tmp_path):
    repo, commit = _make_repo(tmp_path)
    ledger = MemoryAuditLedger()
    envelope = _envelope(repo, commit, tmp_path)

    execute_verification(envelope, audit_ledger=ledger, runner=_passing_runner)

    assert (tmp_path / "state" / "verifier_worktrees").exists()
    assert envelope.state_root == tmp_path / "state"
    assert verify_audit_chain(ledger.read_events())
