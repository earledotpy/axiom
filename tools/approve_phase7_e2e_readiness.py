from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = ROOT / "axiom.db"

sys.path.insert(0, str(ROOT))

from tools.run_phase7_acceptance import (  # noqa: E402
    CALIBRATION_WRITE_APPROVAL_TOKEN,
    E2E_APPROVAL_EVENT_TYPE,
    E2E_OPERATOR_APPROVAL_TOKEN,
    E2E_TEST_PATH,
    inspect_prerequisites,
)


TOOL_VERSION = "approve_phase7_e2e_readiness.v1"


@dataclass(frozen=True)
class Phase7ReadinessApprovalResult:
    passed: bool
    db_path: str
    session_id: int | None
    safe_pass_enabled: bool
    e2e_approval_recorded: bool
    prerequisites: list[dict[str, Any]]
    event_ids: dict[str, int]
    violations: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def get_db_path() -> Path:
    return Path(os.environ.get("AXIOM_DB_PATH", str(DEFAULT_DB_PATH)))


def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path), timeout=5.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn


def _table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def _latest_session(conn: sqlite3.Connection) -> sqlite3.Row | None:
    if not _table_exists(conn, "sessions"):
        return None
    return conn.execute(
        """
        SELECT session_id, safe_pass_enabled, safe_pass_disabled_reason,
               autonomous_operation_enabled
        FROM sessions
        ORDER BY session_id DESC
        LIMIT 1
        """
    ).fetchone()


def _current_approved_profile(conn: sqlite3.Connection) -> sqlite3.Row | None:
    return conn.execute(
        """
        SELECT mp.profile_id, mp.profile_label, mp.model_name, mp.ollama_host,
               mp.thinking_mode, mp.thinking_mode_rule_version,
               mp.calibration_run_id, cc.approved_by_panel_version
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
        """,
        (CALIBRATION_WRITE_APPROVAL_TOKEN,),
    ).fetchone()


def _insert_session_event(
    conn: sqlite3.Connection,
    *,
    session_id: int,
    event_type: str,
    details: dict[str, Any],
) -> int:
    cur = conn.execute(
        """
        INSERT INTO session_events (session_id, event_type, details_json)
        VALUES (?, ?, ?)
        """,
        (session_id, event_type, json.dumps(details, sort_keys=True)),
    )
    return int(cur.lastrowid)


def _insert_security_event(
    conn: sqlite3.Connection,
    *,
    session_id: int,
    event_type: str,
    reason: str,
    details: dict[str, Any],
) -> int:
    cur = conn.execute(
        """
        INSERT INTO security_events
        (session_id, task_id, event_type, reason, severity, details_json)
        VALUES (?, NULL, ?, ?, 'info', ?)
        """,
        (session_id, event_type, reason, json.dumps(details, sort_keys=True)),
    )
    return int(cur.lastrowid)


def approve_phase7_e2e_readiness(
    *,
    approval_token: str,
    enable_safe_pass: bool,
    approve_e2e: bool,
    operator_id: str = "Jeremy",
    db_path: Path | None = None,
) -> Phase7ReadinessApprovalResult:
    path = db_path or get_db_path()
    violations: list[dict[str, Any]] = []
    event_ids: dict[str, int] = {}
    session_id: int | None = None
    safe_pass_enabled = False
    e2e_approval_recorded = False

    if approval_token != E2E_OPERATOR_APPROVAL_TOKEN:
        violations.append(
            {
                "check": "operator_approval_token",
                "reason": "invalid_phase7_e2e_approval_token",
            }
        )

    if not enable_safe_pass:
        violations.append(
            {
                "check": "safe_pass_readiness",
                "reason": "enable_safe_pass_flag_required",
            }
        )

    if not approve_e2e:
        violations.append(
            {
                "check": "full_goal_e2e_operator_approval",
                "reason": "approve_e2e_flag_required",
            }
        )

    if not path.exists():
        violations.append(
            {
                "check": "operational_database",
                "reason": "database_missing",
                "db_path": str(path),
            }
        )
        return Phase7ReadinessApprovalResult(
            passed=False,
            db_path=str(path),
            session_id=None,
            safe_pass_enabled=False,
            e2e_approval_recorded=False,
            prerequisites=[],
            event_ids={},
            violations=violations,
        )

    prerequisite_statuses = inspect_prerequisites(path)
    prerequisite_map = {item.name: item for item in prerequisite_statuses}
    for name in ("classifier_calibration", "current_model_fingerprint"):
        status = prerequisite_map.get(name)
        if status is None or not status.passed:
            violations.append(
                {
                    "check": name,
                    "reason": "phase7_prerequisite_not_satisfied",
                    "detail": status.detail if status else "missing prerequisite status",
                }
            )

    if not (ROOT / E2E_TEST_PATH).exists():
        violations.append(
            {
                "check": "full_goal_e2e_test",
                "reason": "e2e_test_missing",
                "path": E2E_TEST_PATH,
            }
        )

    try:
        with _connect(path) as conn:
            required_tables = {
                "sessions",
                "session_events",
                "security_events",
                "classifier_calibration_runs",
                "model_profile_fingerprints",
            }
            for table_name in sorted(required_tables):
                if not _table_exists(conn, table_name):
                    violations.append(
                        {
                            "check": "operational_database_schema",
                            "reason": "required_table_missing",
                            "table": table_name,
                        }
                    )

            session = _latest_session(conn)
            if session is None:
                violations.append(
                    {
                        "check": "latest_session",
                        "reason": "latest_session_missing",
                    }
                )
            else:
                session_id = int(session["session_id"])
                if int(session["autonomous_operation_enabled"]) != 0:
                    violations.append(
                        {
                            "check": "non_autonomous_boundary",
                            "reason": "autonomous_operation_already_enabled",
                            "session_id": session_id,
                        }
                    )

            profile = (
                _current_approved_profile(conn)
                if not any(
                    item.get("check") == "operational_database_schema"
                    for item in violations
                )
                else None
            )

            if violations:
                return Phase7ReadinessApprovalResult(
                    passed=False,
                    db_path=str(path),
                    session_id=session_id,
                    safe_pass_enabled=False,
                    e2e_approval_recorded=False,
                    prerequisites=[item.to_dict() for item in prerequisite_statuses],
                    event_ids={},
                    violations=violations,
                )

            assert session_id is not None
            assert profile is not None

            material = {
                "operator_id": operator_id,
                "approval_token": approval_token,
                "tool_version": TOOL_VERSION,
                "calibration_run_id": profile["calibration_run_id"],
                "profile_id": int(profile["profile_id"]),
                "profile_label": profile["profile_label"],
                "model_name": profile["model_name"],
                "ollama_host": profile["ollama_host"],
                "thinking_mode": profile["thinking_mode"],
                "thinking_mode_rule_version": profile["thinking_mode_rule_version"],
                "approved_by_panel_version": profile["approved_by_panel_version"],
                "e2e_test_path": E2E_TEST_PATH,
                "autonomous_operation_enabled": False,
                "final_e2e_executed": False,
            }

            conn.execute("BEGIN IMMEDIATE")
            conn.execute(
                """
                UPDATE sessions
                SET safe_pass_enabled = 1,
                    safe_pass_disabled_reason = NULL,
                    safe_pass_disabled_at = NULL,
                    safe_pass_alert_sent = 0
                WHERE session_id = ?
                """,
                (session_id,),
            )
            event_ids["safe_pass_readiness"] = _insert_session_event(
                conn,
                session_id=session_id,
                event_type="phase7_safe_pass_readiness_enabled",
                details=material,
            )
            event_ids["full_goal_e2e_approval"] = _insert_session_event(
                conn,
                session_id=session_id,
                event_type=E2E_APPROVAL_EVENT_TYPE,
                details=material,
            )
            event_ids["security_event"] = _insert_security_event(
                conn,
                session_id=session_id,
                event_type="phase7_e2e_readiness_approved",
                reason="operator_approved_phase7_e2e_readiness_without_autonomous_enablement",
                details=material,
            )

            safe_pass_enabled = True
            e2e_approval_recorded = True
    except sqlite3.Error as exc:
        violations.append(
            {
                "check": "operational_database_write",
                "reason": "readiness_approval_failed",
                "error": str(exc),
            }
        )

    return Phase7ReadinessApprovalResult(
        passed=not violations,
        db_path=str(path),
        session_id=session_id,
        safe_pass_enabled=safe_pass_enabled,
        e2e_approval_recorded=e2e_approval_recorded,
        prerequisites=[item.to_dict() for item in prerequisite_statuses],
        event_ids=event_ids,
        violations=violations,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Approve AXIOM Phase 7 full-goal E2E readiness material."
    )
    parser.add_argument("--approval-token", required=True)
    parser.add_argument("--enable-safe-pass", action="store_true")
    parser.add_argument("--approve-e2e", action="store_true")
    parser.add_argument("--operator-id", default="Jeremy")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = approve_phase7_e2e_readiness(
        approval_token=args.approval_token,
        enable_safe_pass=args.enable_safe_pass,
        approve_e2e=args.approve_e2e,
        operator_id=args.operator_id,
    )
    payload = result.to_dict()

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("AXIOM Phase 7 E2E readiness approval")
        print("====================================")
        print(f"passed: {payload['passed']}")
        print(f"session_id: {payload['session_id']}")
        print(f"safe_pass_enabled: {payload['safe_pass_enabled']}")
        print(f"e2e_approval_recorded: {payload['e2e_approval_recorded']}")
        print("violations:")
        if payload["violations"]:
            for violation in payload["violations"]:
                print(f"- {violation['check']}: {violation['reason']}")
        else:
            print("- none")

    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
