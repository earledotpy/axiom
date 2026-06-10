"""SQLite nonce registry for offline Level 2A replay checks."""

from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
import sqlite3


DEFAULT_NONCE_REGISTRY_PATH = Path(__file__).with_name("nonce_registry.db")
NONCE_REGISTRY_ENV_VAR = "AXIOM_NONCE_REGISTRY_PATH"


def resolve_nonce_registry_path(path: str | os.PathLike[str] | None = None) -> Path:
    if path is not None:
        return Path(path)
    return Path(os.environ.get(NONCE_REGISTRY_ENV_VAR, DEFAULT_NONCE_REGISTRY_PATH))


class NonceRegistry:
    def __init__(self, path: str | os.PathLike[str] | None = None) -> None:
        self.path = resolve_nonce_registry_path(path)

    def register_nonce(self, nonce: str) -> bool:
        if not isinstance(nonce, str) or not nonce:
            raise ValueError("ERR_INVALID_NONCE")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as conn:
            self._ensure_schema(conn)
            try:
                conn.execute(
                    "INSERT INTO nonces (nonce, registered_utc) VALUES (?, ?)",
                    (nonce, _utc_now()),
                )
            except sqlite3.IntegrityError:
                return False
            conn.commit()
        return True

    def nonce_exists(self, nonce: str) -> bool:
        if not isinstance(nonce, str) or not nonce:
            raise ValueError("ERR_INVALID_NONCE")
        if not self.path.exists():
            return False
        with sqlite3.connect(self.path) as conn:
            self._ensure_schema(conn)
            row = conn.execute("SELECT 1 FROM nonces WHERE nonce = ?", (nonce,)).fetchone()
        return row is not None

    @staticmethod
    def _ensure_schema(conn: sqlite3.Connection) -> None:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS nonces (
                nonce TEXT PRIMARY KEY,
                registered_utc TEXT NOT NULL
            )
            """
        )


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
