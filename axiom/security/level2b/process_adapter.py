"""Dry-run multi-principal process execution planning for Level 2B."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Sequence


class PrincipalRole(str, Enum):
    BUILDER = "builder"
    REVIEWER = "reviewer"
    VERIFIER = "verifier"


PRINCIPAL_ACCOUNTS = {
    PrincipalRole.BUILDER: "axiom_builder",
    PrincipalRole.REVIEWER: "axiom_reviewer",
    PrincipalRole.VERIFIER: "axiom_verifier",
}


class ProcessAdapterError(ValueError):
    """Raised when a Level 2B process plan must fail closed."""


@dataclass(frozen=True)
class AclAssertion:
    path: Path
    account: str
    can_read: bool
    can_write: bool


@dataclass(frozen=True)
class ProcessExecutionRequest:
    role: PrincipalRole
    command: tuple[str, ...]
    workspace: Path
    impersonation_token: str | None = None
    acl_assertions: tuple[AclAssertion, ...] = ()


@dataclass(frozen=True)
class ProcessExecutionPlan:
    account: str
    command: tuple[str, ...]
    workspace: Path
    dry_run: bool = True


def _coerce_role(role: PrincipalRole | str) -> PrincipalRole:
    if isinstance(role, PrincipalRole):
        return role
    try:
        return PrincipalRole(role)
    except ValueError as exc:
        raise ProcessAdapterError(f"ERR_UNKNOWN_PRINCIPAL_ROLE:{role}") from exc


def account_for_role(role: PrincipalRole | str) -> str:
    return PRINCIPAL_ACCOUNTS[_coerce_role(role)]


def assert_acl_boundaries(assertions: Sequence[AclAssertion], *, account: str) -> bool:
    if not assertions:
        raise ProcessAdapterError("ERR_ACL_ASSERTIONS_REQUIRED")
    for assertion in assertions:
        if assertion.account != account:
            raise ProcessAdapterError("ERR_ACL_ACCOUNT_MISMATCH")
        if not assertion.can_read:
            raise ProcessAdapterError("ERR_ACL_READ_REQUIRED")
    return True


def build_execution_plan(request: ProcessExecutionRequest) -> ProcessExecutionPlan:
    if not request.command:
        raise ProcessAdapterError("ERR_COMMAND_REQUIRED")
    account = account_for_role(request.role)
    if not request.impersonation_token:
        raise ProcessAdapterError("ERR_IMPERSONATION_TOKEN_REQUIRED")
    assert_acl_boundaries(request.acl_assertions, account=account)
    return ProcessExecutionPlan(
        account=account,
        command=tuple(request.command),
        workspace=Path(request.workspace),
    )
