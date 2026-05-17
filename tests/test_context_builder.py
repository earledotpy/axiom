import pytest

from axiom.core.context_builder import ContextBuilder, ContextBundleTooLargeError


def test_context_builder_builds_bundle_under_limit():
    builder = ContextBuilder(max_bundle_kb=1)

    bundle = builder.build_bundle({"message": "hello"})

    assert bundle["payload"] == {"message": "hello"}
    assert bundle["size_bytes"] <= 1024
    assert bundle["max_bundle_bytes"] == 1024


def test_context_builder_raises_when_bundle_exceeds_limit():
    builder = ContextBuilder(max_bundle_kb=1)

    with pytest.raises(ContextBundleTooLargeError):
        builder.build_bundle({"message": "x" * 2048})


def test_context_builder_rejects_non_positive_limit():
    with pytest.raises(ValueError):
        ContextBuilder(max_bundle_kb=0)


def test_context_builder_serialization_is_stable():
    first = ContextBuilder.serialize({"b": 2, "a": 1})
    second = ContextBuilder.serialize({"a": 1, "b": 2})

    assert first == second
    assert first == '{"a":1,"b":2}'
