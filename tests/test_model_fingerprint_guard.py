from axiom.security.model_fingerprint_guard import ModelFingerprintGuard


def test_infer_thinking_mode_returns_disabled_for_think_false():
    data = {"parameters": "think false"}
    assert ModelFingerprintGuard._infer_thinking_mode(data) == "disabled"


def test_infer_thinking_mode_returns_disabled_for_uppercase_think_false():
    data = {"parameters": "THINK FALSE"}
    assert ModelFingerprintGuard._infer_thinking_mode(data) == "disabled"


def test_infer_thinking_mode_returns_disabled_for_whitespace_think_false():
    data = {"parameters": "  think  false  "}
    assert ModelFingerprintGuard._infer_thinking_mode(data) == "disabled"


def test_infer_thinking_mode_returns_unknown_without_think_false():
    data = {"parameters": "temperature 0.2"}
    assert ModelFingerprintGuard._infer_thinking_mode(data) == "unknown"


def test_infer_thinking_mode_does_not_inspect_template():
    data = {
        "parameters": "",
        "template": "think false",
    }
    assert ModelFingerprintGuard._infer_thinking_mode(data) == "unknown"


def test_infer_thinking_mode_does_not_inspect_system():
    data = {
        "parameters": "",
        "system": "think false",
    }
    assert ModelFingerprintGuard._infer_thinking_mode(data) == "unknown"
