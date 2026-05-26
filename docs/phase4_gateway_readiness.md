# AXIOM Phase 4 Gateway Readiness

## Status

Phase 4 is authorized for bounded implementation.

AXIOM remains:

```text
fail_closed_non_autonomous
autonomous_allowed = False
safe_pass_enabled = False
```

The current Phase 4 slices implement ModelGateway cloud-cascade readiness validation, ModelGateway cloud-cascade HTTP execution behind explicit `real_calls_enabled`, MemoryGateway sqlite-vec invariant hardening, MemoryGateway write/query readiness behind explicit real-operation enablement plus injected embedding providers, MemoryGateway local Ollama `/api/embed` provider adapter plus operator smoke wrapper behind explicit `--live`, NetworkGateway Brave Search readiness/execution behind explicit `real_fetch_enabled`, and SandboxGateway Windows Job Object readiness/execution behind explicit `real_execution_enabled`. This does not perform real local Ollama `/api/chat` or `/api/generate` calls, Telegram/operator control execution, agent execution, persistent scheduling, or automatic scheduler-to-executor integration.

## Implemented slice

The implemented Phase 4 slice is:

```text
ModelGateway cloud cascade readiness
ModelGateway cloud cascade HTTP execution
ModelGateway operator-facing cloud cascade smoke wrapper/reporting
MemoryGateway sqlite-vec invariant hardening
MemoryGateway real write/query readiness
MemoryGateway local Ollama /api/embed embedding provider adapter
MemoryGateway operator-facing local Ollama smoke wrapper/reporting
NetworkGateway Brave Search readiness and execution
SandboxGateway Windows Job Object readiness and execution
```

Implementation files:

```text
axiom/gateways/model_gateway.py
axiom/gateways/memory_gateway.py
tools/cloud_cascade_smoke_test.py
tools/network_gateway_smoke_test.py
tools/sandbox_gateway_smoke_test.py
tools/memory_gateway_smoke_test.py
tests/test_model_gateway_wrapper.py
tests/test_memory_gateway.py
tests/test_network_gateway.py
tests/test_sandbox_gateway.py
tests/test_cloud_cascade_smoke_test.py
tests/test_network_gateway_smoke_test.py
tests/test_sandbox_gateway_smoke_test.py
tests/test_memory_gateway_smoke_test.py
```

The readiness contract verifies:

```text
provider_configuration_approved must be true
approved_by_panel_version must be present when approved
provider_order must contain known cloud providers only
provider_order must not contain duplicates
providers must contain known cloud providers only
providers must not contain duplicates
enabled providers must declare a model
enabled providers must declare an API key environment variable name
provider endpoint URLs must use https
provider timeout seconds must be positive
```

Approved cloud provider identifiers remain limited to:

```text
cerebras
groq
openrouter
sambanova
```

The call boundary remains fail-closed:

```text
unapproved cloud cascade raises CloudCascadeNotApprovedError
ready cloud cascade raises ModelGatewayDisabledError unless real_calls_enabled is true
missing provider API key environment variables raise CloudCredentialsError
provider HTTP failures record terminal provider_usage status and continue failover
invalid provider responses record failed provider_usage status
```

API keys are read only from configured environment variable names. They are never written to provider_usage, resource_usage, or test output. Provider calls use OpenAI-compatible chat completion payloads and normalize the first returned message/text into `CloudModelResponse.response_text`.

Operator smoke output does not serialize raw provider responses. Live cloud smoke reports provider/model, usage IDs, response length, and sentinel match status.

Default cloud chat completion endpoints:

```text
cerebras: https://api.cerebras.ai/v1/chat/completions
groq: https://api.groq.com/openai/v1/chat/completions
openrouter: https://openrouter.ai/api/v1/chat/completions
sambanova: https://api.sambanova.ai/v1/chat/completions
```

The test suite uses injected HTTP transports. It does not use real API keys and does not make real cloud requests.

Live smoke tests completed:

```text
groq -> llama-3.3-70b-versatile -> AXIOM_GROQ_SMOKE_OK
cerebras -> gpt-oss-120b -> AXIOM_CEREBRAS_SMOKE_OK
sambanova -> Meta-Llama-3.3-70B-Instruct -> AXIOM_SAMBANOVA_SMOKE_OK
openrouter -> openrouter/auto -> AXIOM_OPENROUTER_SMOKE_OK
full cascade -> groq primary -> AXIOM_CLOUD_CASCADE_SMOKE_OK
```

Validated live cascade order:

```text
groq
cerebras
sambanova
openrouter
```

Cerebras `gpt-oss-120b` and OpenRouter `openrouter/auto` need larger smoke-test output budgets than the other providers because routed/reasoning models may consume small completion budgets before returning final text. Use at least:

```text
cerebras max_tokens: 96
openrouter max_tokens: 256
```

Operator wrapper:

```text
python tools\cloud_cascade_smoke_test.py --target cascade
python tools\cloud_cascade_smoke_test.py --target cascade --live
```

The wrapper defaults to dry-run readiness and key-visibility reporting. It does not print API key values. Real cloud model calls require `--live`.

The MemoryGateway invariant contract verifies:

```text
memory_items table must exist
memory_item_embeddings sqlite-vec table must exist
memory_item_embeddings must use vec0
memory_item_embeddings.embedding must be float[768]
memory_items.embedding_dim must default to 768
memory_items.embedding_dim must CHECK embedding_dim = 768
idx_memory_items_content_model must be a unique index
idx_memory_items_content_model must cover content_sha256 and embedding_model
sqlite-vec batches remain capped at 100 vectors
```

The MemoryGateway boundary remains fail-closed:

```text
require_invariants raises MemoryGatewayError when invariants drift
query_disabled still raises MemoryGatewayDisabledError
write_disabled still raises MemoryGatewayDisabledError
write requires MemoryGatewayConfig.real_operations_enabled
write/query require embedding_provider_approved
write/query require approved_by_panel_version
write/query require an injected embedding provider
write/query require manifest authorization metadata
write requires memory write authorization
write requires write_requires_dedupe
query requires memory read authorization
query enforces max_query_results
```

The implemented write/query readiness path:

```text
hashes content with SHA256 before insert
dedupes by content_sha256 and embedding_model
inserts memory_items rows as pending before vector insert
inserts memory_item_embeddings rows with rowid equal to memory_item_id
updates embedding_status to indexed after vector insert
queries sqlite-vec with MATCH and k
returns indexed memory_items ordered by sqlite-vec distance
keeps sqlite-vec batches capped at 100 vectors
```

The MemoryGateway local embedding provider is:

```text
provider: ollama_embed
host: http://localhost:11434
endpoint: /api/embed
model: nomic-embed-text
embedding_dim: 768
```

The Ollama provider adapter boundary remains fail-closed:

```text
Ollama host must use http
Ollama host must be localhost, 127.0.0.1, or ::1
Ollama port must be 11434
Ollama host must not include path, query, or fragment
Ollama endpoint path must be /api/embed
Ollama timeout seconds must be positive
Ollama expected embedding dimension must be positive
Ollama response must include an embeddings list
Ollama response batch size must match requested input count
Ollama embeddings must match embedding_dim 768
real local Ollama embedding calls require MemoryGateway real-operation gates
real local Ollama embedding calls require operator smoke --live
vector values are not printed by the operator smoke wrapper
raw memory content is not printed by the operator smoke wrapper
```

The provider adapter calls only Ollama `/api/embed`. It does not call `/api/chat` or `/api/generate`.

Operator wrapper:

```text
python tools\memory_gateway_smoke_test.py
python tools\memory_gateway_smoke_test.py --live
```

The wrapper defaults to dry-run readiness reporting. Real local Ollama `/api/embed` write/query calls require `--live`.

Live local Ollama embedding smoke completed:

```text
ollama_embed -> nomic-embed-text -> AXIOM_MEMORY_SMOKE_OK
endpoint: http://localhost:11434/api/embed
session_id: 4592
task_id: 3915
write_status: indexed
query_result_count: 1
query_contains_sentinel: true
```

The test suite uses injected fake embedding providers and fake HTTP transports. It does not call a live embedding model or external embedding API during regression.

The NetworkGateway provider is:

```text
brave_search
endpoint: https://api.search.brave.com/res/v1/web/search
api key env var: BRAVE_SEARCH_API_KEY
header: X-Subscription-Token
```

The provider approval basis is the official Brave Search API documentation and pricing surface. The official docs show the web search endpoint, `X-Subscription-Token` authentication, pagination count capped at 20, and the Search plan with monthly free credits and 50 requests per second capacity.

The NetworkGateway boundary remains fail-closed:

```text
fetch_disabled still raises NetworkAccessDeniedError
real Brave fetch requires NetworkGatewayConfig.real_fetch_enabled
real Brave fetch requires provider_configuration_approved
real Brave fetch requires approved_by_panel_version
real Brave fetch requires BRAVE_SEARCH_API_KEY
provider endpoint must use https
provider endpoint host must be api.search.brave.com
provider endpoint path must be /res/v1/web/search
network policy must be allowlist_only
allowlist must include api.search.brave.com
redirect_policy must be deny
Brave count must be between 1 and 20
response bytes are recorded before success or failure
API key values are not written to resource_usage or smoke output
network smoke output does not print raw query text or provider body previews
```

Operator wrapper:

```text
python tools\network_gateway_smoke_test.py
python tools\network_gateway_smoke_test.py --live
```

The wrapper defaults to dry-run readiness and key-visibility reporting. It does not print API key values. Real Brave Search network calls require `--live`.

The SandboxGateway provider is:

```text
windows_job_object
max_ram_mb: 256
max_wall_clock_seconds: 60
network_access: denied
kill_on_job_close: true
active_process_limit: 1
```

The SandboxGateway boundary remains fail-closed:

```text
execute_disabled still raises SandboxExecutionDeniedError
real sandbox execution requires SandboxGatewayConfig.real_execution_enabled
real sandbox execution requires windows_job_object_approved
real sandbox execution requires approved_by_panel_version
real sandbox execution requires manifest authorization metadata
real sandbox execution requires allow_execute
max_ram_mb cannot exceed 256
max_wall_clock_seconds cannot exceed 60
network_access must remain denied
active_process_limit must remain 1
kill_on_job_close must remain enabled
process is created suspended before Job Object assignment
Job Object sets process memory and job memory caps
Job Object enforces active process limit 1
wall-clock timeout terminates the Job Object
RAM and wall-clock usage are recorded before success or failure
```

Operator wrapper:

```text
python tools\sandbox_gateway_smoke_test.py
python tools\sandbox_gateway_smoke_test.py --live
```

The wrapper defaults to dry-run readiness reporting. Real sandbox process execution requires `--live`.

## Current proof

Use these commands to verify this slice:

```text
python -m py_compile axiom\gateways\model_gateway.py axiom\gateways\memory_gateway.py axiom\gateways\network_gateway.py axiom\gateways\sandbox_gateway.py tools\cloud_cascade_smoke_test.py tools\network_gateway_smoke_test.py tools\sandbox_gateway_smoke_test.py tools\memory_gateway_smoke_test.py tests\test_model_gateway_wrapper.py tests\test_memory_gateway.py tests\test_network_gateway.py tests\test_sandbox_gateway.py tests\test_cloud_cascade_smoke_test.py tests\test_network_gateway_smoke_test.py tests\test_sandbox_gateway_smoke_test.py tests\test_memory_gateway_smoke_test.py tests\test_phase4_gateway_readiness_doc.py
pytest tests\test_model_gateway_wrapper.py tests\test_memory_gateway.py tests\test_network_gateway.py tests\test_sandbox_gateway.py tests\test_cloud_cascade_smoke_test.py tests\test_network_gateway_smoke_test.py tests\test_sandbox_gateway_smoke_test.py tests\test_memory_gateway_smoke_test.py tests\test_phase4_gateway_readiness_doc.py -v
python tools\memory_gateway_smoke_test.py --json
pytest tests -v
python tools\verify_foundation.py
python tools\audit_task_lifecycle.py
python tools\audit_task_execution.py
python tools\audit_policy_security.py
```

Expected posture remains:

```text
foundation_passed: True
operational_mode: fail_closed_non_autonomous
autonomous_allowed: False
safe_pass_enabled: False
fail_closed_coherent: True
policy_security_audit passed
```

## Remaining Phase 4 work

Remaining Phase 4 implementation is:

```text
none
```

Phase 4 closeout is recorded in:

```text
docs\phase4_closeout.md
```

These remain prohibited until their bounded prerequisites are provided:

```text
real Ollama /api/chat or /api/generate calls
unauthorized real cloud model/provider calls outside ModelGateway cloud cascade
ungated real NetworkGateway fetches outside approved Brave Search wrapper
ungated real SandboxGateway process execution outside approved Windows Job Object wrapper
ungated live MemoryGateway embedding-provider calls
autonomous operation
safe-pass enablement
model profile promotion
classifier calibration approval
Telegram/operator control plane
agent layer
persistent scheduler service
automatic scheduler-to-executor integration
```
