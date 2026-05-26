import json
import subprocess
import sys
from pathlib import Path

from tools.verify_foundation import verify_foundation


ROOT = Path(__file__).resolve().parents[1]


def test_verify_foundation_returns_expected_shape():
    result = verify_foundation(profile_label="default")

    assert result["tool_version"] == "verify_foundation.v2"
    assert "foundation_passed" in result
    assert "operational_mode" in result
    assert "session_repair_completed" in result
    assert "autonomous_allowed" in result
    assert "fail_closed_coherent" in result
    assert "blocking_reasons" in result
    assert "bootstrap" in result
    assert "session_repair" in result
    assert "status" in result
    assert "autonomous_readiness" in result
    assert "supervisor_health" in result

    supervisor = result["supervisor_health"]
    assert "checked" in supervisor
    assert "reason" in supervisor
    assert "health" in supervisor


def test_verify_foundation_cli_text_exits_zero_when_foundation_passes():
    result = subprocess.run(
        [sys.executable, "tools/verify_foundation.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert "AXIOM foundation verification" in result.stdout
    assert "foundation_passed: True" in result.stdout
    assert "operational_mode:" in result.stdout
    assert "autonomous_allowed:" in result.stdout
    assert "supervisor_health:" in result.stdout


def test_verify_foundation_cli_json_exits_zero_and_is_parseable():
    result = subprocess.run(
        [sys.executable, "tools/verify_foundation.py", "--json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0

    payload = json.loads(result.stdout)
    assert payload["tool_version"] == "verify_foundation.v2"
    assert payload["foundation_passed"] is True
    assert "bootstrap" in payload
    assert "status" in payload
    assert "autonomous_readiness" in payload
    assert "supervisor_health" in payload
    
    
def test_verify_foundation_includes_task_execution_audit():
    result = verify_foundation()

    assert "task_execution_audit" in result
    audit = result["task_execution_audit"]

    assert audit["checked"] is True
    assert "passed" in audit
    assert audit["scope"] == "latest_session"
    assert "checked_task_count" in audit
    assert "violation_count" in audit


def test_verify_foundation_includes_policy_security_audit():
    result = verify_foundation()

    assert "policy_security_audit" in result
    assert result["policy_security_audit"]["checked"] is True
    assert "passed" in result["policy_security_audit"]
    assert "violation_count" in result["policy_security_audit"]
