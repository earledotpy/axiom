from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOUNDARY = ROOT / "docs" / "phase5.md"
CLOSEOUT = ROOT / "docs" / "phase5.md"
PHASE6_ROADMAP = ROOT / "docs" / "phase6.md"


def test_phase5_agent_boundary_doc_exists_and_names_manual_entrypoints():
    text = BOUNDARY.read_text(encoding="utf-8")

    required = [
        "Phase 5 agent foundations are manual-only and manifest-bound",
        "tools/execute_goal_planning_task.py",
        "tools/execute_task_planning_task.py",
        "tools/execute_tool_execution_task.py",
        "tools/execute_result_verification_task.py",
        "tools/run_manual_agent_foundation_smoke.py",
    ]

    for phrase in required:
        assert phrase in text


def test_phase5_agent_boundary_preserves_prohibitions():
    text = BOUNDARY.read_text(encoding="utf-8")

    prohibited = [
        "autonomous operation",
        "safe-pass enablement",
        "scheduler-to-agent automation",
        "Telegram/operator control plane",
        "task creation by agents",
        "real model calls",
        "cloud cascade calls",
        "network fetches",
        "sandbox execution",
        "memory reads or writes",
        "filesystem reads or writes",
        "new artifact schema creation",
    ]

    for phrase in prohibited:
        assert phrase in text


def test_phase5_closeout_doc_records_completed_surface_and_safe_posture():
    text = CLOSEOUT.read_text(encoding="utf-8")

    required = [
        "Phase 5 agent foundation is implemented",
        "fail_closed_non_autonomous",
        "autonomous_allowed = False",
        "safe_pass_enabled = False",
        "GoalPlanner manifest-bound executor",
        "TaskPlanner manifest-bound executor",
        "ToolExecutor manifest-bound planning-only executor",
        "ResultVerifier manifest-bound summary-only executor",
        "manual agent foundation smoke path",
        "read-only agent boundary audit",
    ]

    for phrase in required:
        assert phrase in text


def test_phase5_closeout_doc_records_verification_commands():
    text = CLOSEOUT.read_text(encoding="utf-8")

    required = [
        "python tools/register_manifests.py",
        "tests\\test_phase5_agent_cli.py",
        "tests\\test_phase5_docs.py",
        "tests\\test_agent_boundary_audit.py",
        "python tools\\verify_foundation.py",
        "python tools\\audit_task_lifecycle.py",
        "python tools\\audit_task_execution.py",
        "python tools\\audit_policy_security.py",
        "python tools\\audit_agent_boundary.py",
        "pytest tests -v",
    ]

    for phrase in required:
        assert phrase in text


def test_phase6_roadmap_tracks_current_bounded_phase6_runtime():
    text = PHASE6_ROADMAP.read_text(encoding="utf-8")

    required = [
        "Slices 6A through 6I are implemented",
        "Build the operator control plane foundation",
        "6A. Entry Gate And Scope Lock",
        "6B. Operator Command Manifest Set",
        "6C. Local Operator Command Parser",
        "6D. Operator Command Ledger",
        "6E. Terminal Operator Control Visibility",
        "6F. External Adapter Design Packet",
        "6G. Telegram Gateway Runtime Foundation",
        "python tools\\audit_agent_boundary.py",
    ]

    for phrase in required:
        assert phrase in text


