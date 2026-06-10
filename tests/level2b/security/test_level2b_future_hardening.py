from __future__ import annotations

from pathlib import Path
import subprocess

import pytest

from axiom.core.orchestrator.state_machines import DocketState, can_transition, next_state, synchronize_mandate_from_docket
from axiom.security.level2b.process_adapter import (
    AclAssertion,
    PrincipalRole,
    ProcessAdapterError,
    ProcessExecutionRequest,
    account_for_role,
    build_execution_plan,
)
from axiom.security.level2b.tpm_sealing import MockTpm
from axiom.security.level2b.translation import (
    DescriptorKind,
    DescriptorStream,
    TranslationError,
    WindowsDescriptor,
    translate_stdio,
)


def test_state_machine_escalates_audit_accepted_pending_2b():
    assert can_transition(DocketState.AUDIT_ACCEPTED_PENDING_2B, "escalate_2b", DocketState)
    assert next_state(DocketState.AUDIT_ACCEPTED_PENDING_2B, "escalate_2b", DocketState) is DocketState.VERIFICATION_PENDING
    assert synchronize_mandate_from_docket(DocketState.AUDIT_ACCEPTED_PENDING_2B) is None


def test_process_adapter_maps_roles_to_distinct_os_accounts(tmp_path):
    assert account_for_role(PrincipalRole.BUILDER) == "axiom_builder"
    assert account_for_role(PrincipalRole.REVIEWER) == "axiom_reviewer"
    assert account_for_role(PrincipalRole.VERIFIER) == "axiom_verifier"

    request = ProcessExecutionRequest(
        role=PrincipalRole.VERIFIER,
        command=("codex", "--version"),
        workspace=tmp_path,
        impersonation_token="mock-token",
        acl_assertions=(AclAssertion(tmp_path, "axiom_verifier", can_read=True, can_write=False),),
    )
    plan = build_execution_plan(request)

    assert plan.account == "axiom_verifier"
    assert plan.command == ("codex", "--version")
    assert plan.dry_run is True


def test_process_adapter_fails_closed_without_token_or_acl(tmp_path):
    with pytest.raises(ProcessAdapterError, match="ERR_IMPERSONATION_TOKEN_REQUIRED"):
        build_execution_plan(
            ProcessExecutionRequest(
                role=PrincipalRole.BUILDER,
                command=("codex",),
                workspace=tmp_path,
                acl_assertions=(AclAssertion(tmp_path, "axiom_builder", can_read=True, can_write=True),),
            )
        )
    with pytest.raises(ProcessAdapterError, match="ERR_ACL_ACCOUNT_MISMATCH"):
        build_execution_plan(
            ProcessExecutionRequest(
                role=PrincipalRole.REVIEWER,
                command=("claude",),
                workspace=tmp_path,
                impersonation_token="mock-token",
                acl_assertions=(AclAssertion(tmp_path, "axiom_builder", can_read=True, can_write=True),),
            )
        )


def test_translation_layer_preserves_stdio_streams():
    translated = translate_stdio(
        [
            WindowsDescriptor(DescriptorStream.STDIN, DescriptorKind.CONSOLE_HANDLE, "CONIN$"),
            WindowsDescriptor(DescriptorStream.STDOUT, DescriptorKind.CONSOLE_HANDLE, "CONOUT$"),
            WindowsDescriptor(DescriptorStream.STDERR, DescriptorKind.FILE_DESCRIPTOR, "2"),
        ],
        namespace="axiom-test",
    )

    assert set(translated) == {DescriptorStream.STDIN, DescriptorStream.STDOUT, DescriptorStream.STDERR}
    assert translated[DescriptorStream.STDIN].socket_path.endswith(".sock")
    assert translated[DescriptorStream.STDOUT].pipe_path.endswith(".pipe")
    assert "/run/axiom-test/" in translated[DescriptorStream.STDERR].socket_path


def test_translation_layer_fails_if_stdio_stream_missing():
    with pytest.raises(TranslationError, match="ERR_STDIO_STREAM_MISSING"):
        translate_stdio([WindowsDescriptor(DescriptorStream.STDIN, DescriptorKind.CONSOLE_HANDLE, "CONIN$")])


def test_firewall_script_outputs_loopback_allow_and_default_block_rules():
    script = Path("tools/generate_firewall_rules.ps1")
    assert script.exists()
    content = script.read_text(encoding="utf-8")

    assert "127.0.0.1" in content
    assert "Allow" in content
    assert "Block" in content
    assert "dryRun" in content
    assert "axiom_builder" in content
    assert "New-NetFirewallRule" not in content


def test_firewall_script_dry_run_executes_if_powershell_available():
    shell = "powershell.exe"
    result = subprocess.run(
        [shell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "tools/generate_firewall_rules.ps1"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0 and "not recognized" in (result.stderr + result.stdout):
        pytest.skip("powershell.exe unavailable")
    assert result.returncode == 0
    assert "127.0.0.1" in result.stdout
    assert "Block" in result.stdout


def test_mock_tpm_signatures_verify_successfully():
    tpm = MockTpm(seed=b"level2b-test")
    key = tpm.create_key(label="axiom_verifier")
    payload = b"verify this manifest"

    signature = tpm.sign(key, payload)

    assert key.non_extractable is True
    assert key.public_key_sha256.startswith("sha256:")
    assert signature.mock_tpm is True
    assert signature.payload_sha256.startswith("sha256:")
    assert tpm.verify(key, payload, signature)
    assert not tpm.verify(key, b"tampered", signature)
