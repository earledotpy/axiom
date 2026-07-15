import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP_CHECK = ROOT / "tools" / "bootstrap_check.py"


def test_bootstrap_check_cli_exits_zero_on_current_foundation():
    result = subprocess.run(
        [sys.executable, str(BOOTSTRAP_CHECK)],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0
    assert "AXIOM bootstrap validation: PASSED" in result.stdout
    assert "[PASS] sqlite_pragmas" in result.stdout
    assert "[PASS] manifest_fingerprints" in result.stdout


def test_bootstrap_check_cli_json_output():
    result = subprocess.run(
        [sys.executable, str(BOOTSTRAP_CHECK), "--json"],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0
    assert '"passed": true' in result.stdout
    assert '"name": "schema_version"' in result.stdout
    assert '"name": "manifest_fingerprints"' in result.stdout
