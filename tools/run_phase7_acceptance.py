from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = ROOT / "axiom.db"
E2E_TEST_PATH = "tests/e2e/test_full_goal_flow_minimum.py"
CALIBRATION_WRITE_APPROVAL_TOKEN = "phase4_calibration_manual_approval"
E2E_APPROVAL_EVENT_TYPE = "phase7_full_goal_e2e_approved"
E2E_OPERATOR_APPROVAL_TOKEN = "phase7_e2e_operator_approval"

sys.path.insert(0, str(ROOT))

from tools.audit_phase7_acceptance_inventory import (  # noqa: E402
    COVERAGE_BUCKETS,
    audit_phase7_acceptance_inventory,
)


@dataclass(frozen=True)
class PrerequisiteStatus:
    name: str
    passed: bool
    detail: str
    evidence: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Phase7AcceptancePlan:
    passed: bool
    acceptance_inventory_passed: bool
    canonical_test_paths: list[str]
    prerequisites: list[PrerequisiteStatus]
    e2e_test_path: str
    e2e_test_present: bool
    e2e_ready: bool
    e2e_blockers: list[str]
    executed: bool
    command: list[str]
    returncode: int | None
    stdout_tail: list[str]
    stderr_tail: list[str]
    violations: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["prerequisites"] = [item.to_dict() for item in self.prerequisites]
        return payload


def get_db_path() -> Path:
    return Path(os.environ.get("AXIOM_DB_PATH", str(DEFAULT_DB_PATH)))


def canonical_test_paths() -> list[str]:
    paths: list[str] = []
    seen: set[str] = set()
    for bucket in COVERAGE_BUCKETS:
        for path in bucket["tests"]:
            if path not in seen:
                seen.add(path)
                paths.append(path)
    return paths


def _read_only_connection(db_path: Path) -> sqlite3.Connection:
    uri = f"file:{db_path}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def _table_columns(conn: sqlite3.Connection, table_name: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {str(row["name"]) for row in rows}


def _has_live_calibration_provenance(row: sqlite3.Row | None) -> bool:
    if row is None:
        return False

    keys = set(row.keys())
    if "details_json" in keys:
        details_raw = row["details_json"]
    elif "calibration_details_json" in keys:
        details_raw = row["calibration_details_json"]
    else:
        details_raw = None
    if not details_raw:
        return False

    try:
        details = json.loads(details_raw)
    except json.JSONDecodeError:
        return False

    return details.get("run_mode") == "live" and details.get("live") is True


def inspect_prerequisites(db_path: Path | None = None) -> list[PrerequisiteStatus]:
    path = db_path or get_db_path()
    prerequisites: list[PrerequisiteStatus] = []

    if not path.exists():
        return [
            PrerequisiteStatus(
                name="operational_database",
                passed=False,
                detail=f"database missing: {path}",
                evidence={"db_path": str(path)},
            )
        ]

    try:
        with _read_only_connection(path) as conn:
            if not _table_exists(conn, "classifier_calibration_runs"):
                prerequisites.append(
                    PrerequisiteStatus(
                        name="classifier_calibration",
                        passed=False,
                        detail="classifier_calibration_runs table missing",
                        evidence={},
                    )
                )
            else:
                calibration_columns = _table_columns(conn, "classifier_calibration_runs")
                details_select = (
                    "details_json"
                    if "details_json" in calibration_columns
                    else "NULL AS details_json"
                )
                row = conn.execute(
                    """
                    SELECT calibration_run_id, model_name, ollama_host, threshold,
                           passed, false_positive_rate, false_negative_rate,
                           approved_by_panel_version, created_at,
                           {details_select}
                    FROM classifier_calibration_runs
                    WHERE passed = 1
                      AND approved_by_panel_version = ?
                    ORDER BY created_at DESC, calibration_run_id DESC
                    LIMIT 1
                    """.format(details_select=details_select),
                    (CALIBRATION_WRITE_APPROVAL_TOKEN,),
                ).fetchone()
                has_live_provenance = _has_live_calibration_provenance(row)
                prerequisites.append(
                    PrerequisiteStatus(
                        name="classifier_calibration",
                        passed=row is not None and has_live_provenance,
                        detail=(
                            "approved live passing calibration run present"
                            if row is not None and has_live_provenance
                            else (
                                "approved passing calibration run lacks live provenance"
                                if row is not None
                                else "no approved passing calibration run present"
                            )
                        ),
                        evidence=dict(row) if row is not None else {},
                    )
                )

            if not _table_exists(conn, "model_profile_fingerprints"):
                prerequisites.append(
                    PrerequisiteStatus(
                        name="current_model_fingerprint",
                        passed=False,
                        detail="model_profile_fingerprints table missing",
                        evidence={},
                    )
                )
            else:
                calibration_columns = _table_columns(conn, "classifier_calibration_runs")
                calibration_details_select = (
                    "cc.details_json AS calibration_details_json"
                    if "details_json" in calibration_columns
                    else "NULL AS calibration_details_json"
                )
                row = conn.execute(
                    """
                    SELECT mp.profile_id, mp.profile_label, mp.model_name,
                           mp.ollama_host, mp.thinking_mode,
                           mp.calibration_run_id, mp.is_current,
                           mp.registration_status, mp.registered_at,
                           cc.passed AS calibration_passed,
                           cc.approved_by_panel_version,
                           {calibration_details_select}
                    FROM model_profile_fingerprints mp
                    JOIN classifier_calibration_runs cc
                      ON cc.calibration_run_id = mp.calibration_run_id
                     AND cc.model_name = mp.model_name
                     AND cc.ollama_host = mp.ollama_host
                     AND cc.passed = 1
                     AND cc.approved_by_panel_version = ?
                    WHERE mp.is_current = 1
                      AND mp.registration_status = 'current'
                    ORDER BY mp.registered_at DESC, mp.profile_id DESC
                    LIMIT 1
                    """.format(calibration_details_select=calibration_details_select),
                    (CALIBRATION_WRITE_APPROVAL_TOKEN,),
                ).fetchone()
                has_live_provenance = _has_live_calibration_provenance(row)
                prerequisites.append(
                    PrerequisiteStatus(
                        name="current_model_fingerprint",
                        passed=row is not None and has_live_provenance,
                        detail=(
                            "current model fingerprint present with approved live passing calibration"
                            if row is not None and has_live_provenance
                            else (
                                "current model fingerprint calibration lacks live provenance"
                                if row is not None
                                else "no current model fingerprint with matching approved passing calibration present"
                            )
                        ),
                        evidence=dict(row) if row is not None else {},
                    )
                )

            if not _table_exists(conn, "sessions"):
                prerequisites.append(
                    PrerequisiteStatus(
                        name="safe_pass_readiness",
                        passed=False,
                        detail="sessions table missing",
                        evidence={},
                    )
                )
            else:
                row = conn.execute(
                    """
                    SELECT session_id, safe_pass_enabled, safe_pass_disabled_reason,
                           autonomous_operation_enabled, created_at
                    FROM sessions
                    ORDER BY session_id DESC
                    LIMIT 1
                    """
                ).fetchone()
                safe_pass_enabled = bool(row and int(row["safe_pass_enabled"]) == 1)
                prerequisites.append(
                    PrerequisiteStatus(
                        name="safe_pass_readiness",
                        passed=safe_pass_enabled,
                        detail=(
                            "safe-pass enabled in latest session"
                            if safe_pass_enabled
                            else "safe-pass is not enabled in latest session"
                        ),
                        evidence=dict(row) if row is not None else {},
                    )
                )
    except sqlite3.Error as exc:
        prerequisites.append(
            PrerequisiteStatus(
                name="operational_database_read",
                passed=False,
                detail=f"read-only database inspection failed: {exc}",
                evidence={"db_path": str(path)},
            )
        )

    return prerequisites


def inspect_e2e_operator_approval(db_path: Path | None = None) -> PrerequisiteStatus:
    path = db_path or get_db_path()

    if not path.exists():
        return PrerequisiteStatus(
            name="full_goal_e2e_operator_approval",
            passed=False,
            detail=f"database missing: {path}",
            evidence={"db_path": str(path)},
        )

    try:
        with _read_only_connection(path) as conn:
            if not _table_exists(conn, "session_events"):
                return PrerequisiteStatus(
                    name="full_goal_e2e_operator_approval",
                    passed=False,
                    detail="explicit operator approval for full-goal E2E not supplied",
                    evidence={},
                )

            row = conn.execute(
                """
                SELECT event_id, session_id, event_type, details_json, created_at
                FROM session_events
                WHERE event_type = ?
                ORDER BY event_id DESC
                LIMIT 1
                """,
                (E2E_APPROVAL_EVENT_TYPE,),
            ).fetchone()

            if row is None:
                return PrerequisiteStatus(
                    name="full_goal_e2e_operator_approval",
                    passed=False,
                    detail="explicit operator approval for full-goal E2E not supplied",
                    evidence={},
                )

            details = {}
            try:
                details = json.loads(row["details_json"] or "{}")
            except json.JSONDecodeError:
                details = {}

            token_matches = (
                details.get("approval_token") == E2E_OPERATOR_APPROVAL_TOKEN
            )
            return PrerequisiteStatus(
                name="full_goal_e2e_operator_approval",
                passed=token_matches,
                detail=(
                    "explicit operator approval for full-goal E2E recorded"
                    if token_matches
                    else "explicit operator approval record is invalid"
                ),
                evidence={**dict(row), "details": details},
            )
    except sqlite3.Error as exc:
        return PrerequisiteStatus(
            name="full_goal_e2e_operator_approval",
            passed=False,
            detail=f"read-only operator approval inspection failed: {exc}",
            evidence={"db_path": str(path)},
        )


def tail_lines(value: str, limit: int = 40) -> list[str]:
    lines = value.splitlines()
    return lines[-limit:]


def build_phase7_acceptance_plan(
    *,
    run: bool = False,
    include_e2e: bool = False,
    operator_approved_e2e: bool = False,
    use_stored_e2e_approval: bool = True,
    db_path: Path | None = None,
) -> Phase7AcceptancePlan:
    inventory = audit_phase7_acceptance_inventory()
    tests = canonical_test_paths()
    prerequisites = inspect_prerequisites(db_path)
    prerequisite_blockers = [
        item.detail for item in prerequisites if not item.passed
    ]
    stored_operator_approval = inspect_e2e_operator_approval(db_path)
    operator_approval_passed = operator_approved_e2e or (
        use_stored_e2e_approval and stored_operator_approval.passed
    )
    e2e_present = (ROOT / E2E_TEST_PATH).exists()
    e2e_blockers = list(prerequisite_blockers)

    if not e2e_present:
        e2e_blockers.append(f"{E2E_TEST_PATH} is not present")
    if not operator_approval_passed:
        if use_stored_e2e_approval:
            e2e_blockers.append(stored_operator_approval.detail)
        else:
            e2e_blockers.append("explicit operator approval for full-goal E2E not supplied")

    e2e_ready = not e2e_blockers
    selected_tests = list(tests)
    if include_e2e and e2e_ready:
        selected_tests.append(E2E_TEST_PATH)

    violations: list[dict[str, Any]] = []
    if not inventory.passed:
        violations.extend(inventory.violations)
    for path in tests:
        if not (ROOT / path).exists():
            violations.append(
                {
                    "check": "canonical_test_path",
                    "reason": "mapped_test_missing",
                    "path": path,
                }
            )

    if include_e2e and not e2e_ready:
        violations.append(
            {
                "check": "full_goal_e2e",
                "reason": "e2e_requested_but_blocked",
                "blockers": e2e_blockers,
            }
        )

    command = [sys.executable, "-m", "pytest", *selected_tests, "-v"]
    returncode: int | None = None
    stdout_tail: list[str] = []
    stderr_tail: list[str] = []

    if run and not violations:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        returncode = completed.returncode
        stdout_tail = tail_lines(completed.stdout)
        stderr_tail = tail_lines(completed.stderr)
        if completed.returncode != 0:
            violations.append(
                {
                    "check": "pytest",
                    "reason": "phase7_acceptance_tests_failed",
                    "returncode": completed.returncode,
                }
            )

    executed = returncode is not None

    return Phase7AcceptancePlan(
        passed=not violations,
        acceptance_inventory_passed=inventory.passed,
        canonical_test_paths=tests,
        prerequisites=prerequisites,
        e2e_test_path=E2E_TEST_PATH,
        e2e_test_present=e2e_present,
        e2e_ready=e2e_ready,
        e2e_blockers=e2e_blockers,
        executed=executed,
        command=command,
        returncode=returncode,
        stdout_tail=stdout_tail,
        stderr_tail=stderr_tail,
        violations=violations,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build or run the AXIOM Phase 7B acceptance suite."
    )
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--run", action="store_true", help="Run mapped pytest modules")
    parser.add_argument(
        "--include-e2e",
        action="store_true",
        help="Include full-goal E2E only when all prerequisites are satisfied",
    )
    parser.add_argument(
        "--operator-approved-e2e",
        action="store_true",
        help="Operator approval flag required before full-goal E2E can be selected",
    )
    args = parser.parse_args()

    result = build_phase7_acceptance_plan(
        run=args.run,
        include_e2e=args.include_e2e,
        operator_approved_e2e=args.operator_approved_e2e,
    )
    payload = result.to_dict()

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("AXIOM Phase 7B acceptance runner")
        print("================================")
        print(f"passed: {payload['passed']}")
        print(f"acceptance_inventory_passed: {payload['acceptance_inventory_passed']}")
        print(f"canonical_test_count: {len(payload['canonical_test_paths'])}")
        print(f"executed: {payload['executed']}")
        print(f"returncode: {payload['returncode']}")
        print("")
        print("prerequisites:")
        for item in payload["prerequisites"]:
            print(f"- {item['name']}: {item['passed']} ({item['detail']})")
        print("")
        print(f"e2e_ready: {payload['e2e_ready']}")
        print("e2e blockers:")
        if payload["e2e_blockers"]:
            for blocker in payload["e2e_blockers"]:
                print(f"- {blocker}")
        else:
            print("- none")
        print("")
        print("command:")
        print(" ".join(payload["command"]))
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
