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

    assert payload["tool_version"] == "operator_command_index.v10"
    assert "generated_at_utc" in payload
    assert "python tools\\bootstrap_check.py" in commands
    assert "python tools\\status_check.py" in commands
    assert "python tools\\repair_session_state.py" in commands
    assert "python tools\\autonomous_readiness_check.py" in commands
    assert "python tools\\verify_foundation.py" in commands
    assert "python tools\\supervisor_health_check.py" in commands
    assert "python tools\\audit_task_lifecycle.py" in commands
    assert "python tools\\audit_task_execution.py" in commands
    assert "python tools\\execution_readiness_check.py" in commands
    assert "python tools\\cloud_cascade_smoke_test.py" in commands
    assert "python tools\\network_gateway_smoke_test.py" in commands
    assert "python tools\\sandbox_gateway_smoke_test.py" in commands
    assert "python tools\\memory_gateway_smoke_test.py" in commands
    assert "python tools\\run_calibration.py" in commands
    assert "python tools\\stage_noop_task.py" in commands
    assert "python tools\\scheduler_tick.py" in commands
    assert "python tools\\run_scheduler_loop.py" in commands
    assert "python tools\\dispatch_next_task.py" in commands
    assert "python tools\\start_task.py" in commands
    assert "python tools\\execute_noop_task.py" in commands
    assert "python tools\\run_manual_noop_cycle.py" in commands
    assert "python tools\\snapshot_project_state.py" in commands
    assert "python tools\\generate_handoff.py" in commands
    assert "python tools\\operator_command_index.py" in commands
    assert "pytest tests -v" in commands


def test_operator_command_index_markdown_contains_preferred_health_check():
    markdown = command_index_markdown()

    assert "# AXIOM Operator Command Index" in markdown
    assert "operator_command_index.v10" in markdown
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
    assert payload["tool_version"] == "operator_command_index.v10"
    assert payload["command_count"] >= 20


def test_operator_command_index_write_creates_json_and_markdown(tmp_path):
    paths = write_command_index(output_dir=tmp_path)

    assert paths["json"].exists()
    assert paths["markdown"].exists()

    json_payload = json.loads(paths["json"].read_text(encoding="utf-8"))
    markdown = paths["markdown"].read_text(encoding="utf-8")

    assert json_payload["tool_version"] == "operator_command_index.v10"
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


def test_operator_command_index_includes_execution_tools():
    payload = command_index_payload()
    
    commands = {entry["command"] for entry in payload["commands"]}
    assert "python tools\\run_scheduler_loop.py" in commands
    assert "python tools\\execute_noop_task.py" in commands
    assert "python tools\\audit_task_execution.py" in commands
    assert "python tools\\run_manual_noop_cycle.py" in commands
    assert "python tools\\execution_readiness_check.py" in commands
    assert "python tools\\stage_noop_task.py" in commands
    assert "python tools\\cloud_cascade_smoke_test.py" in commands
    assert "python tools\\network_gateway_smoke_test.py" in commands
    assert "python tools\\sandbox_gateway_smoke_test.py" in commands
    assert "python tools\\memory_gateway_smoke_test.py" in commands
    assert "python tools\\run_calibration.py" in commands

    text = json.dumps(payload, sort_keys=True)
    assert "--allow-when-autonomous-blocked" in text
    assert "--manual-test-override" in text


def test_operator_command_index_markdown_mentions_manual_execution_tools():
    markdown = command_index_markdown()

    assert "run_scheduler_loop.py" in markdown
    assert "execute_noop_task.py" in markdown
    assert "audit_task_execution.py" in markdown
    assert "run_manual_noop_cycle.py" in markdown
    assert "execution_readiness_check.py" in markdown
    assert "stage_noop_task.py" in markdown

def test_operator_command_index_classifies_stage_noop_task_boundary():
    payload = command_index_payload()

    entries = {
        entry["command"]: entry
        for entry in payload["commands"]
    }

    entry = entries["python tools\\stage_noop_task.py"]

    assert entry["read_only"] is False
    assert entry["requires_manual_test_override"] is False
    assert entry["dispatches_scheduler"] is False
    assert entry["executes_task_body"] is False
    assert entry["changes_task_state"] is True
    assert entry["calls_model"] is False
    assert entry["calls_network"] is False
    assert entry["calls_sandbox"] is False

def test_operator_command_index_classifies_manual_execution_tools_as_bounded_state_changing():
    payload = command_index_payload()
    
    entries = {
        entry["command"]: entry
        for entry in payload["commands"]
    }
    
    scheduler_loop = entries["python tools\\run_scheduler_loop.py"]
    assert scheduler_loop["read_only"] is False
    assert scheduler_loop["requires_manual_test_override"] is True
    assert scheduler_loop["dispatches_scheduler"] is True
    assert scheduler_loop["changes_task_state"] is True
    assert scheduler_loop["executes_task_body"] is False
    
    execute_noop = entries["python tools\\execute_noop_task.py"]
    assert execute_noop["read_only"] is False
    assert execute_noop["requires_manual_test_override"] is True
    assert execute_noop["executes_task_body"] is True
    assert execute_noop["changes_task_state"] is True
    
    manual_cycle = entries["python tools\\run_manual_noop_cycle.py"]
    assert manual_cycle["read_only"] is False
    assert manual_cycle["requires_manual_test_override"] is True
    assert manual_cycle["dispatches_scheduler"] is True
    assert manual_cycle["executes_task_body"] is True
    assert manual_cycle["changes_task_state"] is True


def test_operator_command_index_includes_policy_security_audit():
    payload = command_index_payload()
    commands = {entry["command"] for entry in payload["commands"]}
    entries = {entry["command"]: entry for entry in payload["commands"]}

    assert "python tools\\audit_policy_security.py" in commands
    
    payload_text = json.dumps(payload, sort_keys=True)
    assert "audit_policy_security" in payload_text
    assert "role/operator manifest schema and policy completeness" in payload_text
    assert "operator-control command binding" in payload_text
    assert "tool-capability semantic contracts" in payload_text
    assert "scanner return-contract stability" in payload_text
    assert "security-event schema/index/domain coverage" in payload_text
    assert (
        "docs\\phase3.md"
        in entries["python tools\\audit_policy_security.py"]["notes"]
    )

    markdown = command_index_markdown()
    assert "docs\\phase3.md" in markdown


def test_operator_command_index_classifies_cloud_cascade_smoke_test():
    payload = command_index_payload()
    entries = {entry["command"]: entry for entry in payload["commands"]}

    entry = entries["python tools\\cloud_cascade_smoke_test.py"]

    assert entry["read_only"] is False
    assert entry["requires_manual_test_override"] is True
    assert entry["dispatches_scheduler"] is False
    assert entry["executes_task_body"] is False
    assert entry["changes_task_state"] is False
    assert entry["calls_model"] is True
    assert entry["calls_network"] is False
    assert entry["calls_sandbox"] is False
    assert "--live" in entry["notes"]
    assert "docs\\phase4.md" in entry["notes"]


def test_operator_command_index_classifies_network_gateway_smoke_test():
    payload = command_index_payload()
    entries = {entry["command"]: entry for entry in payload["commands"]}

    entry = entries["python tools\\network_gateway_smoke_test.py"]

    assert entry["read_only"] is False
    assert entry["requires_manual_test_override"] is True
    assert entry["dispatches_scheduler"] is False
    assert entry["executes_task_body"] is False
    assert entry["changes_task_state"] is False
    assert entry["calls_model"] is False
    assert entry["calls_network"] is True
    assert entry["calls_sandbox"] is False
    assert "--live" in entry["notes"]
    assert "docs\\phase4.md" in entry["notes"]


def test_operator_command_index_classifies_sandbox_gateway_smoke_test():
    payload = command_index_payload()
    entries = {entry["command"]: entry for entry in payload["commands"]}

    entry = entries["python tools\\sandbox_gateway_smoke_test.py"]

    assert entry["read_only"] is False
    assert entry["requires_manual_test_override"] is True
    assert entry["dispatches_scheduler"] is False
    assert entry["executes_task_body"] is False
    assert entry["changes_task_state"] is False
    assert entry["calls_model"] is False
    assert entry["calls_network"] is False
    assert entry["calls_sandbox"] is True
    assert "--live" in entry["notes"]
    assert "docs\\phase4.md" in entry["notes"]


def test_operator_command_index_classifies_memory_gateway_smoke_test():
    payload = command_index_payload()
    entries = {entry["command"]: entry for entry in payload["commands"]}

    entry = entries["python tools\\memory_gateway_smoke_test.py"]

    assert entry["read_only"] is False
    assert entry["requires_manual_test_override"] is True
    assert entry["dispatches_scheduler"] is False
    assert entry["executes_task_body"] is False
    assert entry["changes_task_state"] is False
    assert entry["calls_model"] is True
    assert entry["calls_network"] is False
    assert entry["calls_sandbox"] is False
    assert "--live" in entry["notes"]
    assert "/api/embed" in entry["notes"]
    assert "/api/chat" in entry["notes"]
    assert "/api/generate" in entry["notes"]
    assert "docs\\phase4.md" in entry["notes"]


def test_operator_command_index_classifies_classifier_calibration_check():
    payload = command_index_payload()
    entries = {entry["command"]: entry for entry in payload["commands"]}

    entry = entries["python tools\\run_calibration.py"]

    assert entry["read_only"] is False
    assert entry["requires_manual_test_override"] is True
    assert entry["dispatches_scheduler"] is False
    assert entry["executes_task_body"] is False
    assert entry["changes_task_state"] is False
    assert entry["calls_model"] is True
    assert entry["calls_network"] is False
    assert entry["calls_sandbox"] is False
    assert "--live" in entry["notes"]
    assert "--write-db" in entry["notes"]
    assert "outside Phase 4 gateway authority" in entry["notes"]

