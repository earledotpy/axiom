import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
IPC_DB = ROOT / "ipc" / "ipc_db.py"


def run_ipc(tmp_path: Path, *args: str) -> dict | list:
    env = os.environ.copy()
    env["AXIOM_IPC_DB_PATH"] = str(tmp_path / "ipc_test.db")
    result = subprocess.run(
        [sys.executable, str(IPC_DB), *args],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(result.stdout)


def write_message(tmp_path: Path, msg_type: str | None, subject: str) -> dict:
    args = [
        "write",
        "--from",
        "codex",
        "--to",
        "claude",
        "--subject",
        subject,
        "--time",
        f"2026-06-06 18:00:{len(subject):02d}",
        "--body",
        "Write-Output unsafe",
    ]
    if msg_type is not None:
        args.extend(["--type", msg_type])
    return run_ipc(tmp_path, *args)


def test_command_frame_variants_are_rejected_and_not_pending(tmp_path: Path) -> None:
    for index, msg_type in enumerate(["command", " COMMAND ", "Command"]):
        result = write_message(tmp_path, msg_type, f"command-{index}")
        assert result["rejected"] is True
        assert result["type"] == "phase2-rejected-command"

    pending = run_ipc(tmp_path, "pending", "--agent", "claude")
    assert pending == []


def test_missing_type_defaults_to_review_prompt_not_command(tmp_path: Path) -> None:
    result = write_message(tmp_path, None, "missing-type")
    assert result["rejected"] is False
    assert result["type"] == "ai-prompt"

    pending = run_ipc(tmp_path, "pending", "--agent", "claude")
    assert len(pending) == 1
    assert pending[0]["type"] == "ai-prompt"


def test_phase2_tests_use_temporary_ipc_database(tmp_path: Path) -> None:
    live_db = ROOT / "ipc" / "ipc_messages.db"
    before = live_db.stat().st_mtime_ns if live_db.exists() else None

    write_message(tmp_path, "command", "temp-db-only")

    after = live_db.stat().st_mtime_ns if live_db.exists() else None
    assert after == before
    assert (tmp_path / "ipc_test.db").exists()
