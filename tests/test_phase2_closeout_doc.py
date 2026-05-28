from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "phase2.md"


def test_phase2_closeout_doc_exists():
    assert DOC.exists()


def test_phase2_closeout_doc_records_required_phase2_proof():
    text = DOC.read_text(encoding="utf-8")

    required = [
        "Phase 2 is closed",
        "fail_closed_non_autonomous",
        "autonomous_allowed = False",
        "safe_pass_enabled = False",
        "StateMachine",
        "Scheduler",
        "TaskCommitter",
        "SupervisorMonitor",
        "manual no-op execution harness",
        "manual no-op staging",
        "manual scheduler-dispatched no-op cycle",
        "execution_readiness.ready becomes True",
        "task_lifecycle_audit passes",
        "task_execution_audit passes",
        "supervisor_health_check reports supervisor_health_ok",
        "verify_foundation reports foundation_passed: True",
        "pytest tests -v passes",
    ]

    for phrase in required:
        assert phrase in text


def test_phase2_closeout_doc_preserves_prohibited_boundaries():
    text = DOC.read_text(encoding="utf-8")

    prohibited_boundaries = [
        "automatic scheduler-to-executor integration",
        "persistent scheduler loop",
        "autonomous operation",
        "safe-pass enablement",
        "model profile promotion",
        "real Ollama chat/generate calls",
        "cloud provider calls",
        "real NetworkGateway fetches",
        "real SandboxGateway process execution",
        "real MemoryGateway embedding writes/query",
        "Telegram operator control plane",
        "agent layer",
    ]

    for phrase in prohibited_boundaries:
        assert phrase in text


def test_phase2_closeout_doc_records_noop_result_contract():
    text = DOC.read_text(encoding="utf-8")

    required = [
        '"executor": "noop_task_executor"',
        '"executed": true',
        '"side_effects": "none"',
        '"tools_used": []',
        '"model_calls": []',
        '"network_calls": []',
        '"sandbox_calls": []',
    ]

    for phrase in required:
        assert phrase in text

