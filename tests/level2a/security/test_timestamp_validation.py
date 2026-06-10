from axiom.security.level2a.validators import is_expired, validate_utc_timestamp


def test_valid_timestamp_uses_strict_utc_z_format():
    assert validate_utc_timestamp("2026-06-04T08:15:00Z")


def test_t22_timestamp_rejects_offsets_and_fractional_seconds():
    assert not validate_utc_timestamp("2026-06-04T08:15:00+02:00")
    assert not validate_utc_timestamp("2026-06-04T08:15:00.123Z")


def test_expiry_boundary_uses_current_time_greater_or_equal():
    assert is_expired("2026-06-04T08:15:00Z", "2026-06-04T08:15:00Z")
    assert not is_expired("2026-06-04T08:14:59Z", "2026-06-04T08:15:00Z")
