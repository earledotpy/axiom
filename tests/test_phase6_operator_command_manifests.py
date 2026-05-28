from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from axiom.core.manifest_binder import ManifestBinder
from axiom.core.policy_engine import PolicyEngine
from axiom.persistence.repositories import get_manifest_fingerprint


ROOT = Path(__file__).resolve().parents[1]
POLICY_ROOT = ROOT / "axiom" / "policy"
STATUS_MANIFEST = (
    POLICY_ROOT / "operator_control_manifests" / "status.v1.json"
)
MANIFEST_SCHEMA = POLICY_ROOT / "schemas" / "manifest_schema.json"
TOOL_MAP_SCHEMA = POLICY_ROOT / "schemas" / "tool_capability_map_schema.json"
TOOL_MAP = POLICY_ROOT / "security_artifacts" / "tool_capability_map.json"
DOC = ROOT / "docs" / "phase6.md"


def load_status_manifest() -> dict:
    return json.loads(STATUS_MANIFEST.read_text(encoding="utf-8"))


def test_phase6_status_operator_manifest_is_read_only_and_local_only():
    manifest = load_status_manifest()

    assert manifest["manifest_type"] == "operator_control"
    assert manifest["manifest_id"] == "operator.status.v1"
    assert manifest["operator_command"]["command_name"] == "status"
    assert manifest["operator_command"]["effect_class"] == "read_only"
    assert manifest["operator_command"]["creates_task"] is False
    assert manifest["allowed_tools"] == ["session_controller.status"]
    assert manifest["allowed_capabilities"]["operator_control"][
        "allowed_commands"
    ] == ["status"]
    assert manifest["allowed_capabilities"]["model"]["allow_model_calls"] is False
    assert manifest["network_policy"]["mode"] == "deny_all"
    assert manifest["sandbox_policy"]["allowed"] is False
    assert manifest["memory_policy"]["read"] is False
    assert manifest["memory_policy"]["write"] is False
    assert manifest["allowed_capabilities"]["filesystem"]["read"] is False
    assert manifest["allowed_capabilities"]["filesystem"]["write"] is False


def test_phase6_status_operator_manifest_validates_and_authorizes_status_only():
    manifest = load_status_manifest()
    binder = ManifestBinder(MANIFEST_SCHEMA, TOOL_MAP_SCHEMA, TOOL_MAP)
    binder.validate_manifest(manifest)

    effective = binder.derive_effective_capabilities(manifest)

    assert effective["effective_tool_ids"] == ["session_controller.status"]

    policy = PolicyEngine()
    allowed = policy.authorize_tool_use("session_controller.status", manifest)
    denied = policy.authorize_tool_use(
        "session_controller.enable_autonomous",
        manifest,
    )

    assert allowed.allowed is True
    assert denied.allowed is False
    assert denied.reason == "tool_not_in_allowed_tools"


def test_phase6_register_manifests_registers_status_operator_manifest():
    result = subprocess.run(
        [sys.executable, "tools/register_manifests.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "registered" in result.stdout

    row = get_manifest_fingerprint("operator.status.v1")
    assert row is not None
    assert row["manifest_type"] == "operator_control"
    assert row["command_name"] == "status"
    assert row["role_name"] is None
    assert row["active"] == 1


def test_phase6_operator_manifest_doc_records_6b_scope():
    text = DOC.read_text(encoding="utf-8")

    required = [
        "operator.status.v1 -> status -> session_controller.status",
        "effect_class: read_only",
        "allowed_tools: session_controller.status",
        "cancel_current_chain",
        "pause_after_current",
        "resume",
        "shutdown_after_current",
        "run_classifier_validation",
        "enable_autonomous",
        "reconcile_provider_usage",
        "Telegram runtime",
        "external command ingestion",
    ]

    for phrase in required:
        assert phrase in text


