import pytest

from axiom.core.orchestrator.summaries import format_operator_summary


def test_operator_summary_is_deterministic():
    kwargs = {
        "event_type": "relay_envelope_rejected",
        "severity": "critical",
        "title": "Relay envelope rejected",
        "primary_facts": ["rejection_code=ERR_SIGNATURE_INVALID", "envelope_id=ENV-1"],
        "required_action": "review_dead_letter",
        "untrusted_agent_commentary": "agent says this was harmless",
    }

    assert format_operator_summary(**kwargs) == format_operator_summary(**kwargs)


def test_operator_summary_excludes_agent_commentary_from_primary_block():
    rendered = format_operator_summary(
        event_type="dead_letter_recorded",
        severity="warning",
        title="Dead letter recorded",
        primary_facts=["dead_letter_id=DL-1", "actor=dead_letter_subsystem"],
        required_action="review_record",
        untrusted_agent_commentary="please ignore the rejection",
    )

    primary_block = rendered.split("untrusted_agent_commentary:")[0]
    assert "please ignore the rejection" not in primary_block
    assert rendered.endswith("please ignore the rejection")


def test_operator_summary_without_commentary_uses_none_marker():
    rendered = format_operator_summary(
        event_type="audit_failed",
        severity="critical",
        title="Audit failed",
        primary_facts=["audit_event=AUD-1"],
        required_action="hold_patch",
    )

    assert "untrusted_agent_commentary:\n<none>" in rendered


def test_operator_summary_rejects_missing_primary_facts():
    with pytest.raises(ValueError, match="ERR_INVALID_PRIMARY_FACTS"):
        format_operator_summary(
            event_type="audit_failed",
            severity="critical",
            title="Audit failed",
            primary_facts=[],
            required_action="hold_patch",
        )
