from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tools.cloud_cascade_smoke_test import (
    build_cloud_cascade_config,
    key_visibility,
    max_tokens_for_target,
    provider_order_for_target,
    run_cloud_cascade_smoke,
    sentinel_for_target,
    smoke_payload,
)


ROOT = Path(__file__).resolve().parents[1]


def test_cloud_cascade_smoke_builds_provider_order():
    assert provider_order_for_target("groq") == ("groq",)
    assert provider_order_for_target("cascade") == (
        "groq",
        "cerebras",
        "sambanova",
        "openrouter",
    )


def test_cloud_cascade_smoke_uses_expected_sentinels_and_token_budgets():
    assert sentinel_for_target("groq") == "AXIOM_GROQ_SMOKE_OK"
    assert sentinel_for_target("cerebras") == "AXIOM_CEREBRAS_SMOKE_OK"
    assert sentinel_for_target("sambanova") == "AXIOM_SAMBANOVA_SMOKE_OK"
    assert sentinel_for_target("openrouter") == "AXIOM_OPENROUTER_SMOKE_OK"
    assert sentinel_for_target("cascade") == "AXIOM_CLOUD_CASCADE_SMOKE_OK"
    assert max_tokens_for_target("cerebras") == 96
    assert max_tokens_for_target("openrouter") == 256
    assert max_tokens_for_target("cascade") == 256


def test_cloud_cascade_smoke_payload_requests_exact_sentinel():
    payload = smoke_payload("cascade")

    assert payload["temperature"] == 0
    assert payload["max_tokens"] == 256
    assert payload["messages"][0]["content"] == (
        "Reply with exactly: AXIOM_CLOUD_CASCADE_SMOKE_OK"
    )


def test_cloud_cascade_smoke_config_requires_live_flag_for_real_calls():
    dry_config = build_cloud_cascade_config("cascade", live=False)
    live_config = build_cloud_cascade_config("cascade", live=True)

    assert dry_config.real_calls_enabled is False
    assert live_config.real_calls_enabled is True
    assert dry_config.provider_order == (
        "groq",
        "cerebras",
        "sambanova",
        "openrouter",
    )


def test_cloud_cascade_smoke_key_visibility_does_not_expose_values(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "secret-value")
    config = build_cloud_cascade_config("groq", live=False)

    visibility = key_visibility(config)

    assert visibility == {"GROQ_API_KEY": True}
    assert "secret-value" not in json.dumps(visibility)


def test_cloud_cascade_smoke_dry_run_does_not_call_model(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    payload = run_cloud_cascade_smoke("groq", live=False)

    assert payload["live"] is False
    assert payload["ready"] is True
    assert payload["called_provider"] is None
    assert "response_text" not in payload
    assert payload["sentinel_matched"] is None
    assert payload["key_visibility"] == {"GROQ_API_KEY": False}


def test_cloud_cascade_smoke_cli_json_dry_run_is_parseable():
    result = subprocess.run(
        [
            sys.executable,
            "tools/cloud_cascade_smoke_test.py",
            "--target",
            "groq",
            "--json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["target"] == "groq"
    assert payload["live"] is False
    assert payload["passed"] is True
    assert payload["called_provider"] is None
