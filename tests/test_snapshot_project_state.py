import json
import subprocess
import sys
from pathlib import Path

from axiom.persistence.db import get_connection
from tools.snapshot_project_state import build_project_state_snapshot, write_snapshot

ROOT = Path(__file__).resolve().parents[1]


def test_project_state_snapshot_shape():
    snapshot = build_project_state_snapshot(profile_label="default")

    assert snapshot["tool_version"] == "snapshot_project_state.v1"
    assert "snapshot_created_at_utc" in snapshot
    assert "project_root" in snapshot
    assert "python" in snapshot
    assert "git" in snapshot
    assert "pytest" in snapshot
    assert "bootstrap" in snapshot
    assert "status" in snapshot
    assert "autonomous_readiness" in snapshot
    assert "foundation_verification" in snapshot
    assert "database_state" in snapshot
    assert "supervisor_health" in snapshot


def test_project_state_snapshot_write_creates_json_file():
    path = write_snapshot(profile_label="default")

    assert path.exists()
    assert path.suffix == ".json"

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["tool_version"] == "snapshot_project_state.v1"
    assert "database_state" in payload
    assert "supervisor_health" in payload


def test_project_state_snapshot_cli_writes_file():
    result = subprocess.run(
        [sys.executable, "tools/snapshot_project_state.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert "wrote project state snapshot:" in result.stdout


def test_project_state_snapshot_scopes_model_profiles_to_requested_profile_label():
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO classifier_calibration_runs
            (calibration_run_id, calibration_set_id, calibration_set_sha256,
             model_name, ollama_host, threshold, passed,
             approved_by_panel_version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "snapshot.default.calibration",
                "test_calibration_set",
                "3" * 64,
                "qwen3:4b",
                "http://localhost:11434",
                0.5,
                1,
                "test",
            ),
        )

        conn.execute(
            """
            INSERT INTO classifier_calibration_runs
            (calibration_run_id, calibration_set_id, calibration_set_sha256,
             model_name, ollama_host, threshold, passed,
             approved_by_panel_version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "snapshot.other.calibration",
                "test_calibration_set",
                "4" * 64,
                "qwen3:4b",
                "http://localhost:11434",
                0.5,
                1,
                "test",
            ),
        )

        conn.execute(
            """
            INSERT INTO model_profile_fingerprints
            (profile_label, model_name, ollama_host, ollama_model_tag,
             ollama_model_digest, quantization, parameter_size, model_family,
             model_format, thinking_mode, thinking_mode_rule_version,
             selected_profile_sha256, calibration_run_id, is_current,
             registration_status, registered_by_tool_version, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "default",
                "qwen3:4b",
                "http://localhost:11434",
                "qwen3:4b",
                "digest-default",
                "Q4_K_M",
                "4.0B",
                "qwen3",
                "gguf",
                "unknown",
                "gateway_required_v1",
                "snapshot-default-" + ("0" * 47),
                "snapshot.default.calibration",
                0,
                "candidate",
                "test",
                "{}",
            ),
        )

        conn.execute(
            """
            INSERT INTO model_profile_fingerprints
            (profile_label, model_name, ollama_host, ollama_model_tag,
             ollama_model_digest, quantization, parameter_size, model_family,
             model_format, thinking_mode, thinking_mode_rule_version,
             selected_profile_sha256, calibration_run_id, is_current,
             registration_status, registered_by_tool_version, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "not_default_test_profile",
                "qwen3:4b",
                "http://localhost:11434",
                "qwen3:4b",
                "digest-other",
                "Q4_K_M",
                "4.0B",
                "qwen3",
                "gguf",
                "disabled",
                "profile_verified_v1",
                "snapshot-other-" + ("1" * 49),
                "snapshot.other.calibration",
                0,
                "candidate",
                "test",
                "{}",
            ),
        )

    snapshot = build_project_state_snapshot(profile_label="default")
    profiles = snapshot["database_state"]["latest_model_profiles"]

    assert profiles
    assert {profile["profile_label"] for profile in profiles} == {"default"}