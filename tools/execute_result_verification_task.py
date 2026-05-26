from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from axiom.agents.manual_cli import run_manual_agent_cli  # noqa: E402
from axiom.agents.result_verifier import execute_result_verification_task  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Manually execute one manifest-bound ResultVerifier task."
    )
    parser.add_argument("task_id", type=int)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--manual-test-override", action="store_true")
    args = parser.parse_args()

    return run_manual_agent_cli(
        agent_name="result_verifier",
        task_id=args.task_id,
        execute=execute_result_verification_task,
        json_output=args.json,
        manual_test_override=args.manual_test_override,
    )


if __name__ == "__main__":
    raise SystemExit(main())
