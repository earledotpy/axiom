from axiom.app.status_report import build_status_report
from axiom.persistence.db import get_connection, init_db


def test_status_report_fails_closed_without_current_trusted_profile():
    init_db()

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
                "status.test.pending",
                "pending_calibration_set",
                "0" * 64,
                "qwen3:4b",
                "http://localhost:11434",
                0.0,
                0,
                "pending_panel_approval",
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
                "status_test",
                "qwen3:4b",
                "http://localhost:11434",
                "qwen3:4b",
                "Qwen3",
                "Q4_K_M",
                "4.0B",
                "qwen3",
                "gguf",
                "unknown",
                "gateway_required_v1",
                "status-test-" + ("0" * 52),
                "status.test.pending",
                0,
                "candidate",
                "test",
                "{}",
            ),
        )

        conn.execute(
            """
            INSERT INTO sessions
            (safe_pass_enabled, autonomous_operation_enabled,
             safe_pass_disabled_reason)
            VALUES (0, 0, 'no_stored_profile')
            """
        )

    report = build_status_report(profile_label="status_test")

    assert report.database_initialized is True
    assert report.model_candidate_profile_present is True
    assert report.current_trusted_model_profile_present is False
    assert report.safe_pass_enabled is False
    assert report.autonomous_operation_enabled is False
    assert report.autonomous_available is False
    assert "no_current_trusted_model_profile" in report.blocking_reasons
    assert "safe_pass_disabled" in report.blocking_reasons


def test_status_report_json_shape():
    report = build_status_report(profile_label="status_test")
    payload = report.to_dict()

    assert "database_initialized" in payload
    assert "manifest_fingerprints_valid" in payload
    assert "model_candidate_profile_present" in payload
    assert "current_trusted_model_profile_present" in payload
    assert "safe_pass_enabled" in payload
    assert "autonomous_operation_enabled" in payload
    assert "autonomous_available" in payload
    assert "blocking_reasons" in payload
    assert "details" in payload