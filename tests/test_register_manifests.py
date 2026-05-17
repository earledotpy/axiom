from pathlib import Path
import sys

from axiom.core.boot_verifier import sha256_file, verify_boot_manifests
from axiom.persistence.db import get_connection
from axiom.persistence.repositories import create_session, create_task, get_task

ROOT = Path(r"C:\axiom")
sys.path.insert(0, str(ROOT / "tools"))

from register_manifests import register


TOOL_MAP_MANIFEST_ID = "security.tool_capability_map.v1"
TOOL_MAP_PATH = Path(r"C:\axiom\axiom\policy\security_artifacts\tool_capability_map.json")


def test_register_manifests_repairs_sha_without_breaking_task_foreign_key():
    session_id = create_session(operator_id="register-manifests-fk-test")

    task_id = create_task(
        session_id=session_id,
        chain_id="chain-register-manifests-fk-test",
        task_class="system_maintenance",
        task_type="register_manifests_fk_test",
        manifest_id=TOOL_MAP_MANIFEST_ID,
    )

    actual_sha = sha256_file(TOOL_MAP_PATH)

    with get_connection() as conn:
        conn.execute(
            """
            UPDATE manifest_fingerprints
            SET sha256 = ?
            WHERE manifest_id = ? AND active = 1
            """,
            ("0" * 64, TOOL_MAP_MANIFEST_ID),
        )

    register()

    task = get_task(task_id)

    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT sha256, active, registered_by_tool_version
            FROM manifest_fingerprints
            WHERE manifest_id = ?
            """,
            (TOOL_MAP_MANIFEST_ID,),
        ).fetchone()

    assert task is not None
    assert task["manifest_id"] == TOOL_MAP_MANIFEST_ID
    assert row["sha256"] == actual_sha
    assert row["active"] == 1
    assert row["registered_by_tool_version"] == "register_manifests.v1.13"


def test_register_manifests_leaves_boot_verification_passing():
    register()

    result = verify_boot_manifests()

    assert TOOL_MAP_MANIFEST_ID in result.manifest_ids
