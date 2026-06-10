"""Offline SQLite relay queue for Level 2A envelope artifacts."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sqlite3
from typing import Any


DEFAULT_RELAY_QUEUE_PATH = Path(__file__).with_name("relay_queue.db")
RELAY_QUEUE_ENV_VAR = "AXIOM_RELAY_QUEUE_PATH"


def resolve_relay_queue_path(path: str | os.PathLike[str] | None = None) -> Path:
    if path is not None:
        return Path(path)
    return Path(os.environ.get(RELAY_QUEUE_ENV_VAR, DEFAULT_RELAY_QUEUE_PATH))


class RelayQueue:
    def __init__(self, path: str | os.PathLike[str] | None = None) -> None:
        self.path = resolve_relay_queue_path(path)

    def enqueue_envelope(self, envelope: dict[str, Any]) -> str:
        envelope_id = _require_envelope_id(envelope)
        payload_json = _json_dumps(envelope)
        with self._connect() as conn:
            self._ensure_schema(conn)
            conn.execute("BEGIN IMMEDIATE")
            conn.execute(
                """
                INSERT INTO relay_queue (envelope_id, payload_json, status, enqueued_at)
                VALUES (?, ?, 'pending', ?)
                """,
                (envelope_id, payload_json, _utc_now()),
            )
            conn.commit()
        return envelope_id

    def peek(self) -> dict[str, Any] | None:
        with self._connect() as conn:
            self._ensure_schema(conn)
            row = conn.execute(
                """
                SELECT payload_json FROM relay_queue
                WHERE status = 'pending'
                ORDER BY id ASC
                LIMIT 1
                """
            ).fetchone()
        return json.loads(row["payload_json"]) if row else None

    def dequeue_envelope(self) -> dict[str, Any] | None:
        with self._connect() as conn:
            self._ensure_schema(conn)
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                """
                SELECT id, payload_json FROM relay_queue
                WHERE status = 'pending'
                ORDER BY id ASC
                LIMIT 1
                """
            ).fetchone()
            if row is None:
                conn.commit()
                return None
            conn.execute(
                "UPDATE relay_queue SET status = 'dequeued' WHERE id = ?",
                (row["id"],),
            )
            conn.commit()
        return json.loads(row["payload_json"])

    def mark_processed(self, envelope_id: str) -> bool:
        if not isinstance(envelope_id, str) or not envelope_id:
            raise ValueError("ERR_INVALID_ENVELOPE_ID")
        with self._connect() as conn:
            self._ensure_schema(conn)
            conn.execute("BEGIN IMMEDIATE")
            cursor = conn.execute(
                """
                UPDATE relay_queue
                SET status = 'processed', processed_at = ?
                WHERE envelope_id = ? AND status IN ('pending', 'dequeued')
                """,
                (_utc_now(), envelope_id),
            )
            conn.commit()
        return cursor.rowcount == 1

    def journal_mode(self) -> str:
        with self._connect() as conn:
            self._ensure_schema(conn)
            row = conn.execute("PRAGMA journal_mode").fetchone()
        return str(row[0]).lower()

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
            CREATE TABLE IF NOT EXISTS relay_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                envelope_id TEXT NOT NULL UNIQUE,
                payload_json TEXT NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('pending', 'dequeued', 'processed')),
                enqueued_at TEXT NOT NULL,
                processed_at TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_relay_queue_status_id
            ON relay_queue(status, id)
            """
        )


def enqueue_envelope(envelope: dict[str, Any], path: str | os.PathLike[str] | None = None) -> str:
    return RelayQueue(path).enqueue_envelope(envelope)


def peek(path: str | os.PathLike[str] | None = None) -> dict[str, Any] | None:
    return RelayQueue(path).peek()


def dequeue_envelope(path: str | os.PathLike[str] | None = None) -> dict[str, Any] | None:
    return RelayQueue(path).dequeue_envelope()


def mark_processed(envelope_id: str, path: str | os.PathLike[str] | None = None) -> bool:
    return RelayQueue(path).mark_processed(envelope_id)


def _require_envelope_id(envelope: dict[str, Any]) -> str:
    if not isinstance(envelope, dict):
        raise ValueError("ERR_ENVELOPE_NOT_OBJECT")
    envelope_id = envelope.get("envelope_id")
    if not isinstance(envelope_id, str) or not envelope_id:
        raise ValueError("ERR_INVALID_ENVELOPE_ID")
    return envelope_id


def _json_dumps(value: dict[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
