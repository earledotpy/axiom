from axiom.core.orchestrator.contracts import validate_id


def test_mandate_artifact_id_accepts_full_governance_id():
    assert validate_id("mandate_artifact", "MND-ACCEPTED-2026-0003-PHASE1-ORCHESTRATOR-IMPLEMENTATION")


def test_mandate_short_key_accepts_compact_key_only():
    assert validate_id("mandate_short", "MND-CANDIDATE-2026-0003")
    assert not validate_id("mandate_short", "MND-CANDIDATE-2026-0003-PHASE1")


def test_level2a_entity_ids_are_strict():
    assert validate_id("docket", "DK-2026-0003")
    assert validate_id("relay_envelope", "ENV-12345678-1234-4234-9234-123456789abc")
    assert validate_id("audit_event", "AUD-12345678-1234-4234-9234-123456789abc")
    assert validate_id("schema", "SCH-12345678-1234-4234-9234-123456789abc")
    assert validate_id("evidence", "EVI-12345678-1234-4234-9234-123456789abc")
    assert validate_id("dead_letter", "DL-12345678-1234-4234-9234-123456789abc")
    assert validate_id("nonce", "nonce_v1_" + "a" * 64)


def test_id_formats_reject_uppercase_uuid_and_bad_nonce():
    assert not validate_id("relay_envelope", "ENV-12345678-1234-4234-9234-123456789ABC")
    assert not validate_id("nonce", "nonce_v1_" + "g" * 64)
