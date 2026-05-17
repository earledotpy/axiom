import json
import subprocess
import sys
from pathlib import Path

from tools.generate_handoff_bundle import generate_handoff_bundle


ROOT = Path(__file__).resolve().parents[1]


def test_generate_handoff_bundle_returns_expected_shape():
    manifest = generate_handoff_bundle(profile_label="default")

    assert manifest["tool_version"] == "generate_handoff_bundle.v1"
    assert "created_at_utc" in manifest
    assert "project_root" in manifest
    assert "foundation_passed" in manifest
    assert "operational_mode" in manifest
    assert "autonomous_allowed" in manifest
    assert "fail_closed_coherent" in manifest
    assert "blocking_reasons" in manifest
    assert "artifacts" in manifest

    artifacts = manifest["artifacts"]
    assert "project_state_snapshot" in artifacts
    assert "operator_command_index_json" in artifacts
    assert "operator_command_index_markdown" in artifacts
    assert "handoff_markdown" in artifacts
    assert "bundle_manifest" in artifacts


def test_generate_handoff_bundle_artifact_paths_exist():
    manifest = generate_handoff_bundle(profile_label="default")

    for relative_path in manifest["artifacts"].values():
        path = ROOT / relative_path
        assert path.exists(), f"missing artifact: {path}"


def test_generate_handoff_bundle_cli_json_is_parseable():
    result = subprocess.run(
        [sys.executable, "tools/generate_handoff_bundle.py", "--json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0

    payload = json.loads(result.stdout)
    assert payload["tool_version"] == "generate_handoff_bundle.v1"
    assert "artifacts" in payload
    assert "bundle_manifest" in payload["artifacts"]