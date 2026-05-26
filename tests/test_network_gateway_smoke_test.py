import json
import subprocess
import sys
from pathlib import Path

from tools.network_gateway_smoke_test import (
    BRAVE_API_KEY_ENV,
    BRAVE_ENDPOINT,
    run_network_gateway_smoke,
)


ROOT = Path(__file__).resolve().parents[1]


def test_network_gateway_smoke_dry_run_does_not_require_key(monkeypatch):
    monkeypatch.delenv(BRAVE_API_KEY_ENV, raising=False)

    payload = run_network_gateway_smoke(live=False, query="AXIOM runtime")

    assert payload["provider"] == "brave_search"
    assert payload["endpoint"] == BRAVE_ENDPOINT
    assert payload["api_key_env_var"] == BRAVE_API_KEY_ENV
    assert payload["api_key_is_set"] is False
    assert payload["live"] is False
    assert "query" not in payload
    assert "query_sha256" in payload
    assert payload["result"] == "dry_run_only"
    assert payload["passed"] is True


def test_network_gateway_smoke_does_not_expose_key_value(monkeypatch):
    monkeypatch.setenv(BRAVE_API_KEY_ENV, "secret-network-key")

    payload = run_network_gateway_smoke(live=False, query="AXIOM runtime")
    text = json.dumps(payload, sort_keys=True)

    assert payload["api_key_is_set"] is True
    assert "secret-network-key" not in text


def test_network_gateway_smoke_does_not_expose_query_or_body_preview(monkeypatch):
    monkeypatch.delenv(BRAVE_API_KEY_ENV, raising=False)

    payload = run_network_gateway_smoke(live=False, query="sensitive query")
    text = json.dumps(payload, sort_keys=True)

    assert "sensitive query" not in text
    assert "body_preview" not in payload


def test_network_gateway_smoke_cli_json_dry_run_is_parseable(monkeypatch):
    monkeypatch.delenv(BRAVE_API_KEY_ENV, raising=False)

    result = subprocess.run(
        [
            sys.executable,
            "tools/network_gateway_smoke_test.py",
            "--json",
            "--query",
            "AXIOM runtime",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["provider"] == "brave_search"
    assert payload["live"] is False
    assert payload["passed"] is True
