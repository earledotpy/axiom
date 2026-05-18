from __future__ import annotations

import hashlib
import importlib
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
TOOL_CAPABILITY_MAP = (
    ROOT / "axiom" / "policy" / "security_artifacts" / "tool_capability_map.json"
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def seed_tool_capability_map_manifest(db_module) -> None:
    """
    Seed the baseline security artifact required by most repository,
    scheduler, gateway, and lifecycle tests using the real artifact SHA.
    """
    with db_module.get_connection() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO manifest_fingerprints
            (manifest_id, manifest_type, relative_path, sha256, schema_version,
             manifest_version, role_name, command_name, approved_by_panel_version,
             active, registered_by_tool_version)
            VALUES (?, ?, ?, ?, ?, ?, NULL, NULL, ?, 1, ?)
            """,
            (
                "security.tool_capability_map.v1",
                "tool_capability_map",
                "policy/security_artifacts/tool_capability_map.json",
                sha256_file(TOOL_CAPABILITY_MAP),
                "axiom.tool_capability_map.v1",
                "1.0.0",
                "test",
                "test_fixture",
            ),
        )


@pytest.fixture(autouse=True)
def isolate_axiom_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """
    Prevent tests from writing to the real operational database.

    Each test receives a fresh initialized AXIOM database and the baseline
    tool-capability-map manifest row required by FK-bound test data.
    """
    test_db = tmp_path / "axiom_test.db"
    monkeypatch.setenv("AXIOM_DB_PATH", str(test_db))

    import axiom.persistence.db as db

    importlib.reload(db)
    db.init_db()
    seed_tool_capability_map_manifest(db)

    yield

    importlib.reload(db)