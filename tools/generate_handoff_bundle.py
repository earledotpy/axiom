from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.generate_handoff import write_handoff
from tools.operator_command_index import write_command_index
from tools.snapshot_project_state import write_snapshot
from tools.verify_foundation import verify_foundation


TOOL_VERSION = "generate_handoff_bundle.v1"
LOG_DIR = ROOT / "logs"


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")


def _relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path.resolve())


def generate_handoff_bundle(profile_label: str = "default") -> dict[str, Any]:
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    snapshot_path = write_snapshot(profile_label=profile_label)
    command_index_paths = write_command_index(output_dir=LOG_DIR)
    handoff_path = write_handoff(snapshot_path=snapshot_path, output_dir=LOG_DIR)
    foundation = verify_foundation(profile_label=profile_label)

    manifest = {
        "tool_version": TOOL_VERSION,
        "created_at_utc": _utc_timestamp(),
        "project_root": str(ROOT),
        "profile_label": profile_label,
        "foundation_passed": foundation["foundation_passed"],
        "operational_mode": foundation["operational_mode"],
        "autonomous_allowed": foundation["autonomous_allowed"],
        "fail_closed_coherent": foundation["fail_closed_coherent"],
        "blocking_reasons": foundation["blocking_reasons"],
        "artifacts": {
            "project_state_snapshot": _relative(snapshot_path),
            "operator_command_index_json": _relative(command_index_paths["json"]),
            "operator_command_index_markdown": _relative(command_index_paths["markdown"]),
            "handoff_markdown": _relative(handoff_path),
        },
        "recommended_start_commands": [
            "python tools\\verify_foundation.py",
            "python tools\\bootstrap_check.py",
            "python tools\\status_check.py",
            "python tools\\autonomous_readiness_check.py",
            "pytest tests -v",
        ],
    }

    manifest_path = LOG_DIR / f"handoff_bundle_manifest_{_utc_timestamp()}.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False),
        encoding="utf-8",
    )

    manifest["artifacts"]["bundle_manifest"] = _relative(manifest_path)

    # Re-write with self-reference included.
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False),
        encoding="utf-8",
    )

    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate a complete AXIOM handoff bundle."
    )
    parser.add_argument("--profile-label", default="default")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    manifest = generate_handoff_bundle(profile_label=args.profile_label)

    if args.json:
        print(json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False))
        return 0

    print("AXIOM handoff bundle")
    print("====================")
    print(f"foundation_passed: {manifest['foundation_passed']}")
    print(f"operational_mode: {manifest['operational_mode']}")
    print(f"autonomous_allowed: {manifest['autonomous_allowed']}")
    print(f"fail_closed_coherent: {manifest['fail_closed_coherent']}")

    print("")
    print("artifacts:")
    for name, path in manifest["artifacts"].items():
        print(f"- {name}: {path}")

    if manifest["blocking_reasons"]:
        print("")
        print("blocking_reasons:")
        for reason in manifest["blocking_reasons"]:
            print(f"- {reason}")

    return 0 if manifest["foundation_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())