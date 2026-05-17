import json
import subprocess
import sys
from pathlib import Path

from tools.operator_command_index import (
    command_index_markdown,
    command_index_payload,
    write_command_index,
)


ROOT = Path(__file__).resolve().parents[1]


def test_operator_command_index_payload_contains_core_commands():
    payload = command_index_payload()

    commands = {entry["command"] for entry in payload["commands"]}

    assert payload["tool_version"] == "operator_command_index.v2"
    assert "generated_at_utc" in payload
    assert "python tools\\bootstrap_check.py" in commands
    assert "python tools\\status_check.py" in commands
    assert "python tools\\repair_session_state.py" in commands
    assert "python tools\\autonomous_readiness_check.py" in commands
    assert "python tools\\verify_foundation.py" in commands
    assert "python tools\\snapshot_project_state.py" in commands
    assert "python tools\\generate_handoff.py" in commands
    assert "python tools\\operator_command_index.py" in commands
    assert "pytest tests -v" in commands


def test_operator_command_index_markdown_contains_preferred_health_check():
    markdown = command_index_markdown()

    assert "# AXIOM Operator Command Index" in markdown
    assert "operator_command_index.v2" in markdown
    assert "python tools\\verify_foundation.py" in markdown
    assert "preferred quick health check" in markdown
    assert "pytest tests -v" in markdown


def test_operator_command_index_cli_json_is_parseable():
    result = subprocess.run(
        [sys.executable, "tools/operator_command_index.py", "--json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0

    payload = json.loads(result.stdout)
    assert payload["tool_version"] == "operator_command_index.v2"
    assert payload["command_count"] >= 9


def test_operator_command_index_write_creates_json_and_markdown(tmp_path):
    paths = write_command_index(output_dir=tmp_path)

    assert paths["json"].exists()
    assert paths["markdown"].exists()

    json_payload = json.loads(paths["json"].read_text(encoding="utf-8"))
    markdown = paths["markdown"].read_text(encoding="utf-8")

    assert json_payload["tool_version"] == "operator_command_index.v2"
    assert "# AXIOM Operator Command Index" in markdown


def test_operator_command_index_cli_write_succeeds():
    result = subprocess.run(
        [sys.executable, "tools/operator_command_index.py", "--write"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert "wrote operator command index JSON:" in result.stdout
    assert "wrote operator command index Markdown:" in result.stdout