from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "phase4.md"


def test_phase4_gateway_readiness_doc_exists():
    assert DOC.exists()


def test_phase4_gateway_readiness_doc_records_safe_posture():
    text = DOC.read_text(encoding="utf-8")

    required = [
        "Phase 4 is authorized for bounded implementation",
        "fail_closed_non_autonomous",
        "autonomous_allowed = False",
        "safe_pass_enabled = False",
        "ModelGateway cloud-cascade readiness validation",
        "ModelGateway cloud-cascade HTTP execution",
        "ModelGateway operator-facing cloud cascade smoke wrapper/reporting",
        "MemoryGateway sqlite-vec invariant hardening",
        "MemoryGateway write/query readiness",
        "MemoryGateway local Ollama `/api/embed` provider adapter",
        "operator smoke wrapper behind explicit `--live`",
        "NetworkGateway Brave Search readiness/execution",
        "SandboxGateway Windows Job Object readiness/execution",
        "API keys are read only from configured environment variable names",
        "They are never written to provider_usage, resource_usage, or test output",
        "The test suite uses injected HTTP transports",
        "does not make real cloud requests",
        "does not call a live embedding model or external embedding API",
        "does not perform real local Ollama `/api/chat` or `/api/generate` calls",
    ]

    for phrase in required:
        assert phrase in text


def test_phase4_gateway_readiness_doc_records_readiness_contract():
    text = DOC.read_text(encoding="utf-8")

    required = [
        "provider_configuration_approved must be true",
        "approved_by_panel_version must be present when approved",
        "provider_order must contain known cloud providers only",
        "provider_order must not contain duplicates",
        "providers must contain known cloud providers only",
        "providers must not contain duplicates",
        "enabled providers must declare a model",
        "enabled providers must declare an API key environment variable name",
        "provider endpoint URLs must use https",
        "provider timeout seconds must be positive",
        "cerebras",
        "groq",
        "openrouter",
        "sambanova",
        "CloudCascadeNotApprovedError",
        "ModelGatewayDisabledError",
        "real_calls_enabled",
        "CloudCredentialsError",
        "provider HTTP failures record terminal provider_usage status and continue failover",
        "invalid provider responses record failed provider_usage status",
        "CloudModelResponse.response_text",
        "https://api.cerebras.ai/v1/chat/completions",
        "https://api.groq.com/openai/v1/chat/completions",
        "https://openrouter.ai/api/v1/chat/completions",
        "https://api.sambanova.ai/v1/chat/completions",
    ]

    for phrase in required:
        assert phrase in text


def test_phase4_gateway_readiness_doc_records_memory_invariant_contract():
    text = DOC.read_text(encoding="utf-8")

    required = [
        "memory_items table must exist",
        "memory_item_embeddings sqlite-vec table must exist",
        "memory_item_embeddings must use vec0",
        "memory_item_embeddings.embedding must be float[768]",
        "memory_items.embedding_dim must default to 768",
        "memory_items.embedding_dim must CHECK embedding_dim = 768",
        "idx_memory_items_content_model must be a unique index",
        "idx_memory_items_content_model must cover content_sha256 and embedding_model",
        "sqlite-vec batches remain capped at 100 vectors",
        "require_invariants raises MemoryGatewayError when invariants drift",
        "query_disabled still raises MemoryGatewayDisabledError",
        "write_disabled still raises MemoryGatewayDisabledError",
        "write requires MemoryGatewayConfig.real_operations_enabled",
        "write/query require embedding_provider_approved",
        "write/query require approved_by_panel_version",
        "write/query require an injected embedding provider",
        "write/query require manifest authorization metadata",
        "write requires memory write authorization",
        "write requires write_requires_dedupe",
        "query requires memory read authorization",
        "query enforces max_query_results",
        "hashes content with SHA256 before insert",
        "dedupes by content_sha256 and embedding_model",
        "inserts memory_items rows as pending before vector insert",
        "inserts memory_item_embeddings rows with rowid equal to memory_item_id",
        "updates embedding_status to indexed after vector insert",
        "queries sqlite-vec with MATCH and k",
        "returns indexed memory_items ordered by sqlite-vec distance",
    ]

    for phrase in required:
        assert phrase in text


def test_phase4_gateway_readiness_doc_records_memory_ollama_provider_contract():
    text = DOC.read_text(encoding="utf-8")

    required = [
        "MemoryGateway local Ollama /api/embed embedding provider adapter",
        "MemoryGateway operator-facing local Ollama smoke wrapper/reporting",
        "provider: ollama_embed",
        "host: http://localhost:11434",
        "endpoint: /api/embed",
        "model: nomic-embed-text",
        "embedding_dim: 768",
        "Ollama host must use http",
        "Ollama host must be localhost, 127.0.0.1, or ::1",
        "Ollama port must be 11434",
        "Ollama endpoint path must be /api/embed",
        "Ollama response must include an embeddings list",
        "Ollama embeddings must match embedding_dim 768",
        "real local Ollama embedding calls require MemoryGateway real-operation gates",
        "real local Ollama embedding calls require operator smoke --live",
        "vector values are not printed by the operator smoke wrapper",
        "does not call `/api/chat` or `/api/generate`",
        r"python tools\memory_gateway_smoke_test.py",
        r"python tools\memory_gateway_smoke_test.py --live",
        "Real local Ollama `/api/embed` write/query calls require `--live`",
        "Live local Ollama embedding smoke completed",
        "ollama_embed -> nomic-embed-text -> AXIOM_MEMORY_SMOKE_OK",
        "endpoint: http://localhost:11434/api/embed",
        "session_id: 4592",
        "task_id: 3915",
        "write_status: indexed",
        "query_result_count: 1",
        "query_contains_sentinel: true",
        "fake HTTP transports",
    ]

    for phrase in required:
        assert phrase in text


def test_phase4_gateway_readiness_doc_records_network_gateway_contract():
    text = DOC.read_text(encoding="utf-8")

    required = [
        "NetworkGateway Brave Search readiness and execution",
        "brave_search",
        "endpoint: https://api.search.brave.com/res/v1/web/search",
        "api key env var: BRAVE_SEARCH_API_KEY",
        "header: X-Subscription-Token",
        "official Brave Search API documentation and pricing surface",
        "monthly free credits and 50 requests per second capacity",
        "fetch_disabled still raises NetworkAccessDeniedError",
        "real Brave fetch requires NetworkGatewayConfig.real_fetch_enabled",
        "real Brave fetch requires provider_configuration_approved",
        "real Brave fetch requires approved_by_panel_version",
        "real Brave fetch requires BRAVE_SEARCH_API_KEY",
        "provider endpoint must use https",
        "provider endpoint host must be api.search.brave.com",
        "provider endpoint path must be /res/v1/web/search",
        "network policy must be allowlist_only",
        "allowlist must include api.search.brave.com",
        "redirect_policy must be deny",
        "Brave count must be between 1 and 20",
        "response bytes are recorded before success or failure",
        "API key values are not written to resource_usage or smoke output",
        r"python tools\network_gateway_smoke_test.py",
        r"python tools\network_gateway_smoke_test.py --live",
        "Real Brave Search network calls require `--live`",
    ]

    for phrase in required:
        assert phrase in text


def test_phase4_gateway_readiness_doc_records_sandbox_gateway_contract():
    text = DOC.read_text(encoding="utf-8")

    required = [
        "SandboxGateway Windows Job Object readiness and execution",
        "windows_job_object",
        "max_ram_mb: 256",
        "max_wall_clock_seconds: 60",
        "network_access: denied",
        "kill_on_job_close: true",
        "active_process_limit: 1",
        "execute_disabled still raises SandboxExecutionDeniedError",
        "real sandbox execution requires SandboxGatewayConfig.real_execution_enabled",
        "real sandbox execution requires windows_job_object_approved",
        "real sandbox execution requires approved_by_panel_version",
        "real sandbox execution requires manifest authorization metadata",
        "real sandbox execution requires allow_execute",
        "max_ram_mb cannot exceed 256",
        "max_wall_clock_seconds cannot exceed 60",
        "network_access must remain denied",
        "active_process_limit must remain 1",
        "kill_on_job_close must remain enabled",
        "process is created suspended before Job Object assignment",
        "Job Object sets process memory and job memory caps",
        "Job Object enforces active process limit 1",
        "wall-clock timeout terminates the Job Object",
        "RAM and wall-clock usage are recorded before success or failure",
        r"python tools\sandbox_gateway_smoke_test.py",
        r"python tools\sandbox_gateway_smoke_test.py --live",
        "Real sandbox process execution requires `--live`",
    ]

    for phrase in required:
        assert phrase in text


def test_phase4_gateway_readiness_doc_records_live_cloud_smoke_status():
    text = DOC.read_text(encoding="utf-8")

    required = [
        "Live smoke tests completed",
        "groq -> llama-3.3-70b-versatile -> AXIOM_GROQ_SMOKE_OK",
        "cerebras -> gpt-oss-120b -> AXIOM_CEREBRAS_SMOKE_OK",
        "sambanova -> Meta-Llama-3.3-70B-Instruct -> AXIOM_SAMBANOVA_SMOKE_OK",
        "openrouter -> openrouter/auto -> AXIOM_OPENROUTER_SMOKE_OK",
        "full cascade -> groq primary -> AXIOM_CLOUD_CASCADE_SMOKE_OK",
        "Validated live cascade order",
        "cerebras max_tokens: 96",
        "openrouter max_tokens: 256",
        r"python tools\cloud_cascade_smoke_test.py --target cascade",
        r"python tools\cloud_cascade_smoke_test.py --target cascade --live",
        "Real cloud model calls require `--live`",
    ]

    for phrase in required:
        assert phrase in text


def test_phase4_gateway_readiness_doc_records_verification_commands():
    text = DOC.read_text(encoding="utf-8")

    required = [
        r"python -m py_compile axiom\gateways\model_gateway.py axiom\gateways\memory_gateway.py axiom\gateways\network_gateway.py axiom\gateways\sandbox_gateway.py",
        r"pytest tests\test_model_gateway_wrapper.py tests\test_memory_gateway.py tests\test_network_gateway.py tests\test_sandbox_gateway.py",
        r"python tools\memory_gateway_smoke_test.py --json",
        "pytest tests -v",
        r"python tools\verify_foundation.py",
        r"python tools\audit_task_lifecycle.py",
        r"python tools\audit_task_execution.py",
        r"python tools\audit_policy_security.py",
    ]

    for phrase in required:
        assert phrase in text


def test_phase4_gateway_readiness_doc_preserves_prohibited_boundaries():
    text = DOC.read_text(encoding="utf-8")

    prohibited = [
        "real Ollama /api/chat or /api/generate calls",
        "unauthorized real cloud model/provider calls outside ModelGateway cloud cascade",
        "ungated real NetworkGateway fetches outside approved Brave Search wrapper",
        "ungated real SandboxGateway process execution outside approved Windows Job Object wrapper",
        "ungated live MemoryGateway embedding-provider calls",
        "autonomous operation",
        "safe-pass enablement",
        "model profile promotion",
        "classifier calibration approval",
        "Telegram/operator control plane",
        "agent layer",
        "persistent scheduler service",
        "automatic scheduler-to-executor integration",
    ]

    for phrase in prohibited:
        assert phrase in text


def test_phase4_gateway_readiness_doc_lists_remaining_phase4_work():
    text = DOC.read_text(encoding="utf-8")

    required = [
        "Remaining Phase 4 implementation is:",
        "none",
        r"docs\phase4.md",
    ]

    for phrase in required:
        assert phrase in text

