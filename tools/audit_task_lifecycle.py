from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from axiom.core.task_lifecycle_audit import audit_task_lifecycle


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit AXIOM task lifecycle invariants."
    )
    parser.add_argument("--session-id", type=int)
    parser.add_argument(
        "--latest-session",
        action="store_true",
        help="Audit only the latest session. This is the default.",
    )
    parser.add_argument(
        "--all-sessions",
        action="store_true",
        help="Audit all historical sessions.",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.all_sessions and args.session_id is not None:
        parser.error("--all-sessions cannot be combined with --session-id")

    if args.all_sessions and args.latest_session:
        parser.error("--all-sessions cannot be combined with --latest-session")

    if args.all_sessions:
        session_id = None
        latest_session = False
        scope = "all_sessions"
    elif args.session_id is not None:
        session_id = args.session_id
        latest_session = False
        scope = "session_id"
    else:
        session_id = None
        latest_session = True
        scope = "latest_session"

    result = audit_task_lifecycle(
        session_id=session_id,
        latest_session=latest_session,
    )

    payload = result.to_dict()
    payload["scope"] = scope

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("AXIOM task lifecycle audit")
        print("==========================")
        print(f"passed: {result.passed}")
        print(f"scope: {scope}")
        print(f"session_id: {result.session_id}")

        if result.violations:
            print("")
            print("violations:")
            for violation in result.violations:
                print(f"- {violation.code}: {violation.reason}")
        else:
            print("")
            print("violations: none")

    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())