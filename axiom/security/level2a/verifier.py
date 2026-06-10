"""Restricted Level 2A verification engine primitives."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
from typing import Any, Protocol, Sequence

from axiom.core.orchestrator.contracts import validate_verifier_mandate_envelope
from axiom.core.orchestrator.state_machines import DocketState, MandateState
from axiom.persistence.level2a.audit_chain import compute_audit_chain_hash, compute_event_payload_hash
from axiom.persistence.level2a.interfaces import AuditLedger
from axiom.security.level2a.ast_scanner import require_ast_scan_clean
from axiom.security.level2a.validators import reject_broad_pytest_collection, require_hash_match


class VerificationFailure(ValueError):
    """Raised when verification must fail closed."""


class ProcessRunner(Protocol):
    def __call__(
        self,
        args: Sequence[str],
        *,
        cwd: str,
        env: dict[str, str],
        capture_output: bool,
        text: bool,
        timeout: int,
    ) -> subprocess.CompletedProcess[str]:
        ...


@dataclass(frozen=True)
class TrustedTestTarget:
    identifier: str
    content_sha256: str


@dataclass(frozen=True)
class VerifierMandateEnvelope:
    mandate_id: str
    docket_id: str
    source_workspace: Path
    target_commit: str
    artifact_path: Path
    authorized_artifact_sha256: str
    modified_source_paths: tuple[Path, ...]
    trusted_tests: tuple[TrustedTestTarget, ...]
    state_root: Path

    @classmethod
    def from_dict(cls, payload: dict) -> "VerifierMandateEnvelope":
        validate_verifier_mandate_envelope(payload)
        return cls(
            mandate_id=payload["mandate_id"],
            docket_id=payload["docket_id"],
            source_workspace=Path(payload["source_workspace"]),
            target_commit=payload["target_commit"],
            artifact_path=Path(payload["artifact_path"]),
            authorized_artifact_sha256=payload["authorized_artifact_sha256"],
            modified_source_paths=tuple(Path(path) for path in payload["modified_source_paths"]),
            trusted_tests=tuple(
                TrustedTestTarget(test["identifier"], test["content_sha256"]) for test in payload["trusted_tests"]
            ),
            state_root=Path(payload["state_root"]),
        )


@dataclass(frozen=True)
class VerificationResult:
    success: bool
    docket_state: DocketState
    mandate_state: MandateState
    diagnostics: tuple[str, ...]
    pytest_returncode: int | None = None


NETWORK_BLOCKED_PYTEST = r"""
import socket
import sys

class _BlockedSocket:
    def __init__(self, *args, **kwargs):
        raise RuntimeError("ERR_NETWORK_BLOCKED")

def _blocked_create_connection(*args, **kwargs):
    raise RuntimeError("ERR_NETWORK_BLOCKED")

socket.socket = _BlockedSocket
socket.create_connection = _blocked_create_connection

import pytest
raise SystemExit(pytest.main(["--noconftest", *sys.argv[1:]]))
"""


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def verify_authorized_artifact_hash(artifact_path: str | Path, authorized_artifact_sha256: str) -> bool:
    return require_hash_match(authorized_artifact_sha256, sha256_file(artifact_path))


def create_clean_git_worktree(
    *,
    source_repo: str | Path,
    target_commit: str,
    state_root: str | Path,
    name: str = "phase6_verifier",
) -> Path:
    worktree_root = Path(state_root) / "verifier_worktrees" / name
    if worktree_root.exists():
        raise VerificationFailure(f"AUDIT_FAILED: verifier worktree already exists: {worktree_root}")
    worktree_root.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["git", "-C", str(source_repo), "worktree", "add", "--detach", str(worktree_root), target_commit],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0:
        raise VerificationFailure("AUDIT_FAILED: git worktree creation failed: " + (result.stderr or result.stdout))
    return worktree_root


def verifier_python_path(state_root: str | Path) -> Path:
    root = Path(state_root)
    if os.name == "nt":
        return root / "verifier_venv" / "Scripts" / "python.exe"
    return root / "verifier_venv" / "bin" / "python"


def build_pruned_environment(
    *,
    clean_worktree: str | Path,
    state_root: str | Path,
    base_env: dict[str, str] | None = None,
) -> dict[str, str]:
    base = base_env or os.environ
    env: dict[str, str] = {}
    for key in ("PATH", "TEMP", "TMP"):
        if key in base:
            env[key] = base[key]
    env["PYTHONPATH"] = str(Path(clean_worktree))
    env["AXIOM_WORKSPACE"] = str(Path(clean_worktree))
    env["AXIOM_STATE_ROOT"] = str(Path(state_root))
    return env


def _target_path(identifier: str) -> str:
    return identifier.split("::", 1)[0].replace("\\", "/")


def verify_pinned_test_hashes(clean_worktree: str | Path, trusted_tests: Sequence[TrustedTestTarget]) -> bool:
    root = Path(clean_worktree)
    for target in trusted_tests:
        reject_broad_pytest_collection(target.identifier)
        target_file = root / _target_path(target.identifier)
        if not target_file.is_file():
            raise VerificationFailure(f"AUDIT_FAILED: pinned test file missing: {target.identifier}")
        try:
            require_hash_match(target.content_sha256, sha256_file(target_file))
        except ValueError as exc:
            raise VerificationFailure("AUDIT_FAILED:" + str(exc)) from exc
    return True


def ensure_restricted_pytest_targets(
    requested_targets: Sequence[str],
    trusted_tests: Sequence[TrustedTestTarget],
) -> bool:
    pinned = {target.identifier for target in trusted_tests}
    for target in requested_targets:
        reject_broad_pytest_collection(target)
        if target not in pinned:
            raise VerificationFailure("ERR_BROAD_COLLECTION_VIOLATION: unpinned pytest target")
    return True


def run_restricted_pytest(
    *,
    clean_worktree: str | Path,
    state_root: str | Path,
    trusted_tests: Sequence[TrustedTestTarget],
    runner: ProcessRunner = subprocess.run,
    timeout: int = 120,
) -> subprocess.CompletedProcess[str]:
    targets = [target.identifier for target in trusted_tests]
    ensure_restricted_pytest_targets(targets, trusted_tests)
    command = [str(verifier_python_path(state_root)), "-c", NETWORK_BLOCKED_PYTEST, *targets]
    return runner(
        command,
        cwd=str(Path(clean_worktree)),
        env=build_pruned_environment(clean_worktree=clean_worktree, state_root=state_root),
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def transition_success() -> tuple[DocketState, MandateState]:
    return DocketState.VERIFIED_COMMIT, MandateState.COMPLETED


def transition_failure() -> tuple[DocketState, MandateState]:
    return DocketState.FAILED, MandateState.AUDIT_FAILED


def _append_chained_event(
    audit_ledger: AuditLedger,
    *,
    event_type: str,
    mandate_id: str,
    docket_id: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    event: dict[str, Any] = {
        "event_type": event_type,
        "mandate_id": mandate_id,
        "docket_id": docket_id,
    }
    if payload:
        event["payload"] = payload
    prior_events = audit_ledger.read_events()
    prior_hash = prior_events[-1]["audit_chain_hash"] if prior_events else None
    payload_hash = compute_event_payload_hash(event)
    if prior_hash is not None:
        event["prior_audit_hash"] = prior_hash
    event["event_payload_sha256"] = payload_hash
    event["audit_chain_hash"] = compute_audit_chain_hash(payload_hash, prior_hash)
    audit_ledger.append_event(event)
    return event


def execute_verification(
    envelope: VerifierMandateEnvelope,
    *,
    audit_ledger: AuditLedger,
    runner: ProcessRunner = subprocess.run,
) -> VerificationResult:
    diagnostics: list[str] = []
    worktree: Path | None = None
    try:
        verify_authorized_artifact_hash(envelope.artifact_path, envelope.authorized_artifact_sha256)
        _append_chained_event(
            audit_ledger,
            event_type="artifact_hash_validated",
            mandate_id=envelope.mandate_id,
            docket_id=envelope.docket_id,
            payload={
                "artifact_path": str(envelope.artifact_path),
                "authorized_artifact_sha256": envelope.authorized_artifact_sha256,
            },
        )

        worktree = create_clean_git_worktree(
            source_repo=envelope.source_workspace,
            target_commit=envelope.target_commit,
            state_root=envelope.state_root,
            name=envelope.docket_id.replace("-", "_"),
        )
        _append_chained_event(
            audit_ledger,
            event_type="worktree_created",
            mandate_id=envelope.mandate_id,
            docket_id=envelope.docket_id,
            payload={"worktree": str(worktree), "target_commit": envelope.target_commit},
        )
        scan_targets = [worktree / path for path in envelope.modified_source_paths]
        try:
            require_ast_scan_clean(scan_targets)
        except Exception as exc:
            _append_chained_event(
                audit_ledger,
                event_type="ast_scan_failed",
                mandate_id=envelope.mandate_id,
                docket_id=envelope.docket_id,
                payload={"error": str(exc), "source_count": len(scan_targets)},
            )
            raise
        _append_chained_event(
            audit_ledger,
            event_type="ast_scan_completed",
            mandate_id=envelope.mandate_id,
            docket_id=envelope.docket_id,
            payload={"source_count": len(scan_targets)},
        )
        verify_pinned_test_hashes(worktree, envelope.trusted_tests)
        _append_chained_event(
            audit_ledger,
            event_type="pinned_tests_validated",
            mandate_id=envelope.mandate_id,
            docket_id=envelope.docket_id,
            payload={"target_count": len(envelope.trusted_tests)},
        )

        pytest_result = run_restricted_pytest(
            clean_worktree=worktree,
            state_root=envelope.state_root,
            trusted_tests=envelope.trusted_tests,
            runner=runner,
        )
        _append_chained_event(
            audit_ledger,
            event_type="pytest_completed",
            mandate_id=envelope.mandate_id,
            docket_id=envelope.docket_id,
            payload={"returncode": pytest_result.returncode},
        )
        if pytest_result.returncode != 0:
            raise VerificationFailure("AUDIT_FAILED: pytest verification failed")

        docket_state, mandate_state = transition_success()
        _append_chained_event(
            audit_ledger,
            event_type="verified_commit_recorded",
            mandate_id=envelope.mandate_id,
            docket_id=envelope.docket_id,
            payload={"docket_state": docket_state.value, "mandate_state": mandate_state.value},
        )
        return VerificationResult(True, docket_state, mandate_state, tuple(diagnostics), pytest_result.returncode)
    except Exception as exc:
        diagnostics.append(str(exc))
        docket_state, mandate_state = transition_failure()
        _append_chained_event(
            audit_ledger,
            event_type="audit_failed",
            mandate_id=envelope.mandate_id,
            docket_id=envelope.docket_id,
            payload={"error": str(exc), "docket_state": docket_state.value, "mandate_state": mandate_state.value},
        )
        return VerificationResult(False, docket_state, mandate_state, tuple(diagnostics), None)
    finally:
        if worktree is not None and worktree.exists():
            shutil.rmtree(worktree, ignore_errors=True)
