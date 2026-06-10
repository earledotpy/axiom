"""Offline SQLite dead-letter log for rejected Level 2A artifacts."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sqlite3
from typing import Any
import uuid


DEFAULT_DEAD_LETTER_PATH = Path(__file__).with_name("dead_letter.db")
DEAD_LETTER_ENV_VAR = "AXIOM_DEAD_LETTER_PATH"


def resolve_dead_letter_path(path: str | os.PathLike[str] | None = None) -> Path:
    if path is not None:
        return Path(path)
    return Path(os.environ.get(DEAD_LETTER_ENV_VAR, DEFAULT_DEAD_LETTER_PATH))


class DeadLetterLog:
    def __init__(self, path: str | os.PathLike[str] | None = None) -> None:
        self.path = resolve_dead_letter_path(path)

    def log_dead_letter(
        self,
        *,
        rejection_code: str,
        failure_reason: str,
        raw_payload: Any,
        actor: str,
        original_envelope_id: str | None = None,
        mandate_id: str | None = None,
        docket_id: str | None = None,
    ) -> dict[str, Any]:
        _require_non_empty(rejection_code, "ERR_INVALID_REJECTION_CODE")
        _require_non_empty(failure_reason, "ERR_INVALID_FAILURE_REASON")
        _require_non_empty(actor, "ERR_INVALID_ACTOR")
        record = {
            "dead_letter_id": "DL-" + str(uuid.uuid4()),
            "rejection_code": rejection_code,
            "failure_reason": failure_reason,
            "raw_payload": raw_payload,
            "actor": actor,
            "received_at": _utc_now(),
        }
        if original_envelope_id:
            record["original_envelope_id"] = original_envelope_id
        if mandate_id:
            record["mandate_id"] = mandate_id
        if docket_id:
            record["docket_id"] = docket_id

        with self._connect() as conn:
            self._ensure_schema(conn)
            conn.execute("BEGIN IMMEDIATE")
            conn.execute(
                """
                INSERT INTO dead_letters (
                    dead_letter_id, rejection_code, failure_reason, raw_payload,
                    actor, received_at, original_envelope_id, mandate_id, docket_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["dead_letter_id"],
                    rejection_code,
                    failure_reason,
                    _json_dumps(raw_payload),
                    actor,
                    record["received_at"],
                    original_envelope_id,
                    mandate_id,
                    docket_id,
                ),
            )
            conn.commit()
        return record

    def list_dead_letters(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            self._ensure_schema(conn)
            rows = conn.execute(
                """
                SELECT dead_letter_id, rejection_code, failure_reason, raw_payload,
                       actor, received_at, original_envelope_id, mandate_id, docket_id
                FROM dead_letters
                ORDER BY id ASC
                """
            ).fetchall()
        records = []
        for row in rows:
            record = dict(row)
            record["raw_payload"] = json.loads(record["raw_payload"])
            for key in ("original_envelope_id", "mandate_id", "docket_id"):
                if record[key] is None:
                    del record[key]
            records.append(record)
        return records

    def _connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.path, timeout=30.0, isolation_level=None)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    @staticmethod
    def _ensure_schema(conn: sqlite3.Connection) -> None:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS dead_letters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dead_letter_id TEXT NOT NULL UNIQUE,
                rejection_code TEXT NOT NULL,
                failure_reason TEXT NOT NULL,
                raw_payload TEXT NOT NULL,
                actor TEXT NOT NULL,
                received_at TEXT NOT NULL,
                original_envelope_id TEXT,
                mandate_id TEXT,
                docket_id TEXT
            )
            """
        )


def log_dead_letter(
    *,
    rejection_code: str,
    failure_reason: str,
    raw_payload: Any,
    actor: str,
    path: str | os.PathLike[str] | None = None,
    original_envelope_id: str | None = None,
    mandate_id: str | None = None,
    docket_id: str | None = None,
) -> dict[str, Any]:
    return DeadLetterLog(path).log_dead_letter(
        rejection_code=rejection_code,
        failure_reason=failure_reason,
        raw_payload=raw_payload,
        actor=actor,
        original_envelope_id=original_envelope_id,
        mandate_id=mandate_id,
        docket_id=docket_id,
    )


def list_dead_letters(path: str | os.PathLike[str] | None = None) -> list[dict[str, Any]]:
    return DeadLetterLog(path).list_dead_letters()


def _require_non_empty(value: str, error_code: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(error_code)


def _json_dumps(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
