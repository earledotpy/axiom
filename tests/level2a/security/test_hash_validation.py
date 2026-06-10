import pytest

from axiom.security.level2a.validators import (
    reject_broad_pytest_collection,
    require_hash_match,
    validate_sha256_hash,
)


def test_prefixed_sha256_hash_must_be_lowercase_hex():
    assert validate_sha256_hash("sha256:" + "a" * 64)
    assert not validate_sha256_hash("sha256:" + "A" * 64)
    assert not validate_sha256_hash("a" * 64)


def test_t08_artifact_hash_mismatch_rejected():
    with pytest.raises(ValueError, match="ERR_HASH_MISMATCH"):
        require_hash_match("sha256:" + "a" * 64, "sha256:" + "b" * 64)


def test_matching_artifact_hash_is_allowed():
    assert require_hash_match("sha256:" + "a" * 64, "sha256:" + "a" * 64)


def test_t11_broad_test_collection_rejected():
    with pytest.raises(ValueError, match="ERR_BROAD_COLLECTION_VIOLATION"):
        reject_broad_pytest_collection("tests/level2a/")
    assert reject_broad_pytest_collection("tests/level2a/security/test_hash_validation.py::test_matching_artifact_hash_is_allowed")
