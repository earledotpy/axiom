from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
IPC = ROOT / "ipc"

AUTO_INVOCATION_FILES = [
    "agent_bridge.ps1",
    "_inbox_codex.ps1",
    "_inbox_antigravity.ps1",
    "_inbox_claude.ps1",
    "loop_watcher.ps1",
    "watcher_service.ps1",
]


def read(name: str) -> str:
    return (IPC / name).read_text(encoding="utf-8")


def test_ipc_handlers_do_not_auto_invoke_codex() -> None:
    for name in AUTO_INVOCATION_FILES:
        text = read(name).lower()
        assert "codex exec" not in text
        assert "& codex" not in text


def test_ipc_handlers_do_not_auto_invoke_antigravity() -> None:
    for name in AUTO_INVOCATION_FILES:
        text = read(name).lower()
        assert "agy.exe" not in text
        assert "invoke-conptycapture" not in text
        assert "invoke-conptycapturehosted" not in text


def test_ipc_handlers_do_not_auto_invoke_claude_code() -> None:
    for name in AUTO_INVOCATION_FILES:
        text = read(name).lower()
        assert "& claude" not in text
        assert "claude code" not in text


def test_legacy_bridges_are_explicitly_neutralized() -> None:
    for name in ["agent_bridge.ps1", "_inbox_codex.ps1", "_inbox_antigravity.ps1"]:
        text = read(name).lower()
        assert "ipc-neutralized" in text
        assert "return" in text
