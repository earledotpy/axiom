from axiom.app.bootstrap_validation import BootstrapValidator


def test_bootstrap_validation_reports_autonomous_readiness_without_failing_foundation():
    validator = BootstrapValidator()
    result = validator.run()

    assert result.passed is True

    payload = result.to_dict()
    assert "autonomous_readiness" in payload
    assert "operational_mode" in payload

    readiness = payload["autonomous_readiness"]
    assert "allowed" in readiness
    assert "blocking_reasons" in readiness
    assert "status" in readiness

    if readiness["allowed"]:
        assert payload["operational_mode"] == "autonomous_available"
    else:
        assert payload["operational_mode"] == "fail_closed_non_autonomous"
