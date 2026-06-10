from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
IPC = ROOT / "ipc"


def powershell_sources() -> list[Path]:
    return sorted(IPC.glob("*.ps1"))


def test_invoke_expression_is_absent_from_ipc_powershell_sources() -> None:
    offenders = [
        path.name
        for path in powershell_sources()
        if "Invoke-Expression" in path.read_text(encoding="utf-8")
    ]
    assert offenders == []


def test_message_body_is_not_passed_to_shell_or_agent_execution() -> None:
    risky_tokens = [
        "$msg.body 2>&1",
        "-Prompt $msg.body",
        "--print', $Prompt",
        "workspace-write -C C:\\axiom $Prompt",
    ]
    offenders: list[str] = []
    for path in powershell_sources():
        text = path.read_text(encoding="utf-8")
        if any(token in text for token in risky_tokens):
            offenders.append(path.name)
    assert offenders == []


def test_notification_helper_does_not_execute_message_body_or_agent_prompt() -> None:
    text = (IPC / "watcher_service.ps1").read_text(encoding="utf-8").lower()
    assert "start-process" not in text
    assert "waitforchanged" not in text
    assert "ipc-neutralized" in text
