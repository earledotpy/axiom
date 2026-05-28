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


def upsert_manifest_fingerprint(conn, row: dict[str, object]) -> None:
    cursor = conn.execute(
        """
        UPDATE manifest_fingerprints
        SET manifest_type = :manifest_type,
            relative_path = :relative_path,
            sha256 = :sha256,
            schema_version = :schema_version,
            manifest_version = :manifest_version,
            role_name = :role_name,
            command_name = :command_name,
            approved_by_panel_version = :approved_by_panel_version,
            active = 1,
            registered_by_tool_version = :registered_by_tool_version
        WHERE manifest_id = :manifest_id
        """,
        row,
    )

    if cursor.rowcount:
        return

    conn.execute(
        """
        INSERT INTO manifest_fingerprints
        (manifest_id, manifest_type, relative_path, sha256, schema_version,
         manifest_version, role_name, command_name, approved_by_panel_version,
         active, registered_by_tool_version)
        VALUES
        (:manifest_id, :manifest_type, :relative_path, :sha256, :schema_version,
         :manifest_version, :role_name, :command_name, :approved_by_panel_version,
         1, :registered_by_tool_version)
        """,
        row,
    )


def seed_tool_capability_map_manifest(db_module) -> None:
    """
    Seed the baseline security artifact required by most repository,
    scheduler, gateway, and lifecycle tests using the real artifact SHA.
    """
    with db_module.get_connection() as conn:
        upsert_manifest_fingerprint(
            conn,
            {
                "manifest_id": "security.tool_capability_map.v1",
                "manifest_type": "tool_capability_map",
                "relative_path": "policy/security_artifacts/tool_capability_map.json",
                "sha256": sha256_file(TOOL_CAPABILITY_MAP),
                "schema_version": "axiom.tool_capability_map.v1",
                "manifest_version": "1.0.0",
                "role_name": None,
                "command_name": None,
                "approved_by_panel_version": "test",
                "registered_by_tool_version": "test_fixture",
            },
        )


@pytest.fixture(autouse=True)
def isolate_tool_logs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("tools.snapshot_project_state.LOG_DIR", tmp_path)
    monkeypatch.setattr("tools.generate_handoff.LOG_DIR", tmp_path)
    monkeypatch.setattr("tools.generate_handoff_bundle.LOG_DIR", tmp_path)


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
