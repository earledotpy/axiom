from axiom.persistence.level2a.relay_queue import (
    DEFAULT_RELAY_QUEUE_PATH,
    RELAY_QUEUE_ENV_VAR,
    RelayQueue,
    resolve_relay_queue_path,
)


def _envelope(envelope_id: str = "ENV-12345678-1234-4234-9234-123456789abc") -> dict:
    return {
        "relay_envelope_version": "2A.1",
        "envelope_id": envelope_id,
        "docket_id": "DK-2026-0007",
        "mandate_id": "MND-ACCEPTED-2026-0007-PHASE4-HUB-RELAY",
        "source_role": "operator_console",
        "target_role": "orchestrator",
        "artifact_type": "patch_artifact",
        "artifact_ref": "governance/05_handoffs/phase4.json",
        "artifact_sha256": "sha256:" + "a" * 64,
        "allowed_action_type": "record_artifact",
        "blocked_action_indicators": [],
        "created_at": "2026-06-07T00:00:00Z",
        "nonce": "nonce_v1_" + "b" * 64,
        "canonicalization": "RFC8785",
        "schema_hash": "sha256:" + "c" * 64,
    }


def test_relay_queue_uses_wal_and_supports_enqueue_peek_dequeue_mark_processed(tmp_path):
    queue = RelayQueue(tmp_path / "relay.db")
    envelope = _envelope()

    assert queue.enqueue_envelope(envelope) == envelope["envelope_id"]
    assert queue.journal_mode() == "wal"
    assert queue.peek() == envelope
    assert queue.dequeue_envelope() == envelope
    assert queue.peek() is None
    assert queue.mark_processed(envelope["envelope_id"]) is True


def test_relay_queue_environment_override_is_respected(monkeypatch, tmp_path):
    db_path = tmp_path / "env-relay.db"
    monkeypatch.setenv(RELAY_QUEUE_ENV_VAR, str(db_path))

    queue = RelayQueue()
    queue.enqueue_envelope(_envelope())

    assert queue.path == db_path
    assert db_path.exists()


def test_relay_queue_default_path_is_inside_level2a(monkeypatch):
    monkeypatch.delenv(RELAY_QUEUE_ENV_VAR, raising=False)

    assert resolve_relay_queue_path() == DEFAULT_RELAY_QUEUE_PATH
    assert DEFAULT_RELAY_QUEUE_PATH.name == "relay_queue.db"
    assert DEFAULT_RELAY_QUEUE_PATH.parent.name == "level2a"


def test_relay_queue_tests_do_not_touch_default_database(monkeypatch, tmp_path):
    before_exists = DEFAULT_RELAY_QUEUE_PATH.exists()
    before_mtime = DEFAULT_RELAY_QUEUE_PATH.stat().st_mtime_ns if before_exists else None
    monkeypatch.setenv(RELAY_QUEUE_ENV_VAR, str(tmp_path / "isolated-relay.db"))

    RelayQueue().enqueue_envelope(_envelope())

    after_exists = DEFAULT_RELAY_QUEUE_PATH.exists()
    after_mtime = DEFAULT_RELAY_QUEUE_PATH.stat().st_mtime_ns if after_exists else None
    assert (after_exists, after_mtime) == (before_exists, before_mtime)
