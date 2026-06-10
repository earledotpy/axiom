import pytest

from axiom.security.level2a.canonical import canonicalize


def test_canonicalize_recursively_sorts_dictionary_keys():
    payload = {"z": 1, "a": {"c": 3, "b": 2}}

    assert canonicalize(payload) == b'{"a":{"b":2,"c":3},"z":1}'


def test_canonicalize_handles_supported_json_types_deterministically():
    payload = {
        "string": "line\nsnowman \u2603",
        "list": [True, False, None, {"b": "two", "a": "one"}],
    }

    assert (
        canonicalize(payload)
        == '{"list":[true,false,null,{"a":"one","b":"two"}],"string":"line\\nsnowman \u2603"}'.encode(
            "utf-8"
        )
    )


def test_canonicalize_rejects_float_values():
    with pytest.raises(ValueError, match="ERR_FLOAT_NOT_ALLOWED"):
        canonicalize({"amount": 1.5})


def test_canonicalize_serializes_integers_as_decimal_strings():
    assert canonicalize({"answer": 42, "negative": -7}) == b'{"answer":42,"negative":-7}'
