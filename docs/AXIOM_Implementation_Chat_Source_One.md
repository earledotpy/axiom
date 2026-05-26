# AXIOM Implementation Chat Source Record
Date: 2026-05-20  
Repository root: `C:\axiom`  
Runtime posture: local-first, fail-closed, non-autonomous  
Canonical baseline: `AXIOM_Implementation_v1.13.md`

This file records what was implemented, repaired, tested, and deferred during this chat. It is a source-of-truth handoff artifact for continuing implementation in a new chat or reviewing the current state.

It does not supersede the canonical AXIOM specification. Where this chat exposed host-specific behavior, those host observations are recorded separately from the canonical v1.13 design.

---

## 1. Confirmed Operating State

The implementation was performed against:

```text
C:\axiom
```

Confirmed environment signals:

```text
Python: 3.11.9
pytest: 8.4.2
venv: C:\axiom\venv
rootdir: C:\axiom
configfile: pytest.ini
Ollama host: http://localhost:11434
Installed local model: qwen3:4b
```

Confirmed Ollama `/api/show` state for `qwen3:4b`:

```text
family: qwen3
format: gguf
parameter_size: 4.7B
quantization_level: Q4_K_M
parameters:
  top_p              0.95
  presence_penalty   1.5
  temperature        1
  top_k              20
template: {{ .Prompt }}
system: None
```

Important host-specific finding:

```text
PARAMETER think false is not accepted by this installed Ollama version.
```

Attempted derived model creation failed with:

```text
Error: unknown parameter 'think'
```

Therefore AXIOM cannot currently prove `think false` from the persistent Ollama model profile. AXIOM must enforce `think=False` at `ModelGateway` runtime while treating the model-profile thinking mode as `unknown`.

---

## 2. Highest Confirmed Test Count

The suite reached:

```text
175 tests passed
```

A subsequent model-fingerprint registration slice was started and not fully validated before the chat slowdown. The expected next target after restoring `tools/register_model_fingerprint.py` and tests is:

```text
182 tests passed
```

Do not claim `182 passed` until the new chat actually runs:

```powershell
pytest tests -v
```

---

## 3. Canonical Constraints Preserved

These constraints were repeatedly preserved during implementation:

```text
- Strict sequential execution.
- No autonomous operation.
- No real model calls through ModelGateway.
- No real network fetches through NetworkGateway.
- No real sandbox process execution through SandboxGateway.
- No Telegram/operator-control plane yet.
- No safe-pass enablement yet.
- No model-profile promotion to current when thinking_mode = unknown.
- SQLite cache_size remains -32768.
- sqlite-vec vector batch cap remains 100.
- Context bundle cap remains 500 KB serialized.
- Sandbox limits remain 256 MB RAM and 60 seconds wall-clock.
- ModelGateway rejects caller think=True and injects think=False.
- PlanInjectionScanner v1.13 return contract preserved.
```

---

## 4. Foundation Implemented

### 4.1 Project and package structure

Implemented under:

```text
C:\axiom
```

Key structure:

```text
axiom\
  app\
  core\
  gateways\
  persistence\
  policy\
  security\
config\
logs\
tools\
tests\
```

Package import problems were repaired by ensuring `__init__.py` files existed and by using `pytest.ini` to make the package importable from test runs.

### 4.2 Database layer

Implemented and repaired:

```text
axiom/persistence/db.py
axiom/persistence/schema.sql
```

Confirmed behavior:

```text
- sqlite_vec loaded before vec0 schema usage
- PRAGMA foreign_keys = ON
- PRAGMA journal_mode = WAL
- PRAGMA synchronous = FULL
- PRAGMA busy_timeout = 5000
- PRAGMA cache_size = -32768
- init_db refuses to run without canonical schema.sql
- schema_migrations identifies v1.11.4
```

Early syntax/indentation issues in `db.py` were corrected:

```text
- from __future__ import annotations
- SQLITE_CACHE_SIZE_KB naming fixed
- SCHEMA_PATH = Path(__file__).with_name("schema.sql")
- sql = SCHEMA_PATH.read_text(...)
- tabs/spaces normalized
```

The SQLite `vec0` initialization issue was resolved by loading `sqlite_vec` before schema execution.

---

## 5. Manifest and Security Artifact Layer Implemented

Implemented or repaired:

```text
axiom/core/manifest_binder.py
axiom/core/tool_capability_map.py
tools/register_manifests.py
axiom/policy/schemas/manifest_schema.json
axiom/policy/schemas/tool_capability_map_schema.json
axiom/policy/security_artifacts/tool_capability_map.json
```

Confirmed:

```text
- tool_capability_map registered as security.tool_capability_map.v1
- manifest_fingerprints accepts manifest_type = tool_capability_map
- active row for tool-capability map verified
- SHA256 mismatch detection works
- ManifestBinder validates tool IDs against the loaded tool-capability map
- operator-control semantic binding enforced
```

Important repair:

```text
tools/register_manifests.py was repaired to avoid INSERT OR REPLACE.
```

Reason: `INSERT OR REPLACE` deletes/reinserts rows and can break foreign keys from tables that reference `manifest_fingerprints.manifest_id`. The repair updates existing rows in place where required.

---

## 6. Policy and Scanner Layer Implemented

Implemented:

```text
axiom/core/policy_engine.py
axiom/security/plan_injection_scanner.py
axiom/security/plan_artifact_scanner_service.py
```

Confirmed behavior:

```text
PolicyEngine:
- denies unknown tool_id
- denies tool not in allowed_tools
- denies tool in forbidden_tools
- denies when capability source missing/false
- allows when seven-step authorization passes
- requires operator_control manifests for session_controller.* tools
- checks operator command compatibility through allowed_commands

PlanInjectionScanner:
- safe-pass disabled ordinary artifacts -> checkpoint_blocked / needs_human_input
- safe-pass disabled high-risk artifacts -> quarantined / quarantined
- deterministic block dispatches by risk_class
- classifier block dispatches by risk_class
- enum values match schema domains
```

Plan artifact scanner service was integrated to persist scanner results and update parent task status according to scanner output.

---

## 7. Core Runtime Foundation Implemented

Implemented:

```text
axiom/core/state_machine.py
axiom/core/scheduler.py
axiom/core/task_committer.py
axiom/core/supervisor_monitor.py
```

Confirmed behavior:

```text
- valid task transition rules
- terminal states cannot restart
- pending -> running requires manifest_id
- one running task at a time per session
- scheduler heartbeat write/read/latest
- stale heartbeat detection
- supervisor health reports healthy/fail-closed conditions
- TaskCommitter writes heartbeat before/after status changes
```

A scheduler heartbeat schema mismatch was corrected:

```text
scheduler_heartbeat uses scheduler_state, not scheduler_status.
```

---

## 8. Repository Layer Implemented

Expanded:

```text
axiom/persistence/repositories.py
```

Implemented helper groups:

```text
- sessions
- session events
- security events
- tasks
- task status transitions
- task permissions
- manifest fingerprints
- plan artifacts
- provider usage
- provider usage lifecycle updates
- resource usage
- calibration/model profile read helpers/stubs where needed
```

### 8.1 Provider usage

Canonical provider schema discovered:

```text
provider_usage columns:
- usage_id
- session_id
- task_id
- provider
- model
- status
- estimated_input_tokens
- estimated_output_tokens
- actual_input_tokens
- actual_output_tokens
- actuals_unavailable
- charged_input_estimate
- charged_output_estimate
- error_info
- created_at
- completed_at
```

Repository helper API was aligned to use `model`, not `model_name`, and estimated/actual token fields rather than prompt/completion aliases.

Implemented:

```text
record_provider_usage()
get_provider_usage()
get_provider_usage_for_task()
get_provider_usage_for_session()
update_provider_usage_status()
```

Status lifecycle supports:

```text
started
completed
failed
rate_limited
quota_exhausted
abandoned_session_crash
```

### 8.2 Resource usage

Implemented:

```text
record_resource_usage()
get_resource_usage()
get_resource_usage_for_task()
```

Canonical resource usage enums:

```text
resource_type:
- sandbox_ram_mb
- sandbox_wall_clock_seconds
- context_bundle_kb
- estimated_input_tokens
- estimated_output_tokens
- provider_calls
- network_response_bytes

status:
- within_limit
- exceeded
- unknown
```

The earlier status strings `over_limit` and `not_limited` were corrected to `exceeded` and `unknown`.

---

## 9. Resource Accounting Implemented

Implemented:

```text
axiom/core/token_estimator.py
axiom/core/context_builder.py
axiom/core/resource_limits.py
```

### 9.1 TokenEstimator

Implemented:

```text
- fallback token estimator
- fallback margin = 1.5x
- require_within_limit()
- record_estimated_input_tokens()
- record_estimated_output_tokens()
```

Bug fixed:

```text
max_token -> max_tokens
```

### 9.2 ContextBuilder

Implemented:

```text
- stable JSON serialization
- size_bytes
- size_kb
- 500 KB default cap
- record_bundle_size() -> resource_usage context_bundle_kb
```

### 9.3 ResourceLimitEvaluator

Implemented:

```text
- passive status_for_limit()
- record_and_evaluate()
- exceeded usage can transition pending/running/needs_human_input tasks to blocked_resource_limit
```

No sandbox execution or tool execution is involved.

---

## 10. Fail-Closed Gateways Implemented

### 10.1 NetworkGateway

Implemented:

```text
axiom/gateways/network_gateway.py
```

Behavior:

```text
- deny_all by default
- allowlist_only validates host/scheme
- no real HTTP fetch
- fetch_disabled always fails closed
- record_dummy_response() records network_response_bytes for tests only
```

### 10.2 SandboxGateway

Implemented:

```text
axiom/gateways/sandbox_gateway.py
```

Behavior:

```text
- validates max_ram_mb > 0
- validates max_wall_clock_seconds > 0
- network_access must be denied
- execute_disabled always fails closed
- record_dummy_usage() records sandbox_ram_mb and sandbox_wall_clock_seconds
```

No Windows Job Object implementation yet.

### 10.3 MemoryGateway

Implemented:

```text
axiom/gateways/memory_gateway.py
```

Behavior:

```text
- verifies memory_items table
- verifies memory_item_embeddings vec0 table
- enforces max_vector_batch = 100
- query_disabled fails closed
- write_disabled fails closed
```

No embeddings, vector inserts, or semantic recall yet.

### 10.4 ModelGateway

Implemented:

```text
axiom/gateways/model_gateway.py
```

Behavior:

```text
- prepare_local_ollama_payload()
- rejects think=True
- injects think=False
- validates /api/chat and /api/generate
- call_local_ollama_disabled fails closed
- record_dummy_local_response() records provider_usage and provider_calls
```

No real Ollama generation/chat call yet.

---

## 11. Ollama Prerequisite Inspector Implemented

Implemented:

```text
axiom/gateways/ollama_prereq.py
tools/check_ollama_prereq.py
```

Behavior:

```text
- checks /api/tags
- checks model presence
- checks /api/show
- extracts details.quantization_level
- infers profile_thinking_mode from parameters only
- returns runtime_thinking_enforcement = gateway_required when profile_thinking_mode is unknown
- does not mutate database
- does not call /api/chat or /api/generate
```

Real host output:

```text
AXIOM Ollama prerequisite check: ollama_prerequisites_inspected
host: http://localhost:11434
model: qwen3:4b
reachable: True
tags_available: True
model_present: True
show_available: True
details_present: True
parameters_present: True
quantization_level: Q4_K_M
profile_thinking_mode: unknown
runtime_thinking_enforcement: gateway_required
fingerprint_registration_ready: True
```

Important correction:
Even though `fingerprint_registration_ready` can be true for inspection, the canonical schema still forbids a current profile when `thinking_mode = unknown`.

---

## 12. Model Fingerprint Registration Slice Started

File under active repair:

```text
tools/register_model_fingerprint.py
```

Current source file issue before handoff:

```text
The file was accidentally written with PowerShell here-string marker @' at line 1.
```

Observed failure:

```text
SyntaxError: unterminated string literal (detected at line 1)
```

Correct repair:

```text
Replace the file with pure Python only.
Do not include @' or '@ | Set-Content inside the Python file.
```

### 12.1 Discovered canonical model_profile_fingerprints schema

```text
profile_id INTEGER PRIMARY KEY
profile_label TEXT NOT NULL DEFAULT 'default'
model_name TEXT NOT NULL
ollama_host TEXT NOT NULL
ollama_model_tag TEXT NOT NULL
ollama_model_digest TEXT NOT NULL
quantization TEXT NOT NULL
parameter_size TEXT
model_family TEXT
model_format TEXT
thinking_mode TEXT NOT NULL CHECK IN ('disabled','enabled','unknown')
thinking_mode_rule_version TEXT
template_sha256 TEXT
system_sha256 TEXT
parameters_sha256 TEXT
details_sha256 TEXT
selected_profile_sha256 TEXT NOT NULL UNIQUE
calibration_run_id TEXT NOT NULL
is_current INTEGER NOT NULL DEFAULT 0 CHECK IN (0,1)
registration_status TEXT NOT NULL DEFAULT 'candidate'
  CHECK IN ('candidate','current','superseded','rejected')
registered_by_tool_version TEXT NOT NULL
registered_at TEXT NOT NULL DEFAULT strftime(...)
notes TEXT
```

Schema constraints:

```text
CHECK (is_current = 0 OR thinking_mode != 'unknown')
CHECK ((is_current = 1 AND registration_status = 'current') OR (is_current = 0))
```

Foreign key:

```text
calibration_run_id -> classifier_calibration_runs(calibration_run_id)
```

### 12.2 Discovered classifier_calibration_runs schema

```text
calibration_run_id TEXT PRIMARY KEY
calibration_set_id TEXT NOT NULL
calibration_set_sha256 TEXT NOT NULL
model_name TEXT NOT NULL
ollama_host TEXT NOT NULL
threshold REAL NOT NULL CHECK 0.0 <= threshold <= 1.0
passed INTEGER NOT NULL CHECK IN (0,1)
true_positive_count INTEGER NOT NULL DEFAULT 0
true_negative_count INTEGER NOT NULL DEFAULT 0
false_positive_count INTEGER NOT NULL DEFAULT 0
false_negative_count INTEGER NOT NULL DEFAULT 0
false_positive_rate REAL
false_negative_rate REAL
approved_by_panel_version TEXT NOT NULL
details_json TEXT
created_at TEXT NOT NULL DEFAULT strftime(...)
```

### 12.3 Correct model fingerprint state machine

```text
profile_thinking_mode = unknown:
  thinking_mode = unknown
  thinking_mode_rule_version = gateway_required_v1
  registration_status = candidate
  is_current = 0

profile_thinking_mode = disabled:
  thinking_mode = disabled
  thinking_mode_rule_version = profile_verified_v1
  registration_status = current
  is_current = 1
  demote prior current profile with same profile_label:
    is_current = 0
    registration_status = superseded
```

### 12.4 Pending restored source for tools/register_model_fingerprint.py

Use this exact pure-Python source:

```python
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from axiom.gateways.ollama_prereq import OllamaPrereqInspector
from axiom.persistence.db import get_connection


TOOL_VERSION = "register_model_fingerprint.v1"


class ModelFingerprintRegistrationError(RuntimeError):
    pass


def sha256_text(value: Any) -> str | None:
    if value is None:
        return None

    if not isinstance(value, str):
        value = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )

    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def stable_sha256_json(payload: dict[str, Any]) -> str:
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_profile_payload(result, calibration_run_id: str) -> dict[str, Any]:
    raw_show = result.raw_show or {}
    details = raw_show.get("details") or {}

    return {
        "ollama_host": result.host,
        "model_name": result.model,
        "ollama_model_tag": result.model,
        "ollama_model_digest": (
            raw_show.get("digest")
            or raw_show.get("model_info", {}).get("general.basename")
            or f"unavailable:{result.model}"
        ),
        "quantization": result.quantization_level,
        "parameter_size": details.get("parameter_size"),
        "model_family": details.get("family"),
        "model_format": details.get("format"),
        "thinking_mode": result.profile_thinking_mode,
        "runtime_thinking_enforcement": result.runtime_thinking_enforcement,
        "template": raw_show.get("template"),
        "system": raw_show.get("system"),
        "parameters": raw_show.get("parameters"),
        "details": details,
        "calibration_run_id": calibration_run_id,
    }


def ensure_classifier_calibration_run(
    calibration_run_id: str,
    model: str,
    host: str,
) -> None:
    with get_connection() as conn:
        existing = conn.execute(
            """
            SELECT calibration_run_id
            FROM classifier_calibration_runs
            WHERE calibration_run_id = ?
            """,
            (calibration_run_id,),
        ).fetchone()

        if existing is not None:
            return

        conn.execute(
            """
            INSERT INTO classifier_calibration_runs
            (calibration_run_id, calibration_set_id, calibration_set_sha256,
             model_name, ollama_host, threshold, passed,
             true_positive_count, true_negative_count,
             false_positive_count, false_negative_count,
             false_positive_rate, false_negative_rate,
             approved_by_panel_version, details_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                calibration_run_id,
                "pending_calibration_set",
                "0" * 64,
                model,
                host,
                0.0,
                0,
                0,
                0,
                0,
                0,
                None,
                None,
                "pending_panel_approval",
                json.dumps(
                    {
                        "status": "pending_calibration",
                        "created_by": TOOL_VERSION,
                        "note": (
                            "Placeholder FK target only; not an approved "
                            "classifier calibration."
                        ),
                    },
                    sort_keys=True,
                    ensure_ascii=False,
                ),
            ),
        )


def resolve_registration_state(
    profile_thinking_mode: str,
    requested_registration_status: str,
) -> tuple[int, str]:
    if profile_thinking_mode == "unknown":
        return 0, "candidate"

    if requested_registration_status == "candidate":
        return 1, "current"

    if requested_registration_status == "current":
        return 1, "current"

    return 0, requested_registration_status


def register_model_fingerprint(
    host: str = "http://localhost:11434",
    model: str = "qwen3:4b",
    profile_label: str = "default",
    calibration_run_id: str = "pending_calibration",
    timeout_seconds: int = 5,
    registration_status: str = "candidate",
) -> int:
    result = OllamaPrereqInspector(
        host=host,
        model=model,
        timeout_seconds=timeout_seconds,
    ).inspect()

    if not result.reachable:
        raise ModelFingerprintRegistrationError("Ollama host is not reachable")

    if not result.model_present:
        raise ModelFingerprintRegistrationError(f"Ollama model is not present: {model}")

    if not result.show_available:
        raise ModelFingerprintRegistrationError(
            f"Ollama /api/show unavailable for model: {model}"
        )

    if not result.details_present:
        raise ModelFingerprintRegistrationError("/api/show details missing")

    if not result.quantization_level:
        raise ModelFingerprintRegistrationError(
            "/api/show details.quantization_level missing"
        )

    if result.runtime_thinking_enforcement not in {"profile_verified", "gateway_required"}:
        raise ModelFingerprintRegistrationError(
            f"Invalid runtime thinking enforcement: {result.runtime_thinking_enforcement}"
        )

    if registration_status not in {"candidate", "current", "superseded", "rejected"}:
        raise ModelFingerprintRegistrationError(
            f"Invalid registration_status: {registration_status}"
        )

    raw_show = result.raw_show or {}
    details = raw_show.get("details") or {}

    profile_payload = build_profile_payload(result, calibration_run_id)
    selected_profile_sha256 = stable_sha256_json(profile_payload)

    template_sha256 = sha256_text(raw_show.get("template"))
    system_sha256 = sha256_text(raw_show.get("system"))
    parameters_sha256 = sha256_text(raw_show.get("parameters"))
    details_sha256 = sha256_text(details)

    ollama_model_digest = (
        raw_show.get("digest")
        or raw_show.get("model_info", {}).get("general.basename")
        or f"unavailable:{model}"
    )

    requested_current, effective_registration_status = resolve_registration_state(
        profile_thinking_mode=result.profile_thinking_mode,
        requested_registration_status=registration_status,
    )

    thinking_mode_rule_version = (
        "gateway_required_v1"
        if result.runtime_thinking_enforcement == "gateway_required"
        else "profile_verified_v1"
    )

    notes = json.dumps(
        {
            "runtime_thinking_enforcement": result.runtime_thinking_enforcement,
            "profile_thinking_mode": result.profile_thinking_mode,
            "fingerprint_registration_ready": result.fingerprint_registration_ready,
            "raw_show_digest_available": raw_show.get("digest") is not None,
            "registration_note": (
                "Profiles with thinking_mode='unknown' are recorded as "
                "candidate/non-current due to canonical schema constraints."
            ),
        },
        sort_keys=True,
        ensure_ascii=False,
    )

    ensure_classifier_calibration_run(
        calibration_run_id=calibration_run_id,
        model=model,
        host=host,
    )

    with get_connection() as conn:
        if requested_current == 1:
            conn.execute(
                """
                UPDATE model_profile_fingerprints
                SET is_current = 0,
                    registration_status = 'superseded'
                WHERE profile_label = ?
                  AND is_current = 1
                """,
                (profile_label,),
            )

        cur = conn.execute(
            """
            INSERT INTO model_profile_fingerprints
            (profile_label, model_name, ollama_host, ollama_model_tag,
             ollama_model_digest, quantization, parameter_size, model_family,
             model_format, thinking_mode, thinking_mode_rule_version,
             template_sha256, system_sha256, parameters_sha256, details_sha256,
             selected_profile_sha256, calibration_run_id, is_current,
             registration_status, registered_by_tool_version, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                profile_label,
                model,
                host,
                model,
                ollama_model_digest,
                result.quantization_level,
                details.get("parameter_size"),
                details.get("family"),
                details.get("format"),
                result.profile_thinking_mode,
                thinking_mode_rule_version,
                template_sha256,
                system_sha256,
                parameters_sha256,
                details_sha256,
                selected_profile_sha256,
                calibration_run_id,
                requested_current,
                effective_registration_status,
                TOOL_VERSION,
                notes,
            ),
        )

        return int(cur.lastrowid)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Register AXIOM local Ollama model fingerprint."
    )
    parser.add_argument("--host", default="http://localhost:11434")
    parser.add_argument("--model", default="qwen3:4b")
    parser.add_argument("--profile-label", default="default")
    parser.add_argument("--calibration-run-id", default="pending_calibration")
    parser.add_argument("--registration-status", default="candidate")
    parser.add_argument("--timeout", type=int, default=5)
    args = parser.parse_args()

    profile_id = register_model_fingerprint(
        host=args.host,
        model=args.model,
        profile_label=args.profile_label,
        calibration_run_id=args.calibration_run_id,
        registration_status=args.registration_status,
        timeout_seconds=args.timeout,
    )

    print(f"registered model profile fingerprint {profile_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

---

## 13. Test Files Added or Repaired During This Chat

Added or repaired:

```text
tests/test_sqlite_wal_mode.py
tests/test_schema_v1114_amendments.py
tests/test_model_gateway.py
tests/test_model_fingerprint_guard.py
tests/test_plan_injection_scanner.py
tests/test_policy_engine.py
tests/test_manifest_binder.py
tests/test_bootstrap_validation.py
tests/test_scheduler_foundation.py
tests/test_task_committer.py
tests/test_token_estimator.py
tests/test_context_builder.py
tests/test_resource_usage.py
tests/test_resource_accounting_integration.py
tests/test_resource_limits.py
tests/test_network_gateway.py
tests/test_sandbox_gateway.py
tests/test_memory_gateway.py
tests/test_model_gateway_wrapper.py
tests/test_provider_usage.py
tests/test_provider_usage_lifecycle.py
tests/test_ollama_prereq.py
tests/test_register_model_fingerprint.py
```

The last file is still part of the active model-fingerprint slice; rerun after restoring `register_model_fingerprint.py`.

---

## 14. Commands to Continue From This Source Record

First verify the broken file is fixed:

```powershell
Get-Content C:\axiom\tools\register_model_fingerprint.py -TotalCount 3
```

Expected:

```text
from __future__ import annotations

import argparse
```

Then:

```powershell
python -m py_compile C:\axiom\tools\register_model_fingerprint.py
pytest tests\test_register_model_fingerprint.py -v
```

Expected after repair:

```text
7 passed
```

Then:

```powershell
pytest tests -v
```

Expected target after repair:

```text
182 passed
```

Then register the real local model profile:

```powershell
python tools\register_model_fingerprint.py --model qwen3:4b --profile-label default
```

Expected:

```text
registered model profile fingerprint <id>
```

Then inspect:

```powershell
@'
from axiom.persistence.db import get_connection

with get_connection() as conn:
    row = conn.execute(
        """
        SELECT profile_id, profile_label, model_name, ollama_host,
               ollama_model_tag, ollama_model_digest, quantization,
               parameter_size, model_family, model_format, thinking_mode,
               thinking_mode_rule_version, calibration_run_id,
               is_current, registration_status, notes
        FROM model_profile_fingerprints
        WHERE profile_label = 'default'
        ORDER BY profile_id DESC
        LIMIT 1
        """
    ).fetchone()

    print(dict(row))
'@ | python
```

Expected important fields:

```text
thinking_mode: unknown
thinking_mode_rule_version: gateway_required_v1
is_current: 0
registration_status: candidate
calibration_run_id: pending_calibration
```

This result is correct because the host cannot persist `think false` at the model-profile level.

---

## 15. Deferred Items Still Not Implemented

Do not proceed into these without explicit approval and verified prerequisites:

```text
- Autonomous scheduler loop
- Safe-pass enablement
- Classifier calibration approval
- Real Ollama chat/generate calls
- Real NetworkGateway fetches
- Real SandboxGateway process execution / Windows Job Objects
- Real MemoryGateway embedding writes/query
- Telegram operator control plane
- Cloud cascade
- Open WebUI integration
- Host hardening installer/guide
```

---

## 16. AXIOM Terminal / Operator UI Notes

The project context now assumes AXIOM Terminal is Jeremy’s default implementation shell:

```text
C:\axiom\ui\terminal
```

Known desired terminal wrappers from previous context:

```text
axiom-status     -> python tools\verify_foundation.py
axiom-audit      -> lifecycle + execution audits
axiom-health     -> supervisor health for latest session
axiom-preflight  -> foundation + lifecycle + execution + supervisor health
axiom-regression -> pytest tests -v
axiom-handoff    -> snapshot/handoff/bundle
axiom-edit / ae  -> terminal-native editor
```

Terminal commands should remain wrappers around approved tools and read-only diagnostics. State-changing terminal commands must not bypass AXIOM policy/audit behavior.

---

## 17. Practical Implementation Lessons From This Chat

1. Do not put PowerShell here-string markers inside Python files.
2. Schema constraints are authoritative; patch code/tests to schema, not schema to tests.
3. For `manifest_fingerprints`, do not use `INSERT OR REPLACE`; it can break FKs.
4. For model profiles:
   - `thinking_mode = unknown` cannot be current.
   - current profile requires `registration_status = current`.
   - `calibration_run_id` must exist.
5. Ollama host behavior differs from the original assumption:
   - `PARAMETER think false` is not supported in this environment.
   - runtime `think=False` enforcement remains necessary.
6. Each new slice should run targeted tests first, then full regression.
7. Current working verification pattern:
   ```powershell
   python -m py_compile <changed_file>
   pytest <targeted_test_file> -v
   pytest tests -v
   ```

---

End of source record.
