import pytest

from axiom.app.bootstrap_validation import BootstrapValidationError, BootstrapValidator
from axiom.persistence.db import get_connection


def test_bootstrap_validator_passes_current_foundation():
    result = BootstrapValidator().run()

    assert result.passed is True
    assert result.failures == []
    assert {check.name for check in result.checks} == {
        "sqlite_pragmas",
        "schema_version",
        "sqlite_vec_table",
        "tool_capability_map",
        "manifest_fingerprints",
    }


def test_bootstrap_validator_sqlite_pragmas_check_passes():
    check = BootstrapValidator().check_sqlite_pragmas()

    assert check.passed is True
    assert check.reason == "sqlite_pragmas_valid"
    assert check.details["journal_mode"].lower() == "wal"
    assert check.details["busy_timeout"] >= 5000
    assert check.details["foreign_keys"] == 1
    assert check.details["cache_size"] < 0


def test_bootstrap_validator_schema_version_check_passes():
    check = BootstrapValidator().check_schema_version()

    assert check.passed is True
    assert check.reason == "schema_version_valid"
    assert check.details["schema_versions"] == ["v1.11.4"]


def test_bootstrap_validator_sqlite_vec_table_check_passes():
    check = BootstrapValidator().check_sqlite_vec_table()

    assert check.passed is True
    assert check.reason == "memory_vec_table_present"
    assert check.details["table"] == "memory_item_embeddings"


def test_bootstrap_validator_tool_capability_map_check_passes():
    check = BootstrapValidator().check_tool_capability_map()

    assert check.passed is True
    assert check.reason == "tool_capability_map_loaded"
    assert check.details["tool_count"] >= 1
    assert "model_gateway.call" in check.details["tool_ids"]


def test_bootstrap_validator_manifest_fingerprints_check_passes():
    check = BootstrapValidator().check_manifest_fingerprints()

    assert check.passed is True
    assert check.reason == "manifest_fingerprints_valid"
    assert "security.tool_capability_map.v1" in check.details["manifest_ids"]


def test_bootstrap_validator_raise_on_failure_raises_when_schema_version_bad(monkeypatch):
    validator = BootstrapValidator()

    def fake_bad_schema_check():
        from axiom.app.bootstrap_validation import BootstrapCheck

        return BootstrapCheck(
            name="schema_version",
            passed=False,
            reason="schema_version_mismatch",
            details={"schema_versions": ["bad"]},
        )

    monkeypatch.setattr(validator, "check_schema_version", fake_bad_schema_check)

    with pytest.raises(BootstrapValidationError):
        validator.run(raise_on_failure=True)


def test_bootstrap_validator_detects_manifest_sha_failure_without_raising_by_default():
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT sha256
            FROM manifest_fingerprints
            WHERE manifest_id = 'security.tool_capability_map.v1'
            """
        ).fetchone()
        original_sha = row["sha256"]

        conn.execute(
            """
            UPDATE manifest_fingerprints
            SET sha256 = ?
            WHERE manifest_id = 'security.tool_capability_map.v1'
            """,
            ("0" * 64,),
        )

    try:
        result = BootstrapValidator().run(raise_on_failure=False)

        assert result.passed is False
        assert any(
            check.name == "manifest_fingerprints"
            and check.reason == "manifest_fingerprint_verification_failed"
            for check in result.failures
        )

    finally:
        with get_connection() as conn:
            conn.execute(
                """
                UPDATE manifest_fingerprints
                SET sha256 = ?
                WHERE manifest_id = 'security.tool_capability_map.v1'
                """,
                (original_sha,),
            )
