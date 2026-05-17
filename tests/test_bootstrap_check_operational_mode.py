import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_bootstrap_check_json_includes_operational_mode_and_readiness():
    result = subprocess.run(
        [sys.executable, "tools/bootstrap_check.py", "--json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0

    payload = json.loads(result.stdout)
    assert payload["passed"] is True
    assert "operational_mode" in payload
    assert "autonomous_readiness" in payload
    assert "allowed" in payload["autonomous_readiness"]
    assert "blocking_reasons" in payload["autonomous_readiness"]


def test_bootstrap_check_text_reports_operational_mode():
    result = subprocess.run(
        [sys.executable, "tools/bootstrap_check.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert "AXIOM bootstrap validation: PASSED" in result.stdout
    assert "foundation_passed: True" in result.stdout
    assert "operational_mode:" in result.stdout
    assert "autonomous_allowed:" in result.stdout
    assert "foundation_checks:" in result.stdout