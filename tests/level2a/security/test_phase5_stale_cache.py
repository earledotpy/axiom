import json
from datetime import datetime, timezone
from pathlib import Path

from axiom.core.autonomous_gate import evaluate_autonomous_readiness
from axiom.persistence.db import get_connection
from tests.test_autonomous_gate import insert_active_tool_capability_map


def _seed_current_profile(conn, profile_label: str) -> int:
    calibration_run_id = "phase5.stale.cache.calibration"
    conn.execute(
        """
        INSERT INTO classifier_calibration_runs
        (calibration_run_id, calibration_set_id, calibration_set_sha256,
         model_name, ollama_host, threshold, passed,
         approved_by_panel_version)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(calibration_run_id) DO NOTHING
        """,
        (
            calibration_run_id,
            "phase5_stale_cache_set",
            "3" * 64,
            "qwen3:4b",
            "http://localhost:11434",
            0.5,
            1,
            "test",
        ),
    )

    conn.execute(
        """
        INSERT OR IGNORE INTO model_profile_fingerprints
        (profile_label, model_name, ollama_host, ollama_model_tag,
         ollama_model_digest, quantization, parameter_size, model_family,
         model_format, thinking_mode, thinking_mode_rule_version,
         selected_profile_sha256, calibration_run_id, is_current,
         registration_status, registered_by_tool_version, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            profile_label,
            "qwen3:4b",
            "http://localhost:11434",
            "qwen3:4b",
            "Qwen3",
            "Q4_K_M",
            "4.0B",
            "qwen3",
            "gguf",
            "disabled",
            "profile_verified_v1",
            "phase5-stale-cache-" + ("0" * 45),
            calibration_run_id,
            1,
            "current",
            "test",
            "{}",
        ),
    )

    cur = conn.execute(
        """
        INSERT INTO sessions
        (safe_pass_enabled, autonomous_operation_enabled,
         safe_pass_disabled_reason)
        VALUES (1, 1, NULL)
        """
    )
    session_id = cur.lastrowid
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    conn.execute(
        """
        INSERT INTO scheduler_heartbeat
        (session_id, last_freshness_at, scheduler_state)
        VALUES (?, ?, 'ready')
        """,
        (session_id, now),
    )
    return session_id


def test_stale_posture_cache_allowed_true_does_not_bypass_live_database(tmp_path):
    cache_path = tmp_path / "posture_cache.json"
    cache_path.write_text(
        json.dumps(
            {
                "allowed": True,
                "autonomous_available": True,
                "blocking_reasons": [],
            }
        ),
        encoding="utf-8",
    )

    profile_label = "phase5_stale_cache_denial"
    with get_connection() as conn:
        _seed_current_profile(conn, profile_label)
        conn.execute("UPDATE manifest_fingerprints SET active = 0")

    decision = evaluate_autonomous_readiness(profile_label=profile_label)

    assert cache_path.exists()
    assert json.loads(cache_path.read_text(encoding="utf-8"))["allowed"] is True
    assert decision.allowed is False
    assert "manifest_fingerprints_not_valid" in decision.blocking_reasons


def test_stale_cache_fixture_does_not_touch_default_ipc_cache(tmp_path):
    default_cache = Path("ipc/posture_cache.json")
    before_exists = default_cache.exists()
    before_mtime = default_cache.stat().st_mtime_ns if before_exists else None

    cache_path = tmp_path / "posture_cache.json"
    cache_path.write_text('{"allowed": true}', encoding="utf-8")

    profile_label = "phase5_default_cache_untouched"
    with get_connection() as conn:
        insert_active_tool_capability_map(conn)
        _seed_current_profile(conn, profile_label)

    decision = evaluate_autonomous_readiness(profile_label=profile_label)

    assert decision.allowed is True
    assert default_cache.exists() is before_exists
    if before_exists:
        assert default_cache.stat().st_mtime_ns == before_mtime
