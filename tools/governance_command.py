from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from axiom.core.governance_command import (
    create_command_manifest,
    list_command_intents,
    list_command_manifests,
    load_command_manifest,
    parse_governance_command,
    record_command_intent,
)


def _raw(command: str | None, payload_json: str | None) -> str | dict:
    if payload_json:
        payload = json.loads(payload_json)
        if not isinstance(payload, dict):
            raise ValueError("--payload-json must decode to an object")
        return {"command": command, "payload": payload}
    return command or sys.stdin.read()


def main() -> int:
    parser = argparse.ArgumentParser(description="Parse and record JSON-first AXIOM /axiom:* command intent.")
    parser.add_argument("--root", type=Path, default=ROOT)
    subparsers = parser.add_subparsers(dest="command", required=True)

    manifest = subparsers.add_parser("create-manifest")
    manifest.add_argument("--axiom-command", required=True)
    manifest.add_argument("--effect-class", default="record_intent")
    manifest.add_argument("--allowed-payload-key", action="append", default=[])
    manifest.add_argument("--requires-confirmation", action="store_true")
    manifest.add_argument("--summary", default="")
    manifest.add_argument("--json", action="store_true")

    list_manifests = subparsers.add_parser("list-manifests")
    list_manifests.add_argument("--json", action="store_true")

    show_manifest = subparsers.add_parser("show-manifest")
    show_manifest.add_argument("manifest_id")
    show_manifest.add_argument("--json", action="store_true")

    parse = subparsers.add_parser("parse")
    parse.add_argument("axiom_command", nargs="?")
    parse.add_argument("--payload-json")
    parse.add_argument("--json", action="store_true")

    record = subparsers.add_parser("record")
    record.add_argument("axiom_command", nargs="?")
    record.add_argument("--payload-json")
    record.add_argument("--json", action="store_true")

    list_intents = subparsers.add_parser("list-intents")
    list_intents.add_argument("--json", action="store_true")

    args = parser.parse_args()
    record_root = args.root / "governance" / "80_records"

    if args.command == "create-manifest":
        result = create_command_manifest(
            record_root=record_root,
            command=args.axiom_command,
            effect_class=args.effect_class,
            allowed_payload_keys=args.allowed_payload_key,
            requires_confirmation=args.requires_confirmation,
            summary=args.summary,
        ).to_dict()
        print(json.dumps(result, indent=2, sort_keys=True) if args.json else result["path"])
        return 0

    if args.command == "list-manifests":
        payload = {"command_manifests": list_command_manifests(record_root=record_root)}
        print(json.dumps(payload, indent=2, sort_keys=True) if args.json else "\n".join(item["manifest_id"] for item in payload["command_manifests"]))
        return 0

    if args.command == "show-manifest":
        payload = load_command_manifest(args.manifest_id, record_root=record_root)
        print(json.dumps(payload, indent=2, sort_keys=True) if args.json else payload.get("manifest_id", ""))
        return 0

    if args.command == "parse":
        result = parse_governance_command(_raw(args.axiom_command, args.payload_json), record_root=record_root).to_dict()
        print(json.dumps(result, indent=2, sort_keys=True) if args.json else str(result["accepted"]))
        return 0 if result["accepted"] else 1

    if args.command == "record":
        result = record_command_intent(_raw(args.axiom_command, args.payload_json), record_root=record_root).to_dict()
        print(json.dumps(result, indent=2, sort_keys=True) if args.json else str(result["recorded"]))
        return 0 if result["recorded"] else 1

    if args.command == "list-intents":
        payload = {"command_intents": list_command_intents(record_root=record_root)}
        print(json.dumps(payload, indent=2, sort_keys=True) if args.json else "\n".join(item["intent_id"] for item in payload["command_intents"]))
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
