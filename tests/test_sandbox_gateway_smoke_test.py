import json
import subprocess
import sys
from pathlib import Path

from tools.sandbox_gateway_smoke_test import SENTINEL, run_sandbox_gateway_smoke


ROOT = Path(__file__).resolve().parents[1]


def test_sandbox_gateway_smoke_dry_run_reports_job_object_boundary():
    payload = run_sandbox_gateway_smoke(live=False)

    assert payload["provider"] == "windows_job_object"
    assert payload["live"] is False
    assert payload["max_ram_mb"] == 256
    assert payload["max_wall_clock_seconds"] == 60
    assert payload["network_access"] == "denied"
    assert payload["kill_on_job_close"] is True
    assert payload["active_process_limit"] == 1
    assert payload["sentinel"] == SENTINEL
    assert payload["result"] == "dry_run_only"
    assert payload["passed"] is True


def test_sandbox_gateway_smoke_cli_json_dry_run_is_parseable():
    result = subprocess.run(
        [
            sys.executable,
            "tools/sandbox_gateway_smoke_test.py",
            "--json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["provider"] == "windows_job_object"
    assert payload["live"] is False
    assert payload["passed"] is True
