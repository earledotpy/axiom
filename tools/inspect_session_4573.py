import sqlite3

DB = r"C:\axiom\axiom.db"
SESSION_ID = 4573

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

print("RUNNING TASKS IN SESSION", SESSION_ID)
rows = conn.execute("""
SELECT task_id, session_id, chain_id, task_class, task_type, status,
       manifest_id, started_at, completed_at
FROM tasks
WHERE session_id = ? AND status = 'running'
ORDER BY task_id;
""", (SESSION_ID,)).fetchall()

for row in rows:
    print(dict(row))

print()
print("LATEST HEARTBEATS FOR SESSION", SESSION_ID)
rows = conn.execute("""
SELECT *
FROM scheduler_heartbeat
WHERE session_id = ?
ORDER BY heartbeat_id DESC
LIMIT 5;
""", (SESSION_ID,)).fetchall()

for row in rows:
    print(dict(row))

conn.close()
