from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tools.memory_gateway_smoke_test import (
    OLLAMA_EMBEDDING_DIM,
    OLLAMA_ENDPOINT_PATH,
    OLLAMA_HOST,
    OLLAMA_MODEL,
    run_memory_gateway_smoke,
)


ROOT = Path(__file__).resolve().parents[1]


def test_memory_gateway_smoke_dry_run_reports_local_ollama_boundary():
    payload = run_memory_gateway_smoke(live=False)

    assert payload["provider"] == "ollama_embed"
    assert payload["host"] == OLLAMA_HOST
    assert payload["endpoint"] == f"{OLLAMA_HOST}{OLLAMA_ENDPOINT_PATH}"
    assert payload["endpoint_path"] == "/api/embed"
    assert payload["model"] == OLLAMA_MODEL
    assert payload["embedding_dim"] == OLLAMA_EMBEDDING_DIM
    assert payload["live"] is False
    assert "sentinel" not in payload
    assert "content_sha256" in payload
    assert payload["result"] == "dry_run_only"
    assert payload["passed"] is True


def test_memory_gateway_smoke_cli_json_dry_run_is_parseable():
    result = subprocess.run(
        [sys.executable, "tools/memory_gateway_smoke_test.py", "--json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0

    payload = json.loads(result.stdout)
    assert payload["provider"] == "ollama_embed"
    assert payload["endpoint_path"] == "/api/embed"
    assert payload["model"] == "nomic-embed-text"
    assert payload["live"] is False
    assert "sentinel" not in payload
    assert payload["passed"] is True


def test_memory_gateway_smoke_dry_run_does_not_expose_vectors_or_api_keys():
    payload = run_memory_gateway_smoke(live=False)
    payload_text = json.dumps(payload, sort_keys=True)

    assert "embedding_vector" not in payload_text
    assert "embeddings" not in payload_text
    assert "api_key" not in payload_text.lower()


def test_memory_gateway_smoke_dry_run_does_not_expose_custom_content():
    payload = run_memory_gateway_smoke(live=False, content="sensitive memory content")
    payload_text = json.dumps(payload, sort_keys=True)

    assert "sensitive memory content" not in payload_text
    assert "content_sha256" in payload
