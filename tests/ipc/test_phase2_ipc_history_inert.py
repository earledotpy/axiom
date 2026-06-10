import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
IPC = ROOT / "ipc"
IPC_DB = IPC / "ipc_db.py"

PROTECTED_ARTIFACTS = [
    IPC / "ipc_messages.db",
    IPC / "posture_cache.json",
    IPC / "posture_daemon.log",
    IPC / "to_codex.md",
    IPC / "to_claude.md",
    IPC / "to_antigravity.md",
]


def snapshot() -> dict[Path, int | None]:
    return {
        path: path.stat().st_mtime_ns if path.exists() else None
        for path in PROTECTED_ARTIFACTS
    }


def run_ipc(tmp_path: Path, *args: str) -> dict | list:
    env = os.environ.copy()
    env["AXIOM_IPC_DB_PATH"] = str(tmp_path / "ipc_history.db")
    result = subprocess.run(
        [sys.executable, str(IPC_DB), *args],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(result.stdout)


def test_rejected_command_frames_are_retained_as_inert_history(tmp_path: Path) -> None:
    db_path = tmp_path / "ipc_history.db"
    result = run_ipc(
        tmp_path,
        "write",
        "--from",
        "operator",
        "--to",
        "codex",
        "--subject",
        "history-only",
        "--time",
        "2026-06-06 18:10:00",
        "--body",
        "whoami",
        "--type",
        "command",
    )
    assert result["rejected"] is True

    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT type, processed, dead_letter FROM messages WHERE subject=?",
            ("history-only",),
        ).fetchone()

    assert row == ("phase2-rejected-command", 1, 1)


def test_phase2_tests_do_not_modify_live_ipc_evidence_artifacts(tmp_path: Path) -> None:
    before = snapshot()
    run_ipc(
        tmp_path,
        "write",
        "--from",
        "operator",
        "--to",
        "antigravity",
        "--subject",
        "protected-artifacts",
        "--time",
        "2026-06-06 18:20:00",
        "--body",
        "echo blocked",
        "--type",
        "command",
    )
    assert snapshot() == before


def test_readme_classifies_ipc_as_inert_review_surface() -> None:
    text = (IPC / "README.md").read_text(encoding="utf-8").lower()
    assert "inert historical evidence" in text
    assert "manual review surface" in text
    assert "command" in text
    assert "not returned as pending" in text
