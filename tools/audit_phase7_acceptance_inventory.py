from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
IMPLEMENTATION = ROOT / "AXIOM_Implementation_v1.13.md"
INVENTORY_DOC = ROOT / "docs" / "phase7_acceptance_inventory.md"

ACCEPTANCE_RE = re.compile(r"^(\d+)\.\s+\*\*(Phase \d+)\*\*\s+—\s+(.+?)\s*$")

EXPECTED_ROW_COUNT = 108

COVERAGE_BUCKETS = [
    {
        "name": "schema_and_manifest_foundation",
        "range": [1, 28],
        "tests": [
            "tests/test_sqlite_wal_mode.py",
            "tests/test_schema_v1114_amendments.py",
            "tests/test_manifest_binder.py",
            "tests/test_register_manifests.py",
            "tests/test_policy_security_audit.py",
        ],
        "status": "covered",
    },
    {
        "name": "model_fingerprint_and_gateway",
        "range": [29, 48],
        "tests": [
            "tests/test_register_model_fingerprint.py",
            "tests/test_model_fingerprint_guard.py",
            "tests/test_model_gateway.py",
            "tests/test_model_gateway_wrapper.py",
        ],
        "status": "covered_with_blocked_live_profile",
    },
    {
        "name": "scanner_contract_and_enum_domains",
        "range": [49, 56],
        "tests": [
            "tests/test_plan_injection_scanner.py",
            "tests/test_plan_artifact_scanner_service.py",
            "tests/test_policy_security_audit.py",
        ],
        "status": "covered",
    },
    {
        "name": "policy_engine_and_manifest_binder",
        "range": [57, 67],
        "tests": [
            "tests/test_policy_engine.py",
            "tests/test_manifest_binder.py",
            "tests/test_boot_verifier.py",
        ],
        "status": "covered",
    },
    {
        "name": "database_integrity_and_runtime_domains",
        "range": [68, 83],
        "tests": [
            "tests/test_schema_v1114_amendments.py",
            "tests/test_repositories.py",
            "tests/test_task_permissions.py",
            "tests/test_plan_artifacts.py",
            "tests/test_bootstrap_validation.py",
            "tests/test_policy_security_audit.py",
        ],
        "status": "covered",
    },
    {
        "name": "cli_behavior_and_registration_hardening",
        "range": [84, 92],
        "tests": [
            "tests/test_register_manifests.py",
            "tests/test_register_model_fingerprint.py",
        ],
        "status": "partial_gap_named",
        "gap": "Rows 84 and 85 require explicit under-30-second CLI timing evidence.",
    },
    {
        "name": "boot_logging_and_network_policy_edges",
        "range": [93, 100],
        "tests": [
            "tests/test_boot_verifier.py",
            "tests/test_manifest_binder.py",
            "tests/test_register_manifests.py",
        ],
        "status": "covered",
    },
    {
        "name": "operator_manifest_and_tool_map_final_rows",
        "range": [101, 108],
        "tests": [
            "tests/test_phase6_operator_command_manifests.py",
            "tests/test_manifest_binder.py",
            "tests/test_policy_security_audit.py",
            "tests/test_register_manifests.py",
        ],
        "status": "covered",
    },
]

E2E_BLOCKERS = [
    "classifier calibration approval material",
    "passing calibration run stored in classifier_calibration_runs",
    "current model fingerprint registration",
    "safe-pass readiness decision",
    "explicit operator approval before full-goal E2E",
]


@dataclass(frozen=True)
class AcceptanceRow:
    row_id: int
    phase: str
    requirement: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Phase7AcceptanceInventoryResult:
    passed: bool
    acceptance_row_count: int
    first_row_id: int | None
    last_row_id: int | None
    bucket_count: int
    buckets: list[dict[str, Any]]
    e2e_blockers: list[str]
    violations: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def parse_acceptance_rows() -> list[AcceptanceRow]:
    rows: list[AcceptanceRow] = []
    in_suite = False

    for line in IMPLEMENTATION.read_text(encoding="utf-8").splitlines():
        if line.startswith("# Canonical MVP Acceptance Test Suite"):
            in_suite = True
            continue

        if in_suite and line.startswith("## Task 3 Verification Shell Snippet"):
            break

        if not in_suite:
            continue

        match = ACCEPTANCE_RE.match(line)
        if match:
            rows.append(
                AcceptanceRow(
                    row_id=int(match.group(1)),
                    phase=match.group(2),
                    requirement=match.group(3).strip(),
                )
            )

    return rows


def audit_phase7_acceptance_inventory() -> Phase7AcceptanceInventoryResult:
    rows = parse_acceptance_rows()
    violations: list[dict[str, Any]] = []

    row_ids = [row.row_id for row in rows]
    first_row_id = min(row_ids) if row_ids else None
    last_row_id = max(row_ids) if row_ids else None

    if len(rows) != EXPECTED_ROW_COUNT:
        violations.append(
            {
                "check": "acceptance_row_count",
                "reason": "unexpected_acceptance_row_count",
                "expected": EXPECTED_ROW_COUNT,
                "actual": len(rows),
            }
        )

    expected_ids = set(range(1, EXPECTED_ROW_COUNT + 1))
    missing_ids = sorted(expected_ids - set(row_ids))
    extra_ids = sorted(set(row_ids) - expected_ids)
    if missing_ids or extra_ids:
        violations.append(
            {
                "check": "acceptance_row_ids",
                "reason": "acceptance_row_ids_not_contiguous",
                "missing_ids": missing_ids,
                "extra_ids": extra_ids,
            }
        )

    if not INVENTORY_DOC.exists():
        violations.append(
            {
                "check": "inventory_doc",
                "reason": "phase7_acceptance_inventory_doc_missing",
                "path": str(INVENTORY_DOC.relative_to(ROOT)),
            }
        )
    else:
        text = INVENTORY_DOC.read_text(encoding="utf-8")
        required_phrases = [
            "108 canonical MVP acceptance rows",
            "Rows 84 and 85 require explicit under-30-second CLI timing evidence.",
            "tests/e2e/test_full_goal_flow_minimum.py",
            "classifier calibration approval material",
            "model fingerprint registration",
        ]
        for phrase in required_phrases:
            if phrase not in text:
                violations.append(
                    {
                        "check": "inventory_doc",
                        "reason": "phase7_acceptance_inventory_phrase_missing",
                        "phrase": phrase,
                    }
                )

    for bucket in COVERAGE_BUCKETS:
        start, end = bucket["range"]
        for row_id in range(start, end + 1):
            if row_id not in row_ids:
                violations.append(
                    {
                        "check": "coverage_bucket_ranges",
                        "reason": "bucket_references_missing_acceptance_row",
                        "bucket": bucket["name"],
                        "row_id": row_id,
                    }
                )

        for test_path in bucket["tests"]:
            if not (ROOT / test_path).exists():
                violations.append(
                    {
                        "check": "coverage_bucket_tests",
                        "reason": "mapped_test_missing",
                        "bucket": bucket["name"],
                        "test_path": test_path,
                    }
                )

    return Phase7AcceptanceInventoryResult(
        passed=not violations,
        acceptance_row_count=len(rows),
        first_row_id=first_row_id,
        last_row_id=last_row_id,
        bucket_count=len(COVERAGE_BUCKETS),
        buckets=COVERAGE_BUCKETS,
        e2e_blockers=E2E_BLOCKERS,
        violations=violations,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit AXIOM Phase 7A v1.13 acceptance inventory."
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = audit_phase7_acceptance_inventory()
    payload = result.to_dict()

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("AXIOM Phase 7A acceptance inventory audit")
        print("=========================================")
        print(f"passed: {payload['passed']}")
        print(f"acceptance_row_count: {payload['acceptance_row_count']}")
        print(f"row_id_span: {payload['first_row_id']}..{payload['last_row_id']}")
        print(f"bucket_count: {payload['bucket_count']}")
        print("")
        print("buckets:")
        for bucket in payload["buckets"]:
            start, end = bucket["range"]
            print(f"- {bucket['name']}: rows {start}-{end}; {bucket['status']}")
        print("")
        print("e2e blockers:")
        for blocker in payload["e2e_blockers"]:
            print(f"- {blocker}")
        print("")
        print("violations:")
        if payload["violations"]:
            for violation in payload["violations"]:
                print(f"- {violation['check']}: {violation['reason']}")
        else:
            print("- none")

    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
