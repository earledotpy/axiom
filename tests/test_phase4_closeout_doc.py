from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "phase4_closeout.md"


def test_phase4_closeout_doc_exists():
    assert DOC.exists()


def test_phase4_closeout_doc_records_closed_safe_posture():
    text = DOC.read_text(encoding="utf-8")

    required = [
        "Phase 4 is closed",
        "fail_closed_non_autonomous",
        "autonomous_allowed = False",
        "safe_pass_enabled = False",
        "does not authorize autonomous operation",
        "does not authorize autonomous operation, safe-pass enablement, agent execution, Telegram/operator control execution, or scheduler-to-executor automation",
    ]

    for phrase in required:
        assert phrase in text


def test_phase4_closeout_doc_records_completed_gateway_surface():
    text = DOC.read_text(encoding="utf-8")

    required = [
        "ModelGateway cloud cascade readiness validation",
        "ModelGateway bounded cloud cascade HTTP execution",
        "MemoryGateway sqlite-vec invariant hardening",
        "MemoryGateway real write/query readiness",
        "MemoryGateway local Ollama /api/embed embedding provider adapter",
        "NetworkGateway Brave Search readiness and execution",
        "SandboxGateway Windows Job Object execution boundary",
        "Operator command index v10 gateway smoke registration",
        "cloud model calls require real_calls_enabled and --live smoke intent",
        "Brave Search fetches require real_fetch_enabled and --live smoke intent",
        "Windows Job Object execution requires real_execution_enabled and --live smoke intent",
        "MemoryGateway write/query requires real_operations_enabled",
    ]

    for phrase in required:
        assert phrase in text


def test_phase4_closeout_doc_records_live_smoke_proof():
    text = DOC.read_text(encoding="utf-8")

    required = [
        "groq -> llama-3.3-70b-versatile -> AXIOM_GROQ_SMOKE_OK",
        "cerebras -> gpt-oss-120b -> AXIOM_CEREBRAS_SMOKE_OK",
        "sambanova -> Meta-Llama-3.3-70B-Instruct -> AXIOM_SAMBANOVA_SMOKE_OK",
        "openrouter -> openrouter/auto -> AXIOM_OPENROUTER_SMOKE_OK",
        "full cloud cascade -> groq primary -> AXIOM_CLOUD_CASCADE_SMOKE_OK",
        "brave_search -> status 200 -> response_bytes 14152",
        "windows_job_object -> cmd.exe /c exit 0 -> exit_code 0",
        "ollama_embed -> nomic-embed-text -> AXIOM_MEMORY_SMOKE_OK",
        "NetworkGateway Brave Search: session_id 4587, task_id 3910",
        "SandboxGateway Windows Job Object: session_id 4591, task_id 3914",
        "MemoryGateway Ollama embedding: session_id 4592, task_id 3915",
    ]

    for phrase in required:
        assert phrase in text


def test_phase4_closeout_doc_records_current_proof_commands():
    text = DOC.read_text(encoding="utf-8")

    required = [
        "pytest tests -v",
        "467 passed",
        r"python tools\memory_gateway_smoke_test.py --live --json",
        "query_contains_sentinel: true",
        r"python tools\verify_foundation.py",
        r"python tools\audit_task_lifecycle.py",
        r"python tools\audit_task_execution.py",
        r"python tools\audit_policy_security.py",
        "policy_security_audit passed",
        "checked_count: 15",
        "violation_count: 0",
        "tests\\test_phase4_closeout_doc.py",
    ]

    for phrase in required:
        assert phrase in text


def test_phase4_closeout_doc_preserves_prohibitions():
    text = DOC.read_text(encoding="utf-8")

    prohibited = [
        "autonomous operation",
        "safe-pass enablement",
        "model profile promotion",
        "classifier calibration approval",
        "real Ollama /api/chat or /api/generate calls",
        "cloud model calls outside the approved ModelGateway cloud cascade",
        "network fetches outside the approved Brave Search NetworkGateway wrapper",
        "sandbox execution outside the approved Windows Job Object SandboxGateway wrapper",
        "MemoryGateway embedding writes/query outside approved real-operation gates",
        "Telegram/operator control plane",
        "agent layer",
        "persistent scheduler service",
        "automatic scheduler-to-executor integration",
        "unbounded provider, network, sandbox, or memory execution",
    ]

    for phrase in prohibited:
        assert phrase in text


def test_phase4_closeout_doc_records_phase5_transition_checklist():
    text = DOC.read_text(encoding="utf-8")

    required = [
        "Jeremy explicitly authorizes Phase 5",
        "Phase 5 objective and bounded first slice are named",
        "Phase 5 authority expansion, if any, is stated explicitly",
        "any new provider, agent, scheduler, Telegram, or autonomous surface has a written gate",
        "rollback and smoke-test commands are identified before implementation",
        "existing Phase 4 smoke wrappers remain dry-run by default",
        "standard audits pass before and after the first Phase 5 slice",
        "No Phase 4 implementation item remains before Phase 5",
        "Phase 5 must not begin until Jeremy explicitly authorizes the next bounded slice and its prerequisites",
    ]

    for phrase in required:
        assert phrase in text
