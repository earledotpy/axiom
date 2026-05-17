import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from axiom.persistence.db import get_connection

ROOT = Path(r"C:\axiom")
sys.path.insert(0, str(ROOT / "tools"))

import register_model_fingerprint as rmf


def fake_success_result_unknown():
    return SimpleNamespace(
        host="http://localhost:11434",
        model="qwen3:4b",
        reachable=True,
        model_present=True,
        show_available=True,
        details_present=True,
        parameters_present=True,
        quantization_level="Q4_K_M",
        profile_thinking_mode="unknown",
        runtime_thinking_enforcement="gateway_required",
        fingerprint_registration_ready=True,
        raw_show={
            "digest": "sha256:testdigest",
            "details": {
                "family": "qwen3",
                "format": "gguf",
                "parameter_size": "4.7B",
                "quantization_level": "Q4_K_M",
            },
            "parameters": "temperature 1\ntop_k 20\n",
            "template": "{{ .Prompt }}",
            "system": None,
        },
    )


def fake_success_result_disabled():
    result = fake_success_result_unknown()
    result.profile_thinking_mode = "disabled"
    result.runtime_thinking_enforcement = "profile_verified"
    result.raw_show["parameters"] = "temperature 1\nthink false\n"
    return result


class FakeInspectorUnknown:
    def __init__(self, *args, **kwargs):
        pass

    def inspect(self):
        return fake_success_result_unknown()


class FakeInspectorDisabled:
    def __init__(self, *args, **kwargs):
        pass

    def inspect(self):
        return fake_success_result_disabled()


def test_register_model_fingerprint_records_unknown_as_non_current_candidate(monkeypatch):
    monkeypatch.setattr(rmf, "OllamaPrereqInspector", FakeInspectorUnknown)

    profile_id = rmf.register_model_fingerprint(
        model="qwen3:4b",
        profile_label="test_profile_unknown",
        calibration_run_id="calibration.test.unknown",
    )

    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT *
            FROM model_profile_fingerprints
            WHERE profile_id = ?
            """,
            (profile_id,),
        ).fetchone()
        calibration = conn.execute(
            """
            SELECT *
            FROM classifier_calibration_runs
            WHERE calibration_run_id = ?
            """,
            ("calibration.test.unknown",),
        ).fetchone()

    assert row is not None
    assert row["profile_label"] == "test_profile_unknown"
    assert row["model_name"] == "qwen3:4b"
    assert row["ollama_host"] == "http://localhost:11434"
    assert row["ollama_model_tag"] == "qwen3:4b"
    assert row["ollama_model_digest"] == "sha256:testdigest"
    assert row["quantization"] == "Q4_K_M"
    assert row["parameter_size"] == "4.7B"
    assert row["model_family"] == "qwen3"
    assert row["model_format"] == "gguf"
    assert row["thinking_mode"] == "unknown"
    assert row["thinking_mode_rule_version"] == "gateway_required_v1"
    assert row["selected_profile_sha256"] is not None
    assert row["calibration_run_id"] == "calibration.test.unknown"
    assert row["is_current"] == 0
    assert row["registration_status"] == "candidate"
    assert row["registered_by_tool_version"] == "register_model_fingerprint.v1"

    assert calibration is not None
    assert calibration["passed"] == 0
    assert calibration["approved_by_panel_version"] == "pending_panel_approval"

    notes = json.loads(row["notes"])
    assert notes["runtime_thinking_enforcement"] == "gateway_required"


def test_register_model_fingerprint_records_disabled_as_current(monkeypatch):
    monkeypatch.setattr(rmf, "OllamaPrereqInspector", FakeInspectorDisabled)

    profile_id = rmf.register_model_fingerprint(
        model="qwen3:4b",
        profile_label="test_profile_disabled",
        calibration_run_id="calibration.test.disabled",
    )

    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT *
            FROM model_profile_fingerprints
            WHERE profile_id = ?
            """,
            (profile_id,),
        ).fetchone()

    assert row["thinking_mode"] == "disabled"
    assert row["thinking_mode_rule_version"] == "profile_verified_v1"
    assert row["is_current"] == 1
    assert row["registration_status"] == "current"


def test_register_model_fingerprint_demotes_previous_current_row_only_when_new_current(monkeypatch):
    monkeypatch.setattr(rmf, "OllamaPrereqInspector", FakeInspectorDisabled)

    first_id = rmf.register_model_fingerprint(
        model="qwen3:4b",
        profile_label="demotion_test",
        calibration_run_id="calibration.test.demotion.1",
    )
    second_id = rmf.register_model_fingerprint(
        model="qwen3:4b",
        profile_label="demotion_test",
        calibration_run_id="calibration.test.demotion.2",
    )

    with get_connection() as conn:
        first = conn.execute(
            "SELECT is_current, registration_status FROM model_profile_fingerprints WHERE profile_id = ?",
            (first_id,),
        ).fetchone()
        second = conn.execute(
            "SELECT is_current, registration_status FROM model_profile_fingerprints WHERE profile_id = ?",
            (second_id,),
        ).fetchone()

    assert first["is_current"] == 0
    assert second["is_current"] == 1
    assert second["registration_status"] == "current"


def test_register_model_fingerprint_unknown_candidate_does_not_demote_current(monkeypatch):
    monkeypatch.setattr(rmf, "OllamaPrereqInspector", FakeInspectorDisabled)

    current_id = rmf.register_model_fingerprint(
        model="qwen3:4b",
        profile_label="non_demotion_test",
        calibration_run_id="calibration.test.non_demotion.current",
    )

    monkeypatch.setattr(rmf, "OllamaPrereqInspector", FakeInspectorUnknown)

    candidate_id = rmf.register_model_fingerprint(
        model="qwen3:4b",
        profile_label="non_demotion_test",
        calibration_run_id="calibration.test.non_demotion.candidate",
    )

    with get_connection() as conn:
        current = conn.execute(
            "SELECT is_current, registration_status FROM model_profile_fingerprints WHERE profile_id = ?",
            (current_id,),
        ).fetchone()
        candidate = conn.execute(
            "SELECT is_current, registration_status FROM model_profile_fingerprints WHERE profile_id = ?",
            (candidate_id,),
        ).fetchone()

    assert current["is_current"] == 1
    assert current["registration_status"] == "current"
    assert candidate["is_current"] == 0
    assert candidate["registration_status"] == "candidate"


def test_register_model_fingerprint_rejects_unreachable(monkeypatch):
    class UnreachableInspector:
        def __init__(self, *args, **kwargs):
            pass

        def inspect(self):
            result = fake_success_result_unknown()
            result.reachable = False
            return result

    monkeypatch.setattr(rmf, "OllamaPrereqInspector", UnreachableInspector)

    with pytest.raises(rmf.ModelFingerprintRegistrationError):
        rmf.register_model_fingerprint(model="qwen3:4b", profile_label="unreachable_test")


def test_register_model_fingerprint_rejects_missing_quantization(monkeypatch):
    class MissingQuantInspector:
        def __init__(self, *args, **kwargs):
            pass

        def inspect(self):
            result = fake_success_result_unknown()
            result.quantization_level = None
            return result

    monkeypatch.setattr(rmf, "OllamaPrereqInspector", MissingQuantInspector)

    with pytest.raises(rmf.ModelFingerprintRegistrationError):
        rmf.register_model_fingerprint(model="qwen3:4b", profile_label="missing_quant_test")


def test_register_model_fingerprint_rejects_invalid_registration_status(monkeypatch):
    monkeypatch.setattr(rmf, "OllamaPrereqInspector", FakeInspectorUnknown)

    with pytest.raises(rmf.ModelFingerprintRegistrationError):
        rmf.register_model_fingerprint(
            model="qwen3:4b",
            profile_label="invalid_status_test",
            registration_status="bad_status",
        )
