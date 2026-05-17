import json
import subprocess
import sys
from pathlib import Path

from tools.generate_handoff import build_handoff_markdown, write_handoff


ROOT = Path(__file__).resolve().parents[1]


def fake_snapshot() -> dict:
    return {
        "snapshot_created_at_utc": "2026-05-16T00-00-00Z",
        "project_root": "C:\\axiom",
        "pytest": {"last_known_target": "201 passed"},
        "bootstrap": {
            "passed": True,
            "operational_mode": "fail_closed_non_autonomous",
        },
        "autonomous_readiness": {
            "allowed": False,
            "blocking_reasons": [
                "no_current_trusted_model_profile",
                "safe_pass_disabled",
                "autonomous_operation_disabled",
            ],
        },
        "supervisor_health": {
            "checked": True,
            "reason": "supervisor_health_ok",
            "health": {
                "healthy": True,
                "scheduler_stale": False,
                "running_count": 0,
                "active_task_present": False,
                "active_task_status": None,
            },
        },
        "status": {},
        "foundation_verification": {
            "fail_closed_coherent": True,
        },
        "database_state": {
            "latest_model_profiles": [
                {
                    "profile_id": 19,
                    "profile_label": "default",
                    "model_name": "qwen3:4b",
                    "ollama_host": "http://localhost:11434",
                    "ollama_model_tag": "qwen3:4b",
                    "ollama_model_digest": "Qwen3",
                    "quantization": "Q4_K_M",
                    "parameter_size": "4.0B",
                    "model_family": "qwen3",
                    "model_format": "gguf",
                    "thinking_mode": "unknown",
                    "thinking_mode_rule_version": "gateway_required_v1",
                    "calibration_run_id": "pending_calibration",
                    "is_current": 0,
                    "registration_status": "candidate",
                    "registered_at": "2026-05-16T00:00:00Z",
                }
            ],
            "latest_sessions": [
                {
                    "session_id": 1,
                    "created_at": "2026-05-16T00:00:00Z",
                    "scheduler_status": "initializing",
                    "safe_pass_enabled": 0,
                    "safe_pass_disabled_reason": "no_stored_profile",
                    "safe_pass_disabled_at": "2026-05-16T00:00:00Z",
                    "autonomous_operation_enabled": 0,
                    "shutdown_requested": 0,
                }
            ],
        },
    }


def test_build_handoff_markdown_contains_core_state():
    markdown = build_handoff_markdown(fake_snapshot())

    assert "# AXIOM Project Handoff" in markdown
    assert "fail_closed_non_autonomous" in markdown
    assert "no_current_trusted_model_profile" in markdown
    assert "qwen3:4b" in markdown
    assert "candidate" in markdown
    assert "pytest tests -v" in markdown
    assert "## Supervisor Health" in markdown
    assert "supervisor_health_ok" in markdown
    assert "Running count" in markdown
    assert "Active task present" in markdown

def test_write_handoff_creates_markdown_from_snapshot(tmp_path):
    snapshot_path = tmp_path / "project_state_snapshot_test.json"
    snapshot_path.write_text(json.dumps(fake_snapshot()), encoding="utf-8")

    output_path = write_handoff(snapshot_path=snapshot_path, output_dir=tmp_path)

    assert output_path.exists()
    assert output_path.suffix == ".md"
    assert "AXIOM Project Handoff" in output_path.read_text(encoding="utf-8")


def test_generate_handoff_cli_writes_file():
    result = subprocess.run(
        [sys.executable, "tools/generate_handoff.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert "wrote AXIOM handoff:" in result.stdout