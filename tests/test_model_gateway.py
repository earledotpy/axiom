import pytest

from axiom.gateways.model_gateway import PolicyDeniedError, prepare_local_ollama_payload


def test_prepare_local_ollama_payload_injects_think_false():
    payload = {"model": "qwen3:4b", "prompt": "test"}
    prepared = prepare_local_ollama_payload(payload)

    assert prepared["think"] is False
    assert prepared["model"] == "qwen3:4b"
    assert prepared["prompt"] == "test"


def test_prepare_local_ollama_payload_rejects_think_true():
    with pytest.raises(PolicyDeniedError):
        prepare_local_ollama_payload({"model": "qwen3:4b", "think": True})


def test_prepare_local_ollama_payload_preserves_other_fields():
    payload = {
        "model": "qwen3:4b",
        "prompt": "test",
        "options": {"temperature": 0.2},
    }

    prepared = prepare_local_ollama_payload(payload)

    assert prepared["think"] is False
    assert prepared["options"] == {"temperature": 0.2}
