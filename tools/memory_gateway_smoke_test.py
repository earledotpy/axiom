from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from axiom.gateways.memory_gateway import (
    MemoryAuthorization,
    MemoryGateway,
    MemoryGatewayConfig,
    MemoryWriteItem,
    OllamaEmbeddingProvider,
    OllamaEmbeddingProviderConfig,
)
from axiom.persistence.repositories import create_session, create_task


TOOL_MAP_MANIFEST_ID = "security.tool_capability_map.v1"
OLLAMA_HOST = "http://localhost:11434"
OLLAMA_ENDPOINT_PATH = "/api/embed"
OLLAMA_MODEL = "nomic-embed-text"
OLLAMA_EMBEDDING_DIM = 768
SENTINEL = "AXIOM_MEMORY_SMOKE_OK"


def _make_gateway(live: bool) -> MemoryGateway:
    provider = OllamaEmbeddingProvider(
        OllamaEmbeddingProviderConfig(
            host=OLLAMA_HOST,
            endpoint_path=OLLAMA_ENDPOINT_PATH,
            expected_embedding_dim=OLLAMA_EMBEDDING_DIM,
        )
    )
    return MemoryGateway(
        config=MemoryGatewayConfig(
            real_operations_enabled=live,
            embedding_provider_approved=True,
            approved_by_panel_version="phase4_ollama_embed",
            embedding_model=OLLAMA_MODEL,
            embedding_dim=OLLAMA_EMBEDDING_DIM,
        ),
        embedding_provider=provider,
    )


def run_memory_gateway_smoke(*, live: bool, content: str = SENTINEL) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "provider": "ollama_embed",
        "host": OLLAMA_HOST,
        "endpoint": f"{OLLAMA_HOST}{OLLAMA_ENDPOINT_PATH}",
        "endpoint_path": OLLAMA_ENDPOINT_PATH,
        "model": OLLAMA_MODEL,
        "embedding_dim": OLLAMA_EMBEDDING_DIM,
        "live": live,
        "content_sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        "passed": False,
    }

    if not live:
        payload["result"] = "dry_run_only"
        payload["passed"] = True
        return payload

    session_id = create_session(operator_id="memory-gateway-smoke")
    task_id = create_task(
        session_id=session_id,
        chain_id=f"memory-gateway-smoke-{session_id}",
        task_class="system_maintenance",
        task_type="memory_gateway_smoke",
        manifest_id=TOOL_MAP_MANIFEST_ID,
    )
    payload["session_id"] = session_id
    payload["task_id"] = task_id

    authorization = MemoryAuthorization(
        manifest_id=TOOL_MAP_MANIFEST_ID,
        task_id=task_id,
        read=True,
        write=True,
        max_query_results=1,
        write_requires_dedupe=True,
    )
    gateway = _make_gateway(live=True)
    write_results = gateway.write(
        [
            MemoryWriteItem(
                content=content,
                metadata={"source": "memory_gateway_smoke"},
                session_id=session_id,
                source_task_id=task_id,
            )
        ],
        authorization,
    )
    query_results = gateway.query(content, top_k=1, authorization=authorization)

    payload.update(
        {
            "write_status": write_results[0].status,
            "memory_item_id": write_results[0].memory_item_id,
            "query_result_count": len(query_results),
            "query_contains_sentinel": any(
                result.content == content for result in query_results
            ),
            "passed": (
                write_results[0].status in {"indexed", "deduped"}
                and any(result.content == content for result in query_results)
            ),
        }
    )
    return payload


def _print_text(payload: dict[str, Any]) -> None:
    for key, value in payload.items():
        print(f"{key}: {value}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run a dry-run or explicit live local Ollama MemoryGateway smoke test."
    )
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--content", default=SENTINEL)
    args = parser.parse_args()

    try:
        payload = run_memory_gateway_smoke(live=args.live, content=args.content)
    except Exception as exc:
        payload = {
            "provider": "ollama_embed",
            "host": OLLAMA_HOST,
            "endpoint": f"{OLLAMA_HOST}{OLLAMA_ENDPOINT_PATH}",
            "endpoint_path": OLLAMA_ENDPOINT_PATH,
            "model": OLLAMA_MODEL,
            "embedding_dim": OLLAMA_EMBEDDING_DIM,
            "live": args.live,
            "content_sha256": hashlib.sha256(
                args.content.encode("utf-8")
            ).hexdigest(),
            "passed": False,
            "error": exc.__class__.__name__,
            "reason": str(exc),
        }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        _print_text(payload)

    return 0 if payload.get("passed") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
