import pytest

from axiom.core.autonomous_gate import (
    AutonomousReadinessError,
    evaluate_autonomous_readiness,
    require_autonomous_ready,
)
from axiom.persistence.db import get_connection, init_db


def test_autonomous_gate_blocks_without_current_trusted_profile():
    init_db()

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO sessions
            (safe_pass_enabled, autonomous_operation_enabled,
             safe_pass_disabled_reason)
            VALUES (0, 0, 'no_stored_profile')
            """
        )

    decision = evaluate_autonomous_readiness(
        profile_label="autonomous_gate_no_current_profile_test"
    )

    assert decision.allowed is False
    assert "no_current_trusted_model_profile" in decision.blocking_reasons
    assert "safe_pass_disabled" in decision.blocking_reasons
    assert "autonomous_operation_disabled" in decision.blocking_reasons


def test_require_autonomous_ready_raises_when_blocked():
    init_db()

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO sessions
            (safe_pass_enabled, autonomous_operation_enabled,
             safe_pass_disabled_reason)
            VALUES (0, 0, 'no_stored_profile')
            """
        )

    with pytest.raises(AutonomousReadinessError) as exc:
        require_autonomous_ready(
            profile_label="autonomous_gate_raise_blocked_test"
        )

    assert "Autonomous operation is not available" in str(exc.value)
    assert "no_current_trusted_model_profile" in str(exc.value)


def test_autonomous_gate_allows_when_all_status_conditions_are_true():
    init_db()

    profile_label = "autonomous_gate_allowed_test"
    calibration_run_id = "autonomous.gate.allowed.calibration"

    with get_connection() as conn:
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
                "test_calibration_set",
                "1" * 64,
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
                "autonomous-gate-allowed-" + ("0" * 38),
                calibration_run_id,
                1,
                "current",
                "test",
                "{}",
            ),
        )

        conn.execute(
            """
            INSERT INTO sessions
            (safe_pass_enabled, autonomous_operation_enabled,
             safe_pass_disabled_reason)
            VALUES (1, 1, NULL)
            """
        )

    decision = evaluate_autonomous_readiness(profile_label=profile_label)

    assert decision.allowed is True
    assert decision.blocking_reasons == []


def test_require_autonomous_ready_does_not_raise_when_allowed():
    init_db()

    profile_label = "autonomous_gate_require_allowed_test"
    calibration_run_id = "autonomous.gate.require.allowed.calibration"

    with get_connection() as conn:
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
                "test_calibration_set",
                "2" * 64,
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
                "autonomous-gate-require-allowed-" + ("0" * 30),
                calibration_run_id,
                1,
                "current",
                "test",
                "{}",
            ),
        )

        conn.execute(
            """
            INSERT INTO sessions
            (safe_pass_enabled, autonomous_operation_enabled,
             safe_pass_disabled_reason)
            VALUES (1, 1, NULL)
            """
        )

    require_autonomous_ready(profile_label=profile_label)