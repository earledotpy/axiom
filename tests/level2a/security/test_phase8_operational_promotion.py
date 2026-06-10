import os
import json
import base64
import argparse
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from axiom.app.bootstrap_validation import BootstrapValidator, BootstrapValidationError
from axiom.core.autonomous_gate import (
    evaluate_autonomous_readiness,
    AutonomousReadinessDecision,
    AutonomousReadinessError,
    require_autonomous_ready,
)
from axiom.agents.manual_cli import run_manual_agent_cli
from axiom.agents.base import AgentExecutionResult

# Import seal command functions
from tools.seal import (
    cmd_generate_key,
    cmd_export_public_key,
    cmd_sign,
    cmd_verify,
)


def test_seal_generate_key_and_export(tmp_path):
    # Test generation of Ed25519 keypair
    gen_args = argparse.Namespace(
        out_dir=str(tmp_path),
        passphrase="test_secure_passphrase_123",
    )

    cmd_generate_key(gen_args)

    private_key_path = tmp_path / "private_key.pem"
    public_key_path = tmp_path / "public_key.pem"

    assert private_key_path.exists()
    assert public_key_path.exists()

    # Test export of public key from the generated private key
    export_out_path = tmp_path / "exported_public_key.pem"
    export_args = argparse.Namespace(
        private_key=str(private_key_path),
        passphrase="test_secure_passphrase_123",
        out=str(export_out_path),
    )

    cmd_export_public_key(export_args)
    assert export_out_path.exists()

    # Check that public key file matches the exported one
    with open(public_key_path, "rb") as f1, open(export_out_path, "rb") as f2:
        assert f1.read() == f2.read()


def test_seal_sign_and_verify(tmp_path):
    # Generate keys first
    private_key_path = tmp_path / "private_key.pem"
    gen_args = argparse.Namespace(
        out_dir=str(tmp_path),
        passphrase="passphrase",
    )
    cmd_generate_key(gen_args)

    # Create dummy payload JSON
    payload = {
        "nonce": "test_nonce_val",
        "expiry": "2026-12-31T23:59:59Z",
        "action": "execute_test",
    }
    payload_path = tmp_path / "payload.json"
    with open(payload_path, "w", encoding="utf-8") as f:
        json.dump(payload, f)

    # Sign the payload
    signed_path = tmp_path / "signed_payload.json"
    sign_args = argparse.Namespace(
        payload_file=str(payload_path),
        private_key=str(private_key_path),
        passphrase="passphrase",
        out=str(signed_path),
    )
    cmd_sign(sign_args)

    assert signed_path.exists()

    # Verify signature
    verify_args = argparse.Namespace(
        payload_file=str(signed_path),
        public_key=None,  # read from payload
    )
    # This should run without raising SystemExit or errors
    cmd_verify(verify_args)


def test_setup_verifier_script_contents():
    # Verify that the powershell setup script exists and has correct rules
    script_path = Path("tools/setup_verifier.ps1")
    assert script_path.exists()

    content = script_path.read_text(encoding="utf-8")

    # Step 3 requirements:
    assert "axiom_verifier" in content
    assert "FullControl" in content
    assert "NT AUTHORITY\\SYSTEM" in content
    assert "BUILTIN\\Administrators" in content
    assert "C:\\axiom_state" in content
    assert "SetAccessRuleProtection" in content
    assert "ReadAndExecute" in content


def test_bootstrap_validator_gate_blocks_on_readiness_failure():
    # Mock evaluate_autonomous_readiness to return allowed=False
    mock_decision = AutonomousReadinessDecision(
        allowed=False,
        blocking_reasons=["test_readiness_block"],
        status={"status_check": "blocked"},
    )

    with patch("axiom.app.bootstrap_validation.evaluate_autonomous_readiness", return_value=mock_decision):
        validator = BootstrapValidator()
        
        # Passive check should not raise, but result.passed is still true
        # if the foundation checks pass (which they do in a clean repo),
        # but the operational mode must transition to fail-closed
        result = validator.run(raise_on_failure=False)
        assert result.operational_mode == "fail_closed_non_autonomous"
        
        # When raise_on_failure=True, it must raise BootstrapValidationError
        with pytest.raises(BootstrapValidationError) as exc_info:
            validator.run(raise_on_failure=True)
        assert "autonomous_readiness_not_allowed" in str(exc_info.value)


def test_active_runtime_gate_blocks_agent_cli():
    mock_decision = AutonomousReadinessDecision(
        allowed=False,
        blocking_reasons=["maintenance_lock"],
    )

    mock_execute = MagicMock(return_value=AgentExecutionResult(
        task_id=1,
        session_id=123,
        agent_name="test_agent",
        manifest_id="test.manifest",
        started=True,
        completed=True,
        start_heartbeat_id=10,
        completion_heartbeat_id=11,
        artifact_id=45,
        result_text="done",
        result_json={"status": "ok"},
    ))

    with patch("axiom.agents.manual_cli.evaluate_autonomous_readiness", return_value=mock_decision):
        # Default run with override=False should return 1 and not execute
        code = run_manual_agent_cli(
            agent_name="test_agent",
            task_id=1,
            execute=mock_execute,
            json_output=False,
            manual_test_override=False,
        )
        assert code == 1
        mock_execute.assert_not_called()

        # If override is True, it is allowed to execute
        code_override = run_manual_agent_cli(
            agent_name="test_agent",
            task_id=1,
            execute=mock_execute,
            json_output=False,
            manual_test_override=True,
        )
        assert code_override == 0
        mock_execute.assert_called_once_with(1)
