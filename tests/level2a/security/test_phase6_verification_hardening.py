from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from axiom.core.orchestrator.contracts import ContractValidationError, validate_verifier_mandate_envelope
from axiom.core.orchestrator.state_machines import DocketState, MandateState
from axiom.persistence.level2a.audit_chain import verify_audit_chain
from axiom.security.level2a.ast_scanner import AstScanViolation, require_ast_scan_clean, scan_python_source
from axiom.security.level2a.validators import reject_broad_pytest_collection
from axiom.security.level2a.verifier import (
    TrustedTestTarget,
    VerifierMandateEnvelope,
    build_pruned_environment,
    create_clean_git_worktree,
    ensure_restricted_pytest_targets,
    execute_verification,
    run_restricted_pytest,
    sha256_file,
    transition_failure,
    transition_success,
    verifier_python_path,
    verify_authorized_artifact_hash,
    verify_pinned_test_hashes,
)


class MemoryAuditLedger:
    def __init__(self) -> None:
        self.events = []

    def append_event(self, event: dict) -> None:
        self.events.append(event)

    def read_events(self) -> list[dict]:
        return list(self.events)


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True)


def _make_repo(tmp_path: Path) -> tuple[Path, str]:
    repo = tmp_path / "repo"
    (repo / "axiom" / "module").mkdir(parents=True)
    (repo / "tests" / "level2a" / "security").mkdir(parents=True)
    subprocess.run(["git", "init", str(repo)], check=True, capture_output=True, text=True)
    _git(repo, "config", "user.email", "phase6@example.invalid")
    _git(repo, "config", "user.name", "Phase 6 Test")
    (repo / "axiom" / "module" / "safe.py").write_text("VALUE = 1\n", encoding="utf-8")
    (repo / "tests" / "level2a" / "security" / "test_phase6_verification_hardening.py").write_text(
        "def test_safe():\n    assert True\n",
        encoding="utf-8",
    )
    (repo / "artifact.txt").write_text("authorized artifact\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "seed verifier fixture")
    commit = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], check=True, capture_output=True, text=True)
    return repo, commit.stdout.strip()


def _trusted_test(root: Path) -> TrustedTestTarget:
    identifier = "tests/level2a/security/test_phase6_verification_hardening.py"
    return TrustedTestTarget(identifier, sha256_file(root / identifier))


def test_verifier_matches_and_rejects_authorized_artifact_hash(tmp_path):
    artifact = tmp_path / "artifact.txt"
    artifact.write_text("verified payload\n", encoding="utf-8")
    expected = sha256_file(artifact)

    assert verify_authorized_artifact_hash(artifact, expected)
    with pytest.raises(ValueError, match="ERR_HASH_MISMATCH"):
        verify_authorized_artifact_hash(artifact, "sha256:" + "0" * 64)


def test_verifier_creates_clean_git_worktree_in_test_isolated_location(tmp_path):
    repo, commit = _make_repo(tmp_path)
    state_root = tmp_path / "state"

    worktree = create_clean_git_worktree(source_repo=repo, target_commit=commit, state_root=state_root)

    assert worktree.is_dir()
    assert (worktree / ".git").exists()
    assert str(worktree).startswith(str(state_root))
    assert (worktree / "artifact.txt").read_text(encoding="utf-8") == "authorized artifact\n"


@pytest.mark.parametrize(
    "source",
    [
        "eval('1 + 1')",
        "exec('x = 1')",
        "import subprocess\n",
        "import socket\n",
        "__import__('os')",
    ],
)
def test_ast_scanner_detects_blocked_constructs(source):
    findings = scan_python_source(source)
    assert findings


def test_ast_scanner_rejects_blocked_file_before_execution(tmp_path):
    source = tmp_path / "blocked.py"
    source.write_text("import socket\n", encoding="utf-8")

    with pytest.raises(AstScanViolation, match="AUDIT_FAILED"):
        require_ast_scan_clean([source])


def test_verifier_rejects_mismatched_pinned_test_hash(tmp_path):
    clean_worktree = tmp_path / "worktree"
    test_file = clean_worktree / "tests" / "level2a" / "security" / "test_phase6_verification_hardening.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("def test_safe():\n    assert True\n", encoding="utf-8")
    trusted = TrustedTestTarget("tests/level2a/security/test_phase6_verification_hardening.py", "sha256:" + "1" * 64)

    with pytest.raises(ValueError, match="ERR_HASH_MISMATCH|AUDIT_FAILED"):
        verify_pinned_test_hashes(clean_worktree, [trusted])


def test_pinned_file_targets_are_allowed_but_broad_collection_is_blocked():
    assert reject_broad_pytest_collection("tests/level2a/security/test_phase6_verification_hardening.py")
    assert reject_broad_pytest_collection(
        "tests/level2a/security/test_phase6_verification_hardening.py::test_pinned_file_targets_are_allowed_but_broad_collection_is_blocked"
    )
    for target in ("tests/", "tests/level2a/", "tests/level2a/security/", "tests/**/*.py", "pytest"):
        with pytest.raises(ValueError, match="ERR_BROAD_COLLECTION_VIOLATION"):
            reject_broad_pytest_collection(target)


def test_pytest_collection_fails_for_unpinned_targets_or_unexpected_files(tmp_path):
    trusted = [TrustedTestTarget("tests/level2a/security/test_phase6_verification_hardening.py", "sha256:" + "2" * 64)]

    with pytest.raises(ValueError, match="ERR_BROAD_COLLECTION_VIOLATION"):
        ensure_restricted_pytest_targets(["tests/level2a/"], trusted)
    with pytest.raises(ValueError, match="ERR_BROAD_COLLECTION_VIOLATION"):
        ensure_restricted_pytest_targets(["tests/level2a/security/test_unpinned.py"], trusted)


def test_test_runner_uses_pruned_environment_and_socket_blocking_wrapper(tmp_path):
    clean_worktree = tmp_path / "worktree"
    state_root = tmp_path / "state"
    clean_worktree.mkdir()
    expected_python = verifier_python_path(state_root)
    trusted = [TrustedTestTarget("tests/level2a/security/test_phase6_verification_hardening.py", "sha256:" + "3" * 64)]
    observed = {}

    def fake_runner(args, *, cwd, env, capture_output, text, timeout):
        observed["args"] = list(args)
        observed["cwd"] = cwd
        observed["env"] = dict(env)
        return subprocess.CompletedProcess(args, 0, stdout="ok", stderr="")

    result = run_restricted_pytest(
        clean_worktree=clean_worktree,
        state_root=state_root,
        trusted_tests=trusted,
        runner=fake_runner,
    )

    assert result.returncode == 0
    assert observed["args"][0] == str(expected_python)
    assert "--noconftest" in observed["args"][2]
    assert "ERR_NETWORK_BLOCKED" in observed["args"][2]
    assert set(observed["env"]) <= {"PATH", "PYTHONPATH", "AXIOM_WORKSPACE", "AXIOM_STATE_ROOT", "TEMP", "TMP"}
    assert observed["env"]["PYTHONPATH"] == str(clean_worktree)
    assert observed["env"]["AXIOM_STATE_ROOT"] == str(state_root)


def test_pruned_environment_strips_credentials_and_external_configuration(tmp_path):
    env = build_pruned_environment(
        clean_worktree=tmp_path / "worktree",
        state_root=tmp_path / "state",
        base_env={
            "PATH": os.environ.get("PATH", ""),
            "OPENAI_API_KEY": "secret",
            "ANTHROPIC_API_KEY": "secret",
            "AXIOM_DB_PATH": "production.db",
            "TEMP": str(tmp_path / "temp"),
        },
    )

    assert "OPENAI_API_KEY" not in env
    assert "ANTHROPIC_API_KEY" not in env
    assert "AXIOM_DB_PATH" not in env
    assert env["PYTHONPATH"] == str(tmp_path / "worktree")


def test_successful_verification_transitions_to_verified_commit_and_completed(tmp_path):
    repo, commit = _make_repo(tmp_path)
    ledger = MemoryAuditLedger()
    state_root = tmp_path / "state"
    envelope = VerifierMandateEnvelope(
        mandate_id="MND-ACCEPTED-2026-0009",
        docket_id="DK-2026-0009",
        source_workspace=repo,
        target_commit=commit,
        artifact_path=repo / "artifact.txt",
        authorized_artifact_sha256=sha256_file(repo / "artifact.txt"),
        modified_source_paths=(Path("axiom/module/safe.py"),),
        trusted_tests=(_trusted_test(repo),),
        state_root=state_root,
    )

    def fake_runner(args, *, cwd, env, capture_output, text, timeout):
        return subprocess.CompletedProcess(args, 0, stdout="passed", stderr="")

    result = execute_verification(envelope, audit_ledger=ledger, runner=fake_runner)

    assert result.success is True
    assert result.docket_state is DocketState.VERIFIED_COMMIT
    assert result.mandate_state is MandateState.COMPLETED
    assert [event["event_type"] for event in ledger.events] == [
        "artifact_hash_validated",
        "worktree_created",
        "ast_scan_completed",
        "pinned_tests_validated",
        "pytest_completed",
        "verified_commit_recorded",
    ]
    assert verify_audit_chain(ledger.events)


def test_verification_failure_transitions_to_failed_and_audit_failed(tmp_path):
    repo, commit = _make_repo(tmp_path)
    ledger = MemoryAuditLedger()
    envelope = VerifierMandateEnvelope(
        mandate_id="MND-ACCEPTED-2026-0009",
        docket_id="DK-2026-0009",
        source_workspace=repo,
        target_commit=commit,
        artifact_path=repo / "artifact.txt",
        authorized_artifact_sha256="sha256:" + "0" * 64,
        modified_source_paths=(Path("axiom/module/safe.py"),),
        trusted_tests=(_trusted_test(repo),),
        state_root=tmp_path / "state",
    )

    result = execute_verification(envelope, audit_ledger=ledger)

    assert result.success is False
    assert result.docket_state is DocketState.FAILED
    assert result.mandate_state is MandateState.AUDIT_FAILED
    assert ledger.events[-1]["event_type"] == "audit_failed"


def test_transition_helpers_preserve_phase6_terminal_mapping():
    assert transition_success() == (DocketState.VERIFIED_COMMIT, MandateState.COMPLETED)
    assert transition_failure() == (DocketState.FAILED, MandateState.AUDIT_FAILED)


def test_verifier_mandate_envelope_contract_accepts_file_path_test_pins(tmp_path):
    payload = {
        "verifier_envelope_version": "2A.P6.1",
        "mandate_id": "MND-ACCEPTED-2026-0009",
        "docket_id": "DK-2026-0009",
        "source_workspace": str(tmp_path / "repo"),
        "target_commit": "HEAD",
        "artifact_path": "artifact.txt",
        "authorized_artifact_sha256": "sha256:" + "a" * 64,
        "modified_source_paths": ["axiom/module/safe.py"],
        "trusted_tests": [
            {
                "identifier": "tests/level2a/security/test_phase6_verification_hardening.py",
                "content_sha256": "sha256:" + "b" * 64,
            }
        ],
        "state_root": str(tmp_path / "state"),
    }

    assert validate_verifier_mandate_envelope(payload)
    assert VerifierMandateEnvelope.from_dict(payload).mandate_id == "MND-ACCEPTED-2026-0009"

    payload["trusted_tests"] = [{"identifier": "tests/level2a/", "content_sha256": "sha256:" + "b" * 64}]
    with pytest.raises(ContractValidationError, match="ERR_BROAD_COLLECTION_VIOLATION"):
        validate_verifier_mandate_envelope(payload)
