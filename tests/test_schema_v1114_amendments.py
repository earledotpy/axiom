from uuid import uuid4

from axiom.persistence.db import get_connection, init_db


def test_schema_version_is_v1114():
    init_db()
    with get_connection() as conn:
        rows = conn.execute("SELECT schema_version FROM schema_migrations").fetchall()
        assert {row["schema_version"] for row in rows} == {"v1.11.4"}


def test_manifest_fingerprints_accepts_tool_capability_map_type():
    init_db()
    unique = uuid4().hex

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO manifest_fingerprints
            (manifest_id, manifest_type, relative_path, sha256, schema_version,
             manifest_version, role_name, command_name, approved_by_panel_version,
             active, registered_by_tool_version)
            VALUES (?, ?, ?, ?, ?, ?, NULL, NULL, ?, 0, ?)
            """,
            (
                f"security.tool_capability_map.test_{unique}.v1",
                "tool_capability_map",
                f"policy/security_artifacts/tool_capability_map.test_{unique}.json",
                "0" * 64,
                "axiom.tool_capability_map.v1",
                "1.0.0",
                "v1.11.4",
                "test",
            ),
        )


def test_provider_enum_rejects_unknown_provider():
    init_db()
    with get_connection() as conn:
        session_id = conn.execute("INSERT INTO sessions DEFAULT VALUES").lastrowid
        try:
            conn.execute(
                "INSERT INTO provider_usage (session_id, provider, status) VALUES (?, ?, ?)",
                (session_id, "paid_unknown_provider", "started"),
            )
        except Exception as exc:
            assert "CHECK" in str(exc).upper() or "constraint" in str(exc).lower()
        else:
            raise AssertionError("unknown provider was accepted")
