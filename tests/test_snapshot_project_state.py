import json
import subprocess
import sys
from pathlib import Path

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