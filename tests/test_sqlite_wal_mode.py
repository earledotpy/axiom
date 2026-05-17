from axiom.persistence.db import get_connection, init_db


def test_sqlite_wal_mode_and_pragmas():
    init_db()
    with get_connection() as conn:
        assert conn.execute("PRAGMA journal_mode;").fetchone()[0].lower() == "wal"
        assert conn.execute("PRAGMA synchronous;").fetchone()[0] == 2
        assert conn.execute("PRAGMA busy_timeout;").fetchone()[0] >= 5000
        assert conn.execute("PRAGMA foreign_keys;").fetchone()[0] == 1
        assert conn.execute("PRAGMA cache_size;").fetchone()[0] < 0