import sqlite3

DB = r"C:\axiom\axiom.db"

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

latest_session = conn.execute("""
SELECT session_id, created_at, scheduler_status, autonomous_operation_enabled, safe_pass_enabled
FROM sessions
ORDER BY session_id DESC
LIMIT 1;
""").fetchone()

print("LATEST SESSION")
print(dict(latest_session) if latest_session else "none")

if latest_session:
    sid = latest_session["session_id"]

    print()
    print("RUNNING TASKS IN LATEST SESSION")
    rows = conn.execute("""
    SELECT task_id, session_id, chain_id, task_class, task_type, status, manifest_id, started_at, completed_at
    FROM tasks
    WHERE session_id = ? AND status = 'running'
    ORDER BY task_id;
    """, (sid,)).fetchall()

    if not rows:
        print("none")
    else:
        for row in rows:
            print(dict(row))

    print()
    print("LATEST HEARTBEATS FOR LATEST SESSION")
    rows = conn.execute("""
    SELECT heartbeat_id, session_id, active_task_id, status, last_freshness_at
    FROM scheduler_heartbeat
    WHERE session_id = ?
    ORDER BY heartbeat_id DESC
    LIMIT 5;
    """, (sid,)).fetchall()

    if not rows:
        print("none")
    else:
        for row in rows:
            print(dict(row))

print()
print("GLOBAL RUNNING TASK COUNT")
row = conn.execute("""
SELECT COUNT(*) AS running_count
FROM tasks
WHERE status = 'running';
""").fetchone()
print(dict(row))

print()
print("RUNNING TASKS BY SESSION, LATEST 20 SESSIONS ONLY")
rows = conn.execute("""
SELECT session_id, COUNT(*) AS running_count
FROM tasks
WHERE status = 'running'
GROUP BY session_id
ORDER BY session_id DESC
LIMIT 20;
""").fetchall()

if not rows:
    print("none")
else:
    for row in rows:
        print(dict(row))

conn.close()
