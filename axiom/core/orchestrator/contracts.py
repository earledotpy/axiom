"""Level 2A schema-like contract validators.

These validators are inert: they validate in-memory dictionaries and strings
without persistence, subprocess execution, model calls, network calls, or
runtime Orchestrator activation.
"""

from __future__ import annotations

from enum import Enum
import re
from typing import Any

from axiom.security.level2a.validators import (
    reject_broad_pytest_collection,
    validate_sha256_hash,
    validate_utc_timestamp,
)


ID_PATTERNS: dict[str, re.Pattern[str]] = {
    "mandate_artifact": re.compile(r"^MND-(ACCEPTED|CANDIDATE)-\d{4}-\d{4}(-[A-Z0-9]+)*$"),
    "mandate_short": re.compile(r"^MND-(ACCEPTED|CANDIDATE)-\d{4}-\d{4}$"),
    "docket": re.compile(r"^DK-\d{4}-\d{4}$"),
    "relay_envelope": re.compile(r"^ENV-[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"),
    "audit_event": re.compile(r"^AUD-[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"),
    "schema": re.compile(r"^SCH-[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"),
    "evidence": re.compile(r"^EVI-[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"),
    "dead_letter": re.compile(r"^DL-[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"),
    "nonce": re.compile(r"^nonce_v1_[0-9a-f]{64}$"),
}


class RejectionCode(str, Enum):
    MALFORMED_INPUT = "ERR_MALFORMED_INPUT"
    INVALID_SCHEMA = "ERR_INVALID_SCHEMA"
    CANONICALIZATION_FAILED = "ERR_CANONICALIZATION_FAILED"
    SIGNATURE_INVALID = "ERR_SIGNATURE_INVALID"
    MANDATE_EXPIRED = "ERR_MANDATE_EXPIRED"
    MANDATE_REVOKED = "ERR_MANDATE_REVOKED"
    NONCE_REPLAY = "ERR_NONCE_REPLAY"
    SCOPE_VIOLATION = "ERR_SCOPE_VIOLATION"
    BLOCKED_PATH_VIOLATION = "ERR_BLOCKED_PATH_VIOLATION"
    HASH_MISMATCH = "ERR_HASH_MISMATCH"
    RELAY_BLOCKED_ACTION = "ERR_RELAY_BLOCKED_ACTION"
    VERIFIER_HANDOFF_VIOLATION = "ERR_VERIFIER_HANDOFF_VIOLATION"
    BROAD_COLLECTION_VIOLATION = "ERR_BROAD_COLLECTION_VIOLATION"
    POSTURE_CACHE_AUTHORITY = "ERR_POSTURE_CACHE_AUTHORITY"
    AUDIT_CHAIN_VIOLATION = "ERR_AUDIT_CHAIN_VIOLATION"


class AuditActor(str, Enum):
    ORCHESTRATOR_CORE = "orchestrator_core"
    OPERATOR_CONSOLE = "operator_console"
    VERIFIER_ACCOUNT = "verifier_account"
    AUDIT_SUBSYSTEM = "audit_subsystem"
    DEAD_LETTER_SUBSYSTEM = "dead_letter_subsystem"


class RelaySourceRole(str, Enum):
    OPERATOR_CONSOLE = "operator_console"
    ORCHESTRATOR = "orchestrator"
    BUILDER_AGENT = "builder_agent"
    REVIEWER_AGENT = "reviewer_agent"
    VERIFIER_ACCOUNT = "verifier_account"
    AUDIT_SUBSYSTEM = "audit_subsystem"
    DEAD_LETTER_SUBSYSTEM = "dead_letter_subsystem"
    WEB_CHAT_ADVISORY_SURFACE = "web_chat_advisory_surface"


class RelayTargetRole(str, Enum):
    ORCHESTRATOR = "orchestrator"
    OPERATOR_CONSOLE = "operator_console"
    BUILDER_AGENT = "builder_agent"
    REVIEWER_AGENT = "reviewer_agent"
    VERIFIER_ACCOUNT = "verifier_account"
    AUDIT_SUBSYSTEM = "audit_subsystem"
    DEAD_LETTER_SUBSYSTEM = "dead_letter_subsystem"


class BlockedActionIndicator(str, Enum):
    SHELL_COMMAND_FRAME = "shell_command_frame"
    RAW_PROMPT_TO_AGENT_EXECUTION_FRAME = "raw_prompt_to_agent_execution_frame"
    PEER_TO_PEER_AGENT_ROUTING_FRAME = "peer_to_peer_agent_routing_frame"
    RECURSIVE_AGENT_LOOP_FRAME = "recursive_agent_loop_frame"
    UNSIGNED_AUTHORIZATION_FRAME = "unsigned_authorization_frame"
    CONSOLE_EXECUTION_FRAME = "console_execution_frame"
    RUNTIME_MUTATION_FRAME = "runtime_mutation_frame"
    LIVE_SPINE_MUTATION_FRAME = "live_spine_mutation_frame"
    IPC_REACTIVATION_FRAME = "ipc_reactivation_frame"
    MODEL_INVOCATION_FRAME = "model_invocation_frame"
    NETWORK_CALL_FRAME = "network_call_frame"
    UNSCOPED_FILESYSTEM_WRITE_FRAME = "unscoped_filesystem_write_frame"
    BROAD_TEST_COLLECTION_FRAME = "broad_test_collection_frame"
    VERIFIER_BYPASS_FRAME = "verifier_bypass_frame"
    VERIFIED_COMMIT_CLAIM_FRAME = "verified_commit_claim_frame"
    DOCTRINE_CHANGE_FRAME = "doctrine_change_frame"


RELAY_ARTIFACT_TYPES = frozenset(
    {
        "review_request",
        "architecture_artifact",
        "mandate_candidate",
        "accepted_mandate",
        "patch_artifact",
        "verification_report",
        "audit_event",
        "operator_summary_event",
        "dead_letter_event",
        "definition_package",
        "schema_appendix",
        "test_matrix",
    }
)

ALLOWED_ACTION_TYPES = frozenset(
    {
        "present_for_review",
        "record_artifact",
        "route_for_review",
        "route_for_definition_drafting",
        "request_operator_signature",
        "record_audit_event",
        "record_dead_letter",
        "record_verification_report",
        "record_operator_summary",
    }
)

AUDIT_EVENT_TYPES = frozenset(
    {
        "mandate_received",
        "mandate_signature_validated",
        "mandate_signature_rejected",
        "mandate_expired",
        "mandate_revoked",
        "mandate_nonce_consumed",
        "mandate_replay_rejected",
        "mandate_scope_validated",
        "mandate_scope_rejected",
        "blocked_path_rejected",
        "artifact_hash_validated",
        "artifact_hash_rejected",
        "relay_envelope_received",
        "relay_envelope_validated",
        "relay_envelope_rejected",
        "docket_state_transitioned",
        "console_approval_requested",
        "console_approval_recorded",
        "console_approval_rejected",
        "verifier_handoff_requested",
        "verifier_handoff_rejected",
        "verifier_evidence_recorded",
        "verified_commit_recorded",
        "audit_failed",
        "audit_chain_mutation_detected",
        "dead_letter_recorded",
        "operator_summary_recorded",
    }
)


class ContractValidationError(ValueError):
    """Raised when an inert Level 2A contract fails validation."""


def validate_id(kind: str, value: str) -> bool:
    pattern = ID_PATTERNS[kind]
    return bool(pattern.fullmatch(value))


def _require_exact_fields(payload: dict[str, Any], required: set[str], optional: set[str] | None = None) -> None:
    optional = optional or set()
    unknown = set(payload) - required - optional
    missing = required - set(payload)
    if unknown:
        raise ContractValidationError(f"unknown fields: {sorted(unknown)}")
    if missing:
        raise ContractValidationError(f"missing fields: {sorted(missing)}")
    for field in required:
        if payload[field] is None:
            raise ContractValidationError(f"null required field: {field}")


def _expect_member(enum_type: type[Enum], value: str, field: str) -> None:
    if value not in {item.value for item in enum_type}:
        raise ContractValidationError(f"invalid {field}: {value}")


def validate_relay_envelope(envelope: dict[str, Any]) -> bool:
    required = {
        "relay_envelope_version",
        "envelope_id",
        "docket_id",
        "mandate_id",
        "source_role",
        "target_role",
        "artifact_type",
        "artifact_ref",
        "artifact_sha256",
        "allowed_action_type",
        "blocked_action_indicators",
        "created_at",
        "nonce",
        "canonicalization",
        "schema_hash",
    }
    _require_exact_fields(envelope, required, {"signature_ref"})

    if envelope["relay_envelope_version"] != "2A.1":
        raise ContractValidationError("invalid relay_envelope_version")
    if not validate_id("relay_envelope", envelope["envelope_id"]):
        raise ContractValidationError("invalid envelope_id")
    if not validate_id("docket", envelope["docket_id"]):
        raise ContractValidationError("invalid docket_id")
    if not validate_id("mandate_artifact", envelope["mandate_id"]):
        raise ContractValidationError("invalid mandate_id")
    _expect_member(RelaySourceRole, envelope["source_role"], "source_role")
    _expect_member(RelayTargetRole, envelope["target_role"], "target_role")
    if envelope["artifact_type"] not in RELAY_ARTIFACT_TYPES:
        raise ContractValidationError("invalid artifact_type")
    if envelope["allowed_action_type"] not in ALLOWED_ACTION_TYPES:
        raise ContractValidationError("invalid allowed_action_type")
    if not validate_sha256_hash(envelope["artifact_sha256"]):
        raise ContractValidationError("invalid artifact_sha256")
    if not validate_sha256_hash(envelope["schema_hash"]):
        raise ContractValidationError("invalid schema_hash")
    if not validate_utc_timestamp(envelope["created_at"]):
        raise ContractValidationError("invalid created_at")
    if not validate_id("nonce", envelope["nonce"]):
        raise ContractValidationError("invalid nonce")
    if envelope["canonicalization"] != "RFC8785":
        raise ContractValidationError("invalid canonicalization")
    if not isinstance(envelope["blocked_action_indicators"], list):
        raise ContractValidationError("blocked_action_indicators must be list")
    blocked_values = {item.value for item in BlockedActionIndicator}
    if any(item not in blocked_values for item in envelope["blocked_action_indicators"]):
        raise ContractValidationError("invalid blocked action indicator")
    if envelope["blocked_action_indicators"]:
        raise ContractValidationError(RejectionCode.RELAY_BLOCKED_ACTION.value)
    return True


def validate_audit_event(event: dict[str, Any]) -> bool:
    required = {
        "audit_event_version",
        "event_id",
        "event_type",
        "actor",
        "event_time",
        "prior_audit_hash",
        "event_payload_sha256",
        "audit_chain_hash",
        "canonicalization",
    }
    optional = {"docket_id", "mandate_id", "attempted_actor", "input_hashes", "output_hashes"}
    _require_exact_fields(event, required, optional)
    if event["audit_event_version"] != "2A.1":
        raise ContractValidationError("invalid audit_event_version")
    if not validate_id("audit_event", event["event_id"]):
        raise ContractValidationError("invalid event_id")
    if event["event_type"] not in AUDIT_EVENT_TYPES:
        raise ContractValidationError("invalid event_type")
    _expect_member(AuditActor, event["actor"], "actor")
    if "docket_id" in event and not validate_id("docket", event["docket_id"]):
        raise ContractValidationError("invalid docket_id")
    if "mandate_id" in event and not validate_id("mandate_artifact", event["mandate_id"]):
        raise ContractValidationError("invalid mandate_id")
    if not validate_utc_timestamp(event["event_time"]):
        raise ContractValidationError("invalid event_time")
    for field in ("prior_audit_hash", "event_payload_sha256", "audit_chain_hash"):
        if not validate_sha256_hash(event[field]):
            raise ContractValidationError(f"invalid {field}")
    for field in ("input_hashes", "output_hashes"):
        if field in event and any(not validate_sha256_hash(item) for item in event[field]):
            raise ContractValidationError(f"invalid {field}")
    if event["canonicalization"] != "RFC8785":
        raise ContractValidationError("invalid canonicalization")
    return True


def validate_dead_letter_record(record: dict[str, Any]) -> bool:
    required = {"dead_letter_id", "rejection_code", "failure_reason", "raw_payload", "actor", "received_at"}
    optional = {"original_envelope_id", "mandate_id", "docket_id", "attempted_actor"}
    _require_exact_fields(record, required, optional)
    if not validate_id("dead_letter", record["dead_letter_id"]):
        raise ContractValidationError("invalid dead_letter_id")
    if "original_envelope_id" in record and record["original_envelope_id"]:
        if not validate_id("relay_envelope", record["original_envelope_id"]):
            raise ContractValidationError("invalid original_envelope_id")
    if "mandate_id" in record and record["mandate_id"]:
        if not validate_id("mandate_artifact", record["mandate_id"]):
            raise ContractValidationError("invalid mandate_id")
    if "docket_id" in record and record["docket_id"]:
        if not validate_id("docket", record["docket_id"]):
            raise ContractValidationError("invalid docket_id")
    if record["rejection_code"] not in {item.value for item in RejectionCode}:
        raise ContractValidationError("invalid rejection_code")
    _expect_member(AuditActor, record["actor"], "actor")
    if not validate_utc_timestamp(record["received_at"]):
        raise ContractValidationError("invalid received_at")
    return True


def validate_verifier_mandate_envelope(envelope: dict[str, Any]) -> bool:
    required = {
        "verifier_envelope_version",
        "mandate_id",
        "docket_id",
        "source_workspace",
        "target_commit",
        "artifact_path",
        "authorized_artifact_sha256",
        "modified_source_paths",
        "trusted_tests",
        "state_root",
    }
    _require_exact_fields(envelope, required)
    if envelope["verifier_envelope_version"] != "2A.P6.1":
        raise ContractValidationError("invalid verifier_envelope_version")
    if not validate_id("mandate_artifact", envelope["mandate_id"]):
        raise ContractValidationError("invalid mandate_id")
    if not validate_id("docket", envelope["docket_id"]):
        raise ContractValidationError("invalid docket_id")
    if not validate_sha256_hash(envelope["authorized_artifact_sha256"]):
        raise ContractValidationError("invalid authorized_artifact_sha256")
    if not isinstance(envelope["source_workspace"], str) or not envelope["source_workspace"]:
        raise ContractValidationError("invalid source_workspace")
    if not isinstance(envelope["target_commit"], str) or not envelope["target_commit"]:
        raise ContractValidationError("invalid target_commit")
    if not isinstance(envelope["artifact_path"], str) or not envelope["artifact_path"]:
        raise ContractValidationError("invalid artifact_path")
    if not isinstance(envelope["state_root"], str) or not envelope["state_root"]:
        raise ContractValidationError("invalid state_root")
    if not isinstance(envelope["modified_source_paths"], list) or not all(
        isinstance(path, str) and path.endswith(".py") for path in envelope["modified_source_paths"]
    ):
        raise ContractValidationError("invalid modified_source_paths")
    if not isinstance(envelope["trusted_tests"], list) or not envelope["trusted_tests"]:
        raise ContractValidationError("invalid trusted_tests")
    for test in envelope["trusted_tests"]:
        if not isinstance(test, dict):
            raise ContractValidationError("invalid trusted test entry")
        _require_exact_fields(test, {"identifier", "content_sha256"})
        if not isinstance(test["identifier"], str):
            raise ContractValidationError("invalid trusted test identifier")
        try:
            reject_broad_pytest_collection(test["identifier"])
        except ValueError as exc:
            raise ContractValidationError(str(exc)) from exc
        if not validate_sha256_hash(test["content_sha256"]):
            raise ContractValidationError("invalid trusted test content_sha256")
    return True
