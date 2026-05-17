from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TOOL_VERSION = "test_inventory.v1"


def parse_pytest_collected_count(output: str) -> int | None:
    patterns = [
        r"collected\s+(\d+)\s+items?",
        r"(\d+)\s+tests?\s+collected",
    ]

    for pattern in patterns:
        match = re.search(pattern, output, flags=re.IGNORECASE)
        if match:
            return int(match.group(1))

    return None


def collect_test_inventory() -> dict[str, Any]:
    command = [
        sys.executable,
        "-m",
        "pytest",
        "--collect-only",
        "-q",
        "tests",
    ]

    result = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    combined_output = "\n".join(
        part for part in (result.stdout, result.stderr) if part
    )

    collected_count = parse_pytest_collected_count(combined_output)

    return {
        "tool_version": TOOL_VERSION,
        "command": command,
        "returncode": result.returncode,
        "collected_count": collected_count,
        "collection_succeeded": result.returncode == 0 and collected_count is not None,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Collect AXIOM pytest inventory without running tests."
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    inventory = collect_test_inventory()

    if args.json:
        print(json.dumps(inventory, indent=2, sort_keys=True))
    else:
        print("AXIOM test inventory")
        print("====================")
        print(f"collection_succeeded: {inventory['collection_succeeded']}")
        print(f"collected_count: {inventory['collected_count']}")
        print(f"returncode: {inventory['returncode']}")

    return 0 if inventory["collection_succeeded"] else 1


if __name__ == "__main__":
    raise SystemExit(main())