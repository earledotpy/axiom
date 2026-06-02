from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
IPC_DIR = ROOT / "ipc"
EVIDENCE = ROOT / "governance" / "05_handoffs" / "Phase0_IPC_Freeze_Evidence.md"

EXPECTED_CLASSIFICATIONS = {
    "ipc/_agy_hosted_test.ps1": "probe_or_scratch",
    "ipc/_agy_hosted_test.txt": "documentation_or_evidence",
    "ipc/_agy_probe_stdout.txt": "documentation_or_evidence",
    "ipc/_agy_probe.ps1": "probe_or_scratch",
    "ipc/_agy_probe.txt": "documentation_or_evidence",
    "ipc/_conpty_probe_diag.ps1": "probe_or_scratch",
    "ipc/_conpty_probe.ps1": "probe_or_scratch",
    "ipc/_conpty_probe.txt": "documentation_or_evidence",
    "ipc/_conpty_probe2.ps1": "probe_or_scratch",
    "ipc/_inbox_antigravity.ps1": "executor",
    "ipc/_inbox_claude.ps1": "executor",
    "ipc/_inbox_codex.ps1": "executor",
    "ipc/_posture_runspace.ps1": "posture_or_status_daemon",
    "ipc/_probe_diag.txt": "documentation_or_evidence",
    "ipc/_probe_raw.ps1": "probe_or_scratch",
    "ipc/_probe_raw.txt": "documentation_or_evidence",
    "ipc/agent_bridge.ps1": "executor",
    "ipc/conpty_capture.ps1": "conpty_or_terminal_bridge",
    "ipc/ipc_db.py": "database_index",
    "ipc/ipc_messages.db": "runtime_artifact",
    "ipc/ipc_service.ps1": "watcher",
    "ipc/loop_watcher.ps1": "watcher",
    "ipc/notify.ps1": "notification_helper",
    "ipc/posture_cache.json": "runtime_artifact",
    "ipc/posture_daemon.log": "runtime_artifact",
    "ipc/posture_daemon.ps1": "posture_or_status_daemon",
    "ipc/README.md": "documentation_or_evidence",
    "ipc/send.ps1": "transport",
    "ipc/startup_agy.ps1": "startup_launcher",
    "ipc/startup_claude.ps1": "startup_launcher",
    "ipc/startup_codex.ps1": "startup_launcher",
    "ipc/tmux_bridge.ps1": "conpty_or_terminal_bridge",
    "ipc/to_antigravity.md": "historical_inbox",
    "ipc/to_claude.md": "historical_inbox",
    "ipc/to_codex.md": "historical_inbox",
    "ipc/watcher_service.ps1": "watcher",
}

GUARDED_POWERSHELL = {
    path for path in EXPECTED_CLASSIFICATIONS if path.endswith(".ps1")
}

UNSAFE_SINK_PATTERNS = [
    r"\bInvoke-Expression\b",
    r"\biex\b",
    r"\bInvoke-Command\b",
    r"\[scriptblock\]::Create",
    r"\bStart-Process\b",
    r"\bcodex\s+exec\b",
    r"\bagy\s+--print\b",
    r"\bInvoke-ConPtyCapture(?:Hosted)?\b",
    r"\bsend-keys\b",
    r"\bFileSystemWatcher\b",
    r"\bCreateRunspacePool\b",
    r"\bBeginInvoke\b",
    r"\bpending\s+--agent\b",
    r"\bAdd-Content\b",
    r"\bOut-File\b",
    r"\bMove-Item\b",
    r"\bNew-Object\s+-ComObject\b",
    r"\bpython\s+.*ipc_db\.py\b",
    r"&\s+\$sendScript\s+-To\s+\$msg\.from_agent",
]


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def uncommented_lines(text: str) -> list[tuple[int, str]]:
    lines = []
    for number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        lines.append((number, line))
    return lines


def first_line_matching(text: str, patterns: list[str]) -> int | None:
    for number, line in uncommented_lines(text):
        if any(re.search(pattern, line, re.IGNORECASE) for pattern in patterns):
            return number
    return None


def guard_line(text: str) -> int | None:
    return first_line_matching(text, [r"IPC_PHASE0_FREEZE_ACTIVE\s*=\s*\$true"])


def test_ipc_inventory_reconciles_with_expected_classification_map() -> None:
    walked = {rel(path) for path in IPC_DIR.rglob("*") if path.is_file()}
    assert walked == set(EXPECTED_CLASSIFICATIONS)
    assert len(walked) == len(EXPECTED_CLASSIFICATIONS) == 36


def test_phase0_evidence_contains_pre_modification_hash_baseline() -> None:
    text = EVIDENCE.read_text(encoding="utf-8")
    rows = re.findall(r"^\| (ipc/[^|]+) \| (\d+) \| ([0-9a-f]{64}) \|", text, re.MULTILINE)
    paths = {path for path, _size, _hash in rows}
    assert paths == set(EXPECTED_CLASSIFICATIONS)
    assert len(rows) == len(EXPECTED_CLASSIFICATIONS)


@pytest.mark.parametrize("path", sorted(GUARDED_POWERSHELL))
def test_powershell_guard_dominates_unsafe_sinks(path: str) -> None:
    text = (ROOT / path).read_text(encoding="utf-8-sig")
    guard = guard_line(text)
    assert guard is not None, path
    first_sink = first_line_matching(text, UNSAFE_SINK_PATTERNS)
    if first_sink is not None:
        assert guard < first_sink, f"{path}: guard line {guard} must precede sink line {first_sink}"


def test_ipc_service_composed_service_guard_precedes_runspace_edges() -> None:
    text = (IPC_DIR / "ipc_service.ps1").read_text(encoding="utf-8-sig")
    guard = guard_line(text)
    assert guard is not None
    assert guard < first_line_matching(text, [r"CreateRunspacePool", r"AddScript", r"BeginInvoke"])


def test_startup_scripts_fail_closed_before_launch_or_terminal_edges() -> None:
    for name in ("startup_agy.ps1", "startup_claude.ps1", "startup_codex.ps1"):
        text = (IPC_DIR / name).read_text(encoding="utf-8-sig")
        guard = guard_line(text)
        first_sink = first_line_matching(
            text,
            [r"watcher_service\.ps1", r"Start-Process", r"Register-TmuxSession", r"^\s*agy\s*$", r"^\s*codex\s*$", r"^\s*claude\s*$"],
        )
        assert guard is not None
        assert first_sink is not None
        assert guard < first_sink


def test_ipc_db_command_type_is_neutralized_at_ingress_and_pending_query() -> None:
    text = (IPC_DIR / "ipc_db.py").read_text(encoding="utf-8")
    assert "IPC_PHASE0_FREEZE_ACTIVE = True" in text
    assert "IPC_PHASE0_NEUTRALIZED_COMMAND_TYPE" in text
    assert "def neutralize_message_type" in text
    assert "effective_type.lower() == \"command\"" in text
    assert "lower(type) NOT IN ('command', ?)" in text


def test_markdown_inboxes_are_evidence_only_not_active_sources() -> None:
    active_sources = [
        path for path in IPC_DIR.glob("*.ps1")
        if path.name not in {"startup_agy.ps1", "startup_claude.ps1", "startup_codex.ps1"}
    ]
    for path in active_sources:
        text = path.read_text(encoding="utf-8-sig")
        if re.search(r"to_(claude|codex|antigravity)\.md", text, re.IGNORECASE):
            guard = guard_line(text)
            first_inbox_reference = first_line_matching(text, [r"to_(claude|codex|antigravity)\.md"])
            assert guard is not None
            assert first_inbox_reference is not None
            assert guard < first_inbox_reference


def test_static_tripwire_strings_are_guarded_or_evidence_only() -> None:
    evidence_only_suffixes = {".md", ".txt", ".json", ".log", ".db", ".py"}
    for path in IPC_DIR.rglob("*"):
        if not path.is_file() or path.suffix.lower() in evidence_only_suffixes:
            continue
        text = path.read_text(encoding="utf-8-sig")
        first_sink = first_line_matching(text, UNSAFE_SINK_PATTERNS)
        if first_sink is None:
            continue
        guard = guard_line(text)
        assert guard is not None, rel(path)
        assert guard < first_sink, rel(path)
