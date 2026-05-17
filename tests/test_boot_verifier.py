import json
from pathlib import Path

import pytest

from axiom.core.boot_verifier import BootVerificationError, verify_boot_manifests
from axiom.persistence.db import get_connection
from axiom.persistence.repositories import get_active_manifest_fingerprints


def test_boot_verifier_passes_for_registered_tool_capability_map():
    result = verify_boot_manifests()

    assert result.verified_count >= 1
    assert "security.tool_capability_map.v1" in result.manifest_ids


def test_boot_verifier_logs_info_event_on_success():
    verify_boot_manifests()

    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT *
            FROM security_events
            WHERE event_type = 'manifest_boot_verification_passed'
            ORDER BY event_id DESC
            LIMIT 1
            """
        ).fetchone()

    assert row is not None
    assert row["severity"] == "info"


def test_boot_verifier_fails_on_sha_mismatch_and_logs_critical():
    rows = get_active_manifest_fingerprints()
    target = next(row for row in rows if row["manifest_id"] == "security.tool_capability_map.v1")
    original_sha = target["sha256"]

    with get_connection() as conn:
        conn.execute(
            """
            UPDATE manifest_fingerprints
            SET sha256 = ?
            WHERE manifest_id = ? AND active = 1
            """,
            ("f" * 64, "security.tool_capability_map.v1"),
        )

    try:
        with pytest.raises(BootVerificationError):
            verify_boot_manifests()

        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT *
                FROM security_events
                WHERE event_type = 'manifest_boot_verification_failed'
                ORDER BY event_id DESC
                LIMIT 1
                """
            ).fetchone()

        assert row is not None
        assert row["severity"] == "critical"
        assert row["reason"] == "manifest_sha256_mismatch"

    finally:
        with get_connection() as conn:
            conn.execute(
                """
                UPDATE manifest_fingerprints
                SET sha256 = ?
                WHERE manifest_id = ? AND active = 1
                """,
                (original_sha, "security.tool_capability_map.v1"),
            )


def test_boot_verifier_fails_on_missing_registered_file_and_logs_critical():
    unique_id = "security.tool_capability_map.missing_file_test.v1"

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO manifest_fingerprints
            (manifest_id, manifest_type, relative_path, sha256, schema_version,
             manifest_version, role_name, command_name, approved_by_panel_version,
             active, registered_by_tool_version)
            VALUES (?, ?, ?, ?, ?, ?, NULL, NULL, ?, 1, ?)
            """,
            (
                unique_id,
                "tool_capability_map",
                "policy/security_artifacts/does_not_exist_for_boot_test.json",
                "0" * 64,
                "axiom.tool_capability_map.v1",
                "1.0.0",
                "v1.11.4",
                "test",
            ),
        )

    try:
        with pytest.raises(BootVerificationError):
            verify_boot_manifests()

        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT *
                FROM security_events
                WHERE event_type = 'manifest_boot_verification_failed'
                ORDER BY event_id DESC
                LIMIT 1
                """
            ).fetchone()

        assert row is not None
        assert row["severity"] == "critical"
        assert row["reason"] == "registered_manifest_file_missing"

    finally:
        with get_connection() as conn:
            conn.execute(
                """
                DELETE FROM manifest_fingerprints
                WHERE manifest_id = ?
                """,
                (unique_id,),
            )
