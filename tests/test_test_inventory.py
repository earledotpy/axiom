import json
import subprocess
import sys
from pathlib import Path

from tools.test_inventory import (
    collect_test_inventory,
    parse_pytest_collected_count,
)


ROOT = Path(__file__).resolve().parents[1]


def test_parse_pytest_collected_count_from_items_summary():
    output = "collected 212 items"
    assert parse_pytest_collected_count(output) == 212


def test_parse_pytest_collected_count_from_tests_summary():
    output = "212 tests collected in 0.42s"
    assert parse_pytest_collected_count(output) == 212


def test_test_inventory_cli_json_is_parseable():
    result = subprocess.run(
        [sys.executable, "tools/test_inventory.py", "--json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0

    payload = json.loads(result.stdout)
    assert payload["tool_version"] == "test_inventory.v1"
    assert payload["collection_succeeded"] is True
    assert isinstance(payload["collected_count"], int)
    assert payload["collected_count"] >= 200