import sqlite3

DB = r"C:\axiom\axiom.db"

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

print("scheduler_heartbeat columns")
rows = conn.execute("PRAGMA table_info(scheduler_heartbeat);").fetchall()
for row in rows:
    print(dict(row))

conn.close()
