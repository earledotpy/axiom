import json
import subprocess
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

from axiom.core.delegation import (
    build_delegation_packet,
    create_delegation_packet,
    list_delegation_packets,
    load_delegation_packet,
)
from axiom.core.operator_console import build_command_output


ROOT = Path(__file__).resolve().parents[1]


def _record_root(tmp_path: Path) -> Path:
    root = tmp_path / "governance" / "80_records"
    for directory in (
        "tasks",
        "delegations",
        "handoffs",
        "evaluations",
        "evidence",
        "decisions",
        "console",
        "autonomy",
        "archive",
    ):
        (root / directory).mkdir(parents=True, exist_ok=True)
    return root


def test_build_delegation_packet_is_advisory_and_uses_route_mapping():
    packet = build_delegation_packet(
        operator_goal="Create delegation support",
        scope="MND-4",
        recommended_first_agent="ARCH",
        allowed_actions=["read repository files"],
    )
    payload = packet.to_dict()

    assert payload["schema"] == "axiom.delegation_packet.v0.1"
    assert payload["authority_status"] == "advisory_only"
    assert payload["recommended_first_agent"] == "ARCH"
    assert payload["process"] == "architect"
    assert payload["function"] == "plan"
    assert payload["runtime_action_executed"] is False if "runtime_action_executed" in payload else True
    assert "enable runtime autonomy" in payload["forbidden_actions"]


def test_created_delegation_packet_validates_against_schema(tmp_path):
    record_root = _record_root(tmp_path)
    result = create_delegation_packet(
        operator_goal="Create delegation support",
        scope="MND-4",
        record_root=record_root,
        recommended_first_agent="CURSOR",
        allowed_actions=["create advisory JSON handoffs"],
        required_reviews=["AUD"],
    )

    path = Path(result.path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    schema = json.loads(
        (ROOT / "governance" / "80_records" / "schemas" / "delegation_packet.schema.json").read_text(
            encoding="utf-8"
        )
    )
    Draft202012Validator(schema).validate(payload)

    assert path.exists()
    assert payload["delegation_id"].startswith("DLG-")
    assert payload["authority_status"] == "advisory_only"
    assert payload["recommended_first_agent"] == "CURSOR"
    assert payload["process"] == "synthesize"
    assert payload["function"] == "summarize"


def test_legacy_syn_role_normalizes_to_cursor():
    packet = build_delegation_packet(
        operator_goal="Summarize governance state",
        scope="MND-CURSOR",
        recommended_first_agent="SYN",
    ).to_dict()

    assert packet["recommended_first_agent"] == "CURSOR"
    assert packet["allowed_roles"] == ["CURSOR"]
    assert packet["process"] == "synthesize"
    assert packet["function"] == "summarize"


def test_list_and_load_delegation_packets(tmp_path):
    record_root = _record_root(tmp_path)
    created = create_delegation_packet(
        operator_goal="List delegation support",
        scope="MND-4",
        record_root=record_root,
    )

    packets = list_delegation_packets(record_root=record_root)
    loaded = load_delegation_packet(created.packet["delegation_id"], record_root=record_root)

    assert len(packets) == 1
    assert packets[0]["delegation_id"] == created.packet["delegation_id"]
    assert loaded["operator_goal"] == "List delegation support"


def test_delegation_cli_create_and_list(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            "tools/delegation.py",
            "--root",
            str(tmp_path),
            "create",
            "--goal",
            "Create delegation CLI",
            "--scope",
            "MND-4",
            "--first-agent",
            "AUD",
            "--json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["created"] is True
    assert payload["runtime_action_executed"] is False
    assert payload["ledger_written"] is False
    assert payload["packet"]["process"] == "audit"
    assert payload["packet"]["function"] == "verify"

    list_result = subprocess.run(
        [
            sys.executable,
            "tools/delegation.py",
            "--root",
            str(tmp_path),
            "list",
            "--json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert list_result.returncode == 0
    listed = json.loads(list_result.stdout)
    assert len(listed["delegations"]) == 1
    assert listed["delegations"][0]["scope"] == "MND-4"


def test_operator_console_active_state_includes_delegation_packets(tmp_path):
    record_root = _record_root(tmp_path)
    create_delegation_packet(
        operator_goal="Show delegation in console",
        scope="MND-4",
        record_root=record_root,
        recommended_first_agent="IMPL",
    )

    output = build_command_output("/axiom:show-active-state", root=tmp_path)

    assert output["data"]["summary"]["active_count"] == 1
    item = output["data"]["active_state"][0]
    assert item["scope"] == "MND-4"
    assert item["authority_status"] == "advisory_only"
    assert item["next_expected_role"] == "IMPL"
