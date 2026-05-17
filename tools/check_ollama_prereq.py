from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from axiom.gateways.ollama_prereq import OllamaPrereqInspector


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check read-only Ollama prerequisites for AXIOM."
    )
    parser.add_argument("--host", default="http://localhost:11434")
    parser.add_argument("--model", default="qwen3:4b")
    parser.add_argument("--timeout", type=int, default=5)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = OllamaPrereqInspector(
        host=args.host,
        model=args.model,
        timeout_seconds=args.timeout,
    ).inspect()

    payload = asdict(result)
    if not args.json:
        payload.pop("raw_show", None)

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"AXIOM Ollama prerequisite check: {result.reason}")
        print(f"host: {result.host}")
        print(f"model: {result.model}")
        print(f"reachable: {result.reachable}")
        print(f"tags_available: {result.tags_available}")
        print(f"model_present: {result.model_present}")
        print(f"show_available: {result.show_available}")
        print(f"details_present: {result.details_present}")
        print(f"parameters_present: {result.parameters_present}")
        print(f"quantization_level: {result.quantization_level}")
        print(f"profile_thinking_mode: {result.profile_thinking_mode}")
        print(f"runtime_thinking_enforcement: {result.runtime_thinking_enforcement}")
        print(f"fingerprint_registration_ready: {result.fingerprint_registration_ready}")

    if not result.reachable:
        return 1

    if not result.model_present:
        return 2

    if not result.show_available:
        return 3

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
