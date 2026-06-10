import pytest

from axiom.persistence.level2a.dead_letter import (
    DEAD_LETTER_ENV_VAR,
    DEFAULT_DEAD_LETTER_PATH,
    DeadLetterLog,
    resolve_dead_letter_path,
)


def test_dead_letter_log_records_failed_envelope_and_preserves_payload(tmp_path):
    log = DeadLetterLog(tmp_path / "dead-letter.db")
    payload = {"envelope_id": "ENV-12345678-1234-4234-9234-123456789abc", "bad": True}

    record = log.log_dead_letter(
        rejection_code="ERR_SIGNATURE_INVALID",
        failure_reason="tampered payload",
        raw_payload=payload,
        actor="dead_letter_subsystem",
        original_envelope_id=payload["envelope_id"],
        mandate_id="MND-ACCEPTED-2026-0007-PHASE4-HUB-RELAY",
        docket_id="DK-2026-0007",
    )

    records = log.list_dead_letters()
    assert records == [record]
    assert records[0]["raw_payload"] == payload


def test_dead_letter_environment_override_is_respected(monkeypatch, tmp_path):
    db_path = tmp_path / "env-dead-letter.db"
    monkeypatch.setenv(DEAD_LETTER_ENV_VAR, str(db_path))

    log = DeadLetterLog()
    log.log_dead_letter(
        rejection_code="ERR_RELAY_BLOCKED_ACTION",
        failure_reason="blocked",
        raw_payload={"blocked": ["shell_command_frame"]},
        actor="dead_letter_subsystem",
    )

    assert log.path == db_path
    assert db_path.exists()


def test_dead_letter_rejects_malformed_inputs(tmp_path):
    log = DeadLetterLog(tmp_path / "dead-letter.db")

    with pytest.raises(ValueError, match="ERR_INVALID_REJECTION_CODE"):
        log.log_dead_letter(
            rejection_code="",
            failure_reason="missing code",
            raw_payload={},
            actor="dead_letter_subsystem",
        )


def test_dead_letter_tests_do_not_touch_default_database(monkeypatch, tmp_path):
    before_exists = DEFAULT_DEAD_LETTER_PATH.exists()
    before_mtime = DEFAULT_DEAD_LETTER_PATH.stat().st_mtime_ns if before_exists else None
    monkeypatch.setenv(DEAD_LETTER_ENV_VAR, str(tmp_path / "isolated-dead-letter.db"))

    DeadLetterLog().log_dead_letter(
        rejection_code="ERR_INVALID_SCHEMA",
        failure_reason="isolated",
        raw_payload={"isolated": True},
        actor="dead_letter_subsystem",
    )

    after_exists = DEFAULT_DEAD_LETTER_PATH.exists()
    after_mtime = DEFAULT_DEAD_LETTER_PATH.stat().st_mtime_ns if after_exists else None
    assert (after_exists, after_mtime) == (before_exists, before_mtime)


def test_dead_letter_default_path_is_inside_level2a(monkeypatch):
    monkeypatch.delenv(DEAD_LETTER_ENV_VAR, raising=False)

    assert resolve_dead_letter_path() == DEFAULT_DEAD_LETTER_PATH
    assert DEFAULT_DEAD_LETTER_PATH.name == "dead_letter.db"
    assert DEFAULT_DEAD_LETTER_PATH.parent.name == "level2a"
