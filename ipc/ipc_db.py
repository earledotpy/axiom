"""
IPC SQLite index — called from PowerShell as a CLI helper.
Markdown files remain the human-readable source of truth; this DB is the
canonical deduplication and history layer.

Usage:
  python ipc/ipc_db.py write   --from X --to Y --subject Z --time T --body "..."
  python ipc/ipc_db.py pending --agent claude
  python ipc/ipc_db.py done    --id 42
  python ipc/ipc_db.py history --agent claude [--limit 50]
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent / "ipc_messages.db"

DDL = """
CREATE TABLE IF NOT EXISTS messages (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    from_agent  TEXT    NOT NULL,
    to_agent    TEXT    NOT NULL,
    time        TEXT    NOT NULL,
    subject     TEXT    NOT NULL,
    body        TEXT    NOT NULL,
    processed   INTEGER NOT NULL DEFAULT 0,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_dedup
    ON messages(from_agent, to_agent, time, subject);
CREATE INDEX IF NOT EXISTS idx_pending
    ON messages(to_agent, processed);
"""


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(DDL)
    return conn


def cmd_write(args: argparse.Namespace) -> None:
    with get_conn() as conn:
        try:
            cur = conn.execute(
                "INSERT OR IGNORE INTO messages "
                "(from_agent, to_agent, time, subject, body) VALUES (?,?,?,?,?)",
                (args.from_, args.to, args.time, args.subject, args.body),
            )
            conn.commit()
            row_id = cur.lastrowid if cur.lastrowid else -1
        except sqlite3.IntegrityError:
            row_id = -1  # duplicate — already indexed
    print(json.dumps({"id": row_id}))


def cmd_pending(args: argparse.Namespace) -> None:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, from_agent, to_agent, time, subject, body "
            "FROM messages WHERE to_agent=? AND processed=0 ORDER BY id",
            (args.agent,),
        ).fetchall()
    print(json.dumps([dict(r) for r in rows]))


def cmd_done(args: argparse.Namespace) -> None:
    with get_conn() as conn:
        conn.execute("UPDATE messages SET processed=1 WHERE id=?", (args.id,))
        conn.commit()
    print(json.dumps({"ok": True}))


def cmd_history(args: argparse.Namespace) -> None:
    limit = getattr(args, "limit", 50) or 50
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, from_agent, to_agent, time, subject, body, processed, created_at "
            "FROM messages WHERE to_agent=? OR from_agent=? "
            "ORDER BY id DESC LIMIT ?",
            (args.agent, args.agent, limit),
        ).fetchall()
    print(json.dumps([dict(r) for r in rows]))


def main() -> None:
    parser = argparse.ArgumentParser(description="AXIOM IPC SQLite index")
    sub = parser.add_subparsers(dest="cmd", required=True)

    w = sub.add_parser("write")
    w.add_argument("--from", dest="from_", required=True)
    w.add_argument("--to",      required=True)
    w.add_argument("--subject", required=True)
    w.add_argument("--time",    required=True)
    w.add_argument("--body",    required=True)

    p = sub.add_parser("pending")
    p.add_argument("--agent", required=True)

    d = sub.add_parser("done")
    d.add_argument("--id", type=int, required=True)

    h = sub.add_parser("history")
    h.add_argument("--agent", required=True)
    h.add_argument("--limit", type=int, default=50)

    args = parser.parse_args()
    {"write": cmd_write, "pending": cmd_pending,
     "done": cmd_done, "history": cmd_history}[args.cmd](args)


if __name__ == "__main__":
    main()
