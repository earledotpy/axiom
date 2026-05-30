"""
IPC SQLite index — called from PowerShell as a CLI helper.
Markdown files remain the human-readable source of truth; this DB is the
canonical deduplication and history layer.

Usage:
  python ipc/ipc_db.py write         --from X --to Y --subject Z --time T --body "..." [--type ai-prompt] [--conversation-id ID]
  python ipc/ipc_db.py pending       --agent claude
  python ipc/ipc_db.py done          --id 42
  python ipc/ipc_db.py history       --agent claude [--limit 50]
  python ipc/ipc_db.py mark-retry    --id 42
  python ipc/ipc_db.py recent-check  --from X --to Y --subject S --window 60
  python ipc/ipc_db.py is-agent-blocked     --agent codex
  python ipc/ipc_db.py set-agent-blocked    --agent codex --until ISO8601 --reason "..."
  python ipc/ipc_db.py set-agent-available  --agent codex
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
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    from_agent       TEXT    NOT NULL,
    to_agent         TEXT    NOT NULL,
    time             TEXT    NOT NULL,
    subject          TEXT    NOT NULL,
    body             TEXT    NOT NULL,
    processed        INTEGER NOT NULL DEFAULT 0,
    type             TEXT    NOT NULL DEFAULT 'ai-prompt',
    retry_count      INTEGER NOT NULL DEFAULT 0,
    dead_letter      INTEGER NOT NULL DEFAULT 0,
    conversation_id  TEXT,
    response_pending INTEGER NOT NULL DEFAULT 0,
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_dedup
    ON messages(from_agent, to_agent, time, subject);
CREATE INDEX IF NOT EXISTS idx_pending
    ON messages(to_agent, processed);
"""

AGENT_AVAIL_DDL = """
CREATE TABLE IF NOT EXISTS agent_availability (
    agent         TEXT PRIMARY KEY,
    available     INTEGER NOT NULL DEFAULT 1,
    blocked_until TEXT,
    reason        TEXT
);
"""

# Columns added after initial schema — migrated on every startup via ALTER TABLE
_NEW_COLS: dict[str, str] = {
    "type":             "TEXT NOT NULL DEFAULT 'ai-prompt'",
    "retry_count":      "INTEGER NOT NULL DEFAULT 0",
    "dead_letter":      "INTEGER NOT NULL DEFAULT 0",
    "conversation_id":  "TEXT",
    "response_pending": "INTEGER NOT NULL DEFAULT 0",
}


def _migrate_schema(conn: sqlite3.Connection) -> None:
    existing = {row[1] for row in conn.execute("PRAGMA table_info(messages)").fetchall()}
    for col, defn in _NEW_COLS.items():
        if col not in existing:
            conn.execute(f"ALTER TABLE messages ADD COLUMN {col} {defn}")
    conn.executescript(AGENT_AVAIL_DDL)
    conn.commit()


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(DDL)
    _migrate_schema(conn)
    return conn


def cmd_write(args: argparse.Namespace) -> None:
    msg_type = getattr(args, "type", "ai-prompt") or "ai-prompt"
    conv_id = getattr(args, "conversation_id", None)
    with get_conn() as conn:
        try:
            cur = conn.execute(
                "INSERT OR IGNORE INTO messages "
                "(from_agent, to_agent, time, subject, body, type, conversation_id) "
                "VALUES (?,?,?,?,?,?,?)",
                (args.from_, args.to, args.time, args.subject, args.body, msg_type, conv_id),
            )
            conn.commit()
            row_id = cur.lastrowid if cur.lastrowid else -1
        except sqlite3.IntegrityError:
            row_id = -1  # duplicate — already indexed
    print(json.dumps({"id": row_id}))


def cmd_pending(args: argparse.Namespace) -> None:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, from_agent, to_agent, time, subject, body, "
            "type, retry_count, dead_letter, conversation_id, response_pending "
            "FROM messages WHERE to_agent=? AND processed=0 AND dead_letter=0 ORDER BY id",
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
            "SELECT id, from_agent, to_agent, time, subject, body, processed, "
            "type, retry_count, dead_letter, conversation_id, created_at "
            "FROM messages WHERE to_agent=? OR from_agent=? "
            "ORDER BY id DESC LIMIT ?",
            (args.agent, args.agent, limit),
        ).fetchall()
    print(json.dumps([dict(r) for r in rows]))


def cmd_mark_retry(args: argparse.Namespace) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE messages SET retry_count = retry_count + 1 WHERE id=?",
            (args.id,),
        )
        row = conn.execute(
            "SELECT retry_count FROM messages WHERE id=?", (args.id,)
        ).fetchone()
        if row and row["retry_count"] >= 3:
            conn.execute("UPDATE messages SET dead_letter=1 WHERE id=?", (args.id,))
        conn.commit()
    print(json.dumps({"ok": True}))


def cmd_recent_check(args: argparse.Namespace) -> None:
    window = getattr(args, "window", 60) or 60
    with get_conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS cnt FROM messages "
            "WHERE from_agent=? AND to_agent=? AND subject=? AND processed=1 "
            "AND datetime(created_at) >= datetime('now', ? || ' seconds')",
            (args.from_, args.to, args.subject, f"-{window}"),
        ).fetchone()
    count = row["cnt"] if row else 0
    # exit 0 = dupe detected (caller should skip); exit 1 = clear to process
    sys.exit(0 if count > 0 else 1)


def cmd_is_agent_blocked(args: argparse.Namespace) -> None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT blocked_until FROM agent_availability WHERE agent=?",
            (args.agent,),
        ).fetchone()
    if row and row["blocked_until"]:
        # Compare as strings — ISO8601 sorts lexicographically
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        if row["blocked_until"] > now:
            sys.exit(0)  # blocked
    sys.exit(1)  # available


def cmd_set_agent_blocked(args: argparse.Namespace) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO agent_availability(agent, available, blocked_until, reason) "
            "VALUES(?,0,?,?) ON CONFLICT(agent) DO UPDATE SET "
            "available=0, blocked_until=excluded.blocked_until, reason=excluded.reason",
            (args.agent, args.until, args.reason),
        )
        conn.commit()
    print(json.dumps({"ok": True}))


def cmd_set_agent_available(args: argparse.Namespace) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO agent_availability(agent, available, blocked_until, reason) "
            "VALUES(?,1,NULL,NULL) ON CONFLICT(agent) DO UPDATE SET "
            "available=1, blocked_until=NULL, reason=NULL",
            (args.agent,),
        )
        conn.commit()
    print(json.dumps({"ok": True}))


def main() -> None:
    parser = argparse.ArgumentParser(description="AXIOM IPC SQLite index")
    sub = parser.add_subparsers(dest="cmd", required=True)

    w = sub.add_parser("write")
    w.add_argument("--from", dest="from_", required=True)
    w.add_argument("--to",               required=True)
    w.add_argument("--subject",          required=True)
    w.add_argument("--time",             required=True)
    w.add_argument("--body",             required=True)
    w.add_argument("--type",             default="ai-prompt")
    w.add_argument("--conversation-id",  dest="conversation_id", default=None)

    p = sub.add_parser("pending")
    p.add_argument("--agent", required=True)

    d = sub.add_parser("done")
    d.add_argument("--id", type=int, required=True)

    h = sub.add_parser("history")
    h.add_argument("--agent", required=True)
    h.add_argument("--limit", type=int, default=50)

    mr = sub.add_parser("mark-retry")
    mr.add_argument("--id", type=int, required=True)

    rc = sub.add_parser("recent-check")
    rc.add_argument("--from", dest="from_", required=True)
    rc.add_argument("--to",               required=True)
    rc.add_argument("--subject",          required=True)
    rc.add_argument("--window", type=int, default=60)

    iab = sub.add_parser("is-agent-blocked")
    iab.add_argument("--agent", required=True)

    sab = sub.add_parser("set-agent-blocked")
    sab.add_argument("--agent",  required=True)
    sab.add_argument("--until",  required=True)
    sab.add_argument("--reason", required=True)

    saa = sub.add_parser("set-agent-available")
    saa.add_argument("--agent", required=True)

    args = parser.parse_args()
    {
        "write":              cmd_write,
        "pending":            cmd_pending,
        "done":               cmd_done,
        "history":            cmd_history,
        "mark-retry":         cmd_mark_retry,
        "recent-check":       cmd_recent_check,
        "is-agent-blocked":   cmd_is_agent_blocked,
        "set-agent-blocked":  cmd_set_agent_blocked,
        "set-agent-available": cmd_set_agent_available,
    }[args.cmd](args)


if __name__ == "__main__":
    main()
