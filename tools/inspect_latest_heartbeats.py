import sqlite3

DB = r"C:\axiom\axiom.db"
SESSION_ID = 4444

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

print("LATEST HEARTBEATS FOR SESSION", SESSION_ID)
rows = conn.execute("""
SELECT *
FROM scheduler_heartbeat
WHERE session_id = ?
ORDER BY heartbeat_id DESC
LIMIT 5;
""", (SESSION_ID,)).fetchall()

if not rows:
    print("none")
else:
    for row in rows:
        print(dict(row))

conn.close()
