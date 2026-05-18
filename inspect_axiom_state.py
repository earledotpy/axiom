import sqlite3

DB = r"C:\axiom\axiom.db"

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

print("RUNNING TASKS")
rows = conn.execute("""
SELECT
    task_id,
    session_id,
    chain_id,
    task_class,
    task_type,
    status,
    manifest_id,
    started_at,
    completed_at
FROM tasks
WHERE status = 'running'
ORDER BY task_id;
""").fetchall()

if not rows:
    print("none")
else:
    for row in rows:
        print(dict(row))

print()
print("LATEST SCHEDULER HEARTBEATS")
rows = conn.execute("""
SELECT
    heartbeat_id,
    session_id,
    active_task_id,
    status,
    last_freshness_at
FROM scheduler_heartbeat
ORDER BY heartbeat_id DESC
LIMIT 5;
""").fetchall()

if not rows:
    print("none")
else:
    for row in rows:
        print(dict(row))

conn.close()
