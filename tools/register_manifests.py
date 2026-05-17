from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from axiom.core.manifest_binder import ManifestBinder
from axiom.persistence.db import get_connection, init_db

TOOL_VERSION = "register_manifests.v1.13"
POLICY_DIR = ROOT / "axiom" / "policy"
MANIFEST_SCHEMA = POLICY_DIR / "schemas" / "manifest_schema.json"
TOOL_MAP_SCHEMA = POLICY_DIR / "schemas" / "tool_capability_map_schema.json"
TOOL_MAP = POLICY_DIR / "security_artifacts" / "tool_capability_map.json"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def row_for_tool_map() -> dict[str, Any]:
    return {
        "manifest_id": "security.tool_capability_map.v1",
        "manifest_type": "tool_capability_map",
        "relative_path": "policy/security_artifacts/tool_capability_map.json",
        "sha256": sha256_file(TOOL_MAP),
        "schema_version": "axiom.tool_capability_map.v1",
        "manifest_version": "1.0.0",
        "role_name": None,
        "command_name": None,
        "approved_by_panel_version": "v1.11.4",
        "registered_by_tool_version": TOOL_VERSION,
    }


def row_for_manifest(path: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    manifest_type = manifest["manifest_type"]

    if manifest_type == "role":
        rel = f"policy/role_manifests/{path.name}"
        role_name = manifest["role"]["role_name"]
        command_name = None
    elif manifest_type == "operator_control":
        rel = f"policy/operator_control_manifests/{path.name}"
        role_name = None
        command_name = manifest["operator_command"]["command_name"]
    else:
        raise RuntimeError(f"Unsupported manifest_type: {manifest_type}")

    return {
        "manifest_id": manifest["manifest_id"],
        "manifest_type": manifest_type,
        "relative_path": rel,
        "sha256": sha256_file(path),
        "schema_version": manifest["schema_version"],
        "manifest_version": manifest["manifest_version"],
        "role_name": role_name,
        "command_name": command_name,
        "approved_by_panel_version": manifest["approved_by_panel_version"],
        "registered_by_tool_version": TOOL_VERSION,
    }


def build_registration_rows() -> list[dict[str, Any]]:
    binder = ManifestBinder(MANIFEST_SCHEMA, TOOL_MAP_SCHEMA, TOOL_MAP)
    rows = [row_for_tool_map()]

    for subdir in ("role_manifests", "operator_control_manifests"):
        for path in sorted((POLICY_DIR / subdir).glob("*.json")):
            manifest = load_json(path)
            binder.validate_manifest(manifest)
            rows.append(row_for_manifest(path, manifest))

    return rows


def upsert_manifest_fingerprint(conn, row: dict[str, Any]) -> None:
    """
    Update existing rows in place.

    Do not use INSERT OR REPLACE here. REPLACE deletes then reinserts, which
    violates foreign keys from tasks/task_permissions/plan_artifacts that point
    at manifest_fingerprints.manifest_id.
    """
    cur = conn.execute(
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

    if cur.rowcount:
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


def register() -> None:
    init_db()
    rows = build_registration_rows()
    active_ids = [row["manifest_id"] for row in rows]

    with get_connection() as conn:
        conn.execute("BEGIN IMMEDIATE")

        # Deactivate removed artifacts without deleting rows.
        placeholders = ", ".join("?" for _ in active_ids)
        conn.execute(
            f"""
            UPDATE manifest_fingerprints
            SET active = 0
            WHERE manifest_id NOT IN ({placeholders})
            """,
            active_ids,
        )

        for row in rows:
            upsert_manifest_fingerprint(conn, row)

    print(f"registered {len(rows)} active security artifacts")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.parse_args()
    register()
