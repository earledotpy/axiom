from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

import tools.run_calibration as rc
from axiom.gateways.model_gateway import CloudModelResponse
from axiom.persistence.db import get_connection, init_db


def test_get_file_sha256(tmp_path):
    temp_file = tmp_path / "test.json"
    temp_file.write_text("{}", encoding="utf-8")
    sha = rc.get_file_sha256(temp_file)
    assert len(sha) == 64
    assert isinstance(sha, str)


def test_classify_prompt():
    payload = rc.classify_prompt("Test plan text")
    assert "messages" in payload
    assert len(payload["messages"]) == 2
    assert payload["messages"][0]["role"] == "system"
    assert "Test plan text" in payload["messages"][1]["content"]


def test_write_calibration_to_db(isolate_axiom_db):
    row = {
        "calibration_run_id": "test_run_123",
        "calibration_set_id": "test_set_abc",
        "calibration_set_sha256": "0" * 64,
        "model_name": "qwen3:4b",
        "ollama_host": "http://localhost:11434",
        "threshold": 0.8,
        "passed": 1,
        "true_positive_count": 5,
        "true_negative_count": 5,
        "false_positive_count": 0,
        "false_negative_count": 0,
        "false_positive_rate": 0.0,
        "false_negative_rate": 0.0,
        "approved_by_panel_version": rc.CALIBRATION_WRITE_APPROVAL_TOKEN,
        "details_json": "{}",
    }
    rc.write_calibration_to_db(row)

    with get_connection() as conn:
        db_row = conn.execute(
            "SELECT * FROM classifier_calibration_runs WHERE calibration_run_id = ?",
            ("test_run_123",),
        ).fetchone()

    assert db_row is not None
    assert db_row["calibration_set_id"] == "test_set_abc"
    assert db_row["passed"] == 1


def test_run_calibration_dry_run_does_not_write_db(isolate_axiom_db, monkeypatch, tmp_path):
    # Setup a mock calibration set JSON
    set_file = tmp_path / "calibration_set.json"
    dataset = {
        "calibration_set_id": "mock_set",
        "approved_by_panel_version": "v1.13",
        "items": [
            {"id": "item1", "text": "Ordinary item", "label": "ordinary"},
            {"id": "item2", "text": "Injection item", "label": "injection"},
        ],
    }
    set_file.write_text(json.dumps(dataset), encoding="utf-8")

    # Run in simulation mode (not live), without writing to db.
    test_args = [
        "run_calibration.py",
        "--calibration-set-path",
        str(set_file),
        "--calibration-run-id",
        "sim_run_999",
        "--approved-by-panel-version",
        rc.CALIBRATION_WRITE_APPROVAL_TOKEN,
    ]
    monkeypatch.setattr(sys, "argv", test_args)

    exit_code = rc.main()
    assert exit_code == 0

    with get_connection() as conn:
        db_row = conn.execute(
            "SELECT * FROM classifier_calibration_runs WHERE calibration_run_id = ?",
            ("sim_run_999",),
        ).fetchone()

    assert db_row is None


def test_run_calibration_refuses_simulated_db_write(
    isolate_axiom_db, monkeypatch, tmp_path
):
    set_file = tmp_path / "calibration_set.json"
    dataset = {
        "calibration_set_id": "mock_set",
        "approved_by_panel_version": "v1.13",
        "items": [
            {"id": "item1", "text": "Ordinary item", "label": "ordinary"},
            {"id": "item2", "text": "Injection item", "label": "injection"},
        ],
    }
    set_file.write_text(json.dumps(dataset), encoding="utf-8")

    test_args = [
        "run_calibration.py",
        "--calibration-set-path",
        str(set_file),
        "--write-db",
        "--calibration-run-id",
        "sim_run_999",
        "--approved-by-panel-version",
        rc.CALIBRATION_WRITE_APPROVAL_TOKEN,
    ]
    monkeypatch.setattr(sys, "argv", test_args)

    exit_code = rc.main()
    assert exit_code == 1

    with get_connection() as conn:
        db_row = conn.execute(
            "SELECT * FROM classifier_calibration_runs WHERE calibration_run_id = ?",
            ("sim_run_999",),
        ).fetchone()

    assert db_row is None


def test_run_calibration_live_mocked(isolate_axiom_db, monkeypatch, tmp_path):
    set_file = tmp_path / "calibration_set.json"
    dataset = {
        "calibration_set_id": "mock_set_live",
        "approved_by_panel_version": "v1.13",
        "items": [
            {"id": "item1", "text": "Safe ordinary query", "label": "ordinary"},
            {"id": "item2", "text": "Malicious prompt injection", "label": "injection"},
        ],
    }
    set_file.write_text(json.dumps(dataset), encoding="utf-8")

    # Mock ModelGateway's call_cloud_cascade to return specific classification responses
    mock_call = MagicMock()
    # First call returns safe classification, second returns injection classification
    mock_call.side_effect = [
        CloudModelResponse(
            provider="groq",
            model="llama-3.3-70b-versatile",
            response_text="ordinary",
            provider_usage_id=1,
            provider_call_usage_id=1,
        ),
        CloudModelResponse(
            provider="groq",
            model="llama-3.3-70b-versatile",
            response_text="injection",
            provider_usage_id=2,
            provider_call_usage_id=2,
        ),
    ]

    from axiom.gateways.model_gateway import ModelGateway
    monkeypatch.setattr(ModelGateway, "call_cloud_cascade", mock_call)

    # Insert minimal mock tool capability map to satisfy create_task foreign keys
    with get_connection() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO manifest_fingerprints
            (manifest_id, manifest_type, relative_path, sha256, schema_version,
             manifest_version, role_name, command_name, approved_by_panel_version,
             active, registered_by_tool_version)
            VALUES (?, 'tool_capability_map', 'path', 'sha', 'schema', '1.0.0', NULL, NULL, 'test', 1, 'test')
            """,
            (rc.TOOL_MAP_MANIFEST_ID,),
        )

    test_args = [
        "run_calibration.py",
        "--live",
        "--write-db",
        "--calibration-set-path",
        str(set_file),
        "--calibration-run-id",
        "live_run_888",
        "--approved-by-panel-version",
        rc.CALIBRATION_WRITE_APPROVAL_TOKEN,
    ]
    monkeypatch.setattr(sys, "argv", test_args)

    exit_code = rc.main()
    assert exit_code == 0

    assert mock_call.call_count == 2

    with get_connection() as conn:
        db_row = conn.execute(
            "SELECT * FROM classifier_calibration_runs WHERE calibration_run_id = ?",
            ("live_run_888",),
        ).fetchone()

    assert db_row is not None
    assert db_row["calibration_set_id"] == "mock_set_live"
    assert db_row["passed"] == 1
    assert db_row["true_positive_count"] == 1
    assert db_row["true_negative_count"] == 1
    details = json.loads(db_row["details_json"])
    assert details["run_mode"] == "live"
    assert details["live"] is True


def test_run_calibration_write_db_requires_explicit_approval(
    isolate_axiom_db, monkeypatch, tmp_path
):
    set_file = tmp_path / "calibration_set.json"
    dataset = {
        "calibration_set_id": "mock_set_blocked",
        "items": [
            {"id": "item1", "text": "Ordinary item", "label": "ordinary"},
        ],
    }
    set_file.write_text(json.dumps(dataset), encoding="utf-8")

    test_args = [
        "run_calibration.py",
        "--calibration-set-path",
        str(set_file),
        "--write-db",
        "--calibration-run-id",
        "blocked_run_777",
    ]
    monkeypatch.setattr(sys, "argv", test_args)

    exit_code = rc.main()
    assert exit_code == 1

    with get_connection() as conn:
        db_row = conn.execute(
            "SELECT * FROM classifier_calibration_runs WHERE calibration_run_id = ?",
            ("blocked_run_777",),
        ).fetchone()

    assert db_row is None
