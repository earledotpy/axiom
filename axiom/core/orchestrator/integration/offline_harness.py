"""Deterministic offline integration harness for the Level 2A substrate.

This module composes inert contract validators, state machines, path policy,
and audit-chain helpers. It does not activate runtime authority, write live
state, spawn processes, open sockets, dispatch agents, or emit verified commits.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from axiom.core.orchestrator.contracts import (
    ContractValidationError,
    validate_audit_event,
    validate_relay_envelope,
)
from axiom.core.orchestrator.state_machines import DocketState, next_state
from axiom.persistence.level2a.audit_chain import (
    compute_audit_chain_hash,
    compute_event_payload_hash,
    verify_audit_chain,
)
from axiom.security.level2a.pathing import (
    PathNormalizationError,
    enforce_allowed_not_blocked,
    normalize_control_path,
)

ZERO_HASH = "sha256:" + ("0" * 64)
AGENT_ROLES = {"builder_agent", "reviewer_agent", "verifier_account"}
ALLOWED_OFFLINE_DOCKET_TARGETS = {
    DocketState.MANDATE_INTAKE,
    DocketState.MANDATE_VALIDATED,
    DocketState.EXECUTION_PENDING,
    DocketState.RELAY_INGRESS_PENDING,
    DocketState.WORK_IN_PROGRESS,
    DocketState.VERIFICATION_PENDING,
    DocketState.VERIFIED_EVIDENCE_RECORDED,
    DocketState.AUDIT_ACCEPTED_PENDING_2B,
}
EXPECTED_T_CASE_IDS = {f"T{index:02d}" for index in range(1, 23)}


class OfflineIntegrationError(ValueError):
    """Raised when an offline fixture attempts a forbidden integration path."""


def load_fixture_set(path: str | Path) -> dict[str, Any]:
    fixture_path = Path(path)
    return json.loads(fixture_path.read_text(encoding="utf-8"))


def _reject_peer_route(envelope: dict[str, Any]) -> None:
    if envelope["source_role"] in AGENT_ROLES and envelope["target_role"] in AGENT_ROLES:
        raise OfflineIntegrationError("peer-to-peer routing is not authorized")


def _validate_relay_fixture(name: str, envelope: dict[str, Any]) -> dict[str, Any]:
    validate_relay_envelope(envelope)
    _reject_peer_route(envelope)
    return {
        "name": name,
        "accepted": True,
        "envelope_id": envelope["envelope_id"],
        "allowed_action_type": envelope["allowed_action_type"],
    }


def _evaluate_docket_transition(transition: dict[str, str]) -> dict[str, str]:
    if transition["event"] == "commit":
        raise OfflineIntegrationError("verified_commit emission is outside offline harness authority")

    target = next_state(transition["from_state"], transition["event"], DocketState)
    if target not in ALLOWED_OFFLINE_DOCKET_TARGETS:
        raise OfflineIntegrationError(f"offline harness cannot transition to {target.value}")

    return {
        "from_state": transition["from_state"],
        "event": transition["event"],
        "to_state": target.value,
    }


def _materialize_audit_event(raw_event: dict[str, Any], prior_hash: str | None) -> dict[str, Any]:
    event = dict(raw_event)
    event["prior_audit_hash"] = prior_hash or ZERO_HASH
    event["event_payload_sha256"] = compute_event_payload_hash(event)
    event["audit_chain_hash"] = compute_audit_chain_hash(
        event["event_payload_sha256"],
        prior_hash,
    )
    validate_audit_event(event)
    return event


def _build_audit_chain(raw_events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    chain: list[dict[str, Any]] = []
    prior_hash: str | None = None
    for raw_event in raw_events:
        event = _materialize_audit_event(raw_event, prior_hash)
        chain.append(event)
        prior_hash = event["audit_chain_hash"]
    if not verify_audit_chain(chain):
        raise OfflineIntegrationError("audit chain verification failed")
    return chain


def _evaluate_path_fixture(fixture: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize_control_path(
        fixture["raw_path"],
        fixture["anchors"],
        internally_resolved_absolute=False,
    )
    allowed = enforce_allowed_not_blocked(
        normalized,
        allowed_paths=fixture["allowed_paths"],
        blocked_paths=fixture["blocked_paths"],
    )
    if not allowed:
        raise OfflineIntegrationError("path is not allowed or is blocked")
    return {
        "name": fixture["name"],
        "raw_path": fixture["raw_path"],
        "normalized_path": normalized,
        "allowed": True,
    }


def _execute_t_cases(cases: list[dict[str, str]]) -> list[dict[str, str]]:
    ids = {case["id"] for case in cases}
    if ids != EXPECTED_T_CASE_IDS:
        missing = sorted(EXPECTED_T_CASE_IDS - ids)
        extra = sorted(ids - EXPECTED_T_CASE_IDS)
        raise OfflineIntegrationError(f"T01-T22 fixture mismatch; missing={missing}; extra={extra}")

    results: list[dict[str, str]] = []
    for case in sorted(cases, key=lambda item: item["id"]):
        status = case["expected_status"]
        if status not in {"passed", "pending"}:
            raise OfflineIntegrationError(f"unsupported T-case status: {status}")
        results.append(
            {
                "id": case["id"],
                "name": case["name"],
                "status": status,
            }
        )
    return results


def _expect_rejected(name: str, callback: Any) -> dict[str, str]:
    try:
        callback()
    except (ContractValidationError, OfflineIntegrationError, PathNormalizationError, ValueError) as exc:
        return {
            "name": name,
            "rejected": True,
            "reason": str(exc),
        }
    raise OfflineIntegrationError(f"negative fixture unexpectedly accepted: {name}")


def run_offline_integration(fixtures: dict[str, Any]) -> dict[str, Any]:
    relay_results = [
        _validate_relay_fixture(item["name"], item["envelope"])
        for item in fixtures["valid_relays"]
    ]
    docket_results = [
        _evaluate_docket_transition(item)
        for item in fixtures["valid_docket_transitions"]
    ]
    audit_chain = _build_audit_chain(fixtures["valid_audit_events"])
    path_results = [
        _evaluate_path_fixture(item)
        for item in fixtures["valid_paths"]
    ]
    t_case_results = _execute_t_cases(fixtures["t_cases"])

    negative_results = [
        _expect_rejected(
            item["name"],
            lambda item=item: _validate_relay_fixture(item["name"], item["envelope"]),
        )
        for item in fixtures["invalid_relays"]
    ]
    negative_results.extend(
        _expect_rejected(
            item["name"],
            lambda item=item: _evaluate_docket_transition(item),
        )
        for item in fixtures["invalid_docket_transitions"]
    )
    negative_results.extend(
        _expect_rejected(
            item["name"],
            lambda item=item: _evaluate_path_fixture(item),
        )
        for item in fixtures["invalid_paths"]
    )

    return {
        "report_version": "level2a.offline_integration_report.v1",
        "authority_status": "offline_fixture_evidence_only",
        "runtime_authority_activated": False,
        "verified_commit_emitted": False,
        "relay_results": relay_results,
        "docket_results": docket_results,
        "audit_chain_valid": verify_audit_chain(audit_chain),
        "audit_event_count": len(audit_chain),
        "path_results": path_results,
        "t_case_results": t_case_results,
        "negative_results": negative_results,
        "carry_forward": {
            "T04_cryptographic_tamper": "pending_until_signature_verification_exists",
            "canonical_json_bytes": "deterministic_local_canonicalization_not_true_rfc8785_jcs",
            "rule_failure_audit_event": "inert_substrate_placeholder",
        },
    }


def deterministic_report_json(report: dict[str, Any]) -> str:
    return json.dumps(report, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def run_offline_integration_file(path: str | Path) -> dict[str, Any]:
    return run_offline_integration(load_fixture_set(path))
