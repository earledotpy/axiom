from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = ROOT / "docs" / "phase2.md"


def test_scheduler_executor_boundary_doc_exists():
    assert DOC_PATH.exists()


def test_scheduler_executor_boundary_preserves_manual_only_status():
    text = DOC_PATH.read_text(encoding="utf-8")

    assert "manual, test-only no-op execution cycle" in text
    assert "must not be connected automatically yet" in text
    assert "execution_readiness.ready: False" in text
    assert "no_pending_manifest_bound_task" in text


def test_scheduler_executor_boundary_names_future_preconditions():
    text = DOC_PATH.read_text(encoding="utf-8")

    assert "execution_readiness.ready: True" in text
    assert "running_task_count: 0" in text
    assert "pending_manifest_bound_task_count >= 1" in text
    assert "tasks.manifest_id must be non-null before transition to running" in text
    assert "one-running-task invariant must remain enforced" in text
    assert "heartbeat ordering must be preserved around blocking operations" in text


def test_scheduler_executor_boundary_blocks_dangerous_adjacent_steps():
    text = DOC_PATH.read_text(encoding="utf-8")

    prohibited = [
        "autonomous operation",
        "safe-pass enablement",
        "model profile promotion",
        "real model calls",
        "real network fetches",
        "sandbox process execution",
        "Telegram/operator control plane",
        "agent layer",
        "automatic scheduler-to-executor integration",
    ]

    for item in prohibited:
        assert item in text

