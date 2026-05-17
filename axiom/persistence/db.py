from __future__ import annotations

import os
import sqlite3
import sqlite_vec
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

DEFAULT_DB_PATH = r"C:\axiom\axiom.db"
DB_PATH = Path(os.environ.get("AXIOM_DB_PATH", DEFAULT_DB_PATH))
SCHEMA_PATH = Path(__file__).with_name("schema.sql")
SQLITE_CACHE_SIZE_KB = int(os.environ.get("AXIOM_SQLITE_CACHE_SIZE_KB", "32768"))


def apply_pragmas(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = FULL;")
    conn.execute("PRAGMA busy_timeout = 5000;")
    conn.execute(f"PRAGMA cache_size = -{SQLITE_CACHE_SIZE_KB};")


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(
    str(DB_PATH),
    timeout=5.0,
    check_same_thread=False,
    )
    
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    
    conn.row_factory = sqlite3.Row
    apply_pragmas(conn)
    
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
        
        
def init_db() -> None:
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(
            f"Canonical schema file missing: {SCHEMA_PATH}. "
            "Do not initialize AXIOM without schema.sql."
        )
    
    sql = SCHEMA_PATH.read_text(encoding="utf-8")
    
    if "v1.11.4" not in sql:
        raise RuntimeError(
            "Refusing to initialize database: schema.sql does not identify v1.11.4."
        )
    if "tool_capability_map" not in sql:
        raise RuntimeError(
        "Refusing to initialize database: schema.sql lacks v1.11.4 tool_capability_map amendment."
        )
        
    with get_connection() as conn:
        conn.executescript(sql)
        mode = conn.execute("PRAGMA journal_mode;").fetchone()[0]
        if str(mode).lower() != "wal":
            raise RuntimeError(f"WAL mode not enabled; got {mode!r}")
        
        busy_timeout = conn.execute("PRAGMA busy_timeout;").fetchone()[0]
        if int(busy_timeout) != 5000:
            raise RuntimeError(f"SQLite busy_timeout incorrect. Got: {busy_timeout}")
            
        cache_size = conn.execute("PRAGMA cache_size;").fetchone()[0]
        if int(cache_size) != -32768:
            raise RuntimeError(f"SQLite cache_size incorrect. Got: {cache_size}")