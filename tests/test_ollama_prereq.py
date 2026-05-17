from axiom.gateways.ollama_prereq import OllamaPrereqInspector


def test_ollama_prereq_reports_unreachable_when_tags_unavailable(monkeypatch):
    inspector = OllamaPrereqInspector()

    monkeypatch.setattr(inspector, "_post_json", lambda path, payload: None)
    monkeypatch.setattr(inspector, "_get_json", lambda path: None)

    result = inspector.inspect()

    assert result.reachable is False
    assert result.reason == "ollama_tags_unavailable"
    assert result.runtime_thinking_enforcement == "unverified"
    assert result.fingerprint_registration_ready is False


def test_ollama_prereq_reports_model_not_present(monkeypatch):
    inspector = OllamaPrereqInspector(model="qwen3:4b")

    def fake_post(path, payload):
        if path == "/api/tags":
            return {"models": [{"name": "llama3:8b"}]}
        return None

    monkeypatch.setattr(inspector, "_post_json", fake_post)
    monkeypatch.setattr(inspector, "_get_json", lambda path: None)

    result = inspector.inspect()

    assert result.reachable is True
    assert result.tags_available is True
    assert result.model_present is False
    assert result.reason == "model_not_present"
    assert result.fingerprint_registration_ready is False


def test_ollama_prereq_reports_show_unavailable(monkeypatch):
    inspector = OllamaPrereqInspector(model="qwen3:4b")

    def fake_post(path, payload):
        if path == "/api/tags":
            return {"models": [{"name": "qwen3:4b"}]}
        if path == "/api/show":
            return None
        return None

    monkeypatch.setattr(inspector, "_post_json", fake_post)
    monkeypatch.setattr(inspector, "_get_json", lambda path: None)

    result = inspector.inspect()

    assert result.model_present is True
    assert result.show_available is False
    assert result.reason == "ollama_show_unavailable"
    assert result.fingerprint_registration_ready is False


def test_ollama_prereq_reports_profile_verified_when_parameters_include_think_false(monkeypatch):
    inspector = OllamaPrereqInspector(model="qwen3:4b")

    def fake_post(path, payload):
        if path == "/api/tags":
            return {"models": [{"name": "qwen3:4b"}]}
        if path == "/api/show":
            return {
                "details": {
                    "quantization_level": "Q4_K_M",
                },
                "parameters": "temperature 0.2\nthink false\n",
            }
        return None

    monkeypatch.setattr(inspector, "_post_json", fake_post)
    monkeypatch.setattr(inspector, "_get_json", lambda path: None)

    result = inspector.inspect()

    assert result.reachable is True
    assert result.model_present is True
    assert result.show_available is True
    assert result.details_present is True
    assert result.parameters_present is True
    assert result.quantization_level == "Q4_K_M"
    assert result.profile_thinking_mode == "disabled"
    assert result.runtime_thinking_enforcement == "profile_verified"
    assert result.fingerprint_registration_ready is True
    assert result.reason == "ollama_prerequisites_inspected"


def test_ollama_prereq_reports_gateway_required_when_profile_thinking_unknown(monkeypatch):
    inspector = OllamaPrereqInspector(model="qwen3:4b")

    def fake_post(path, payload):
        if path == "/api/tags":
            return {"models": [{"name": "qwen3:4b"}]}
        if path == "/api/show":
            return {
                "details": {
                    "quantization_level": "Q4_K_M",
                },
                "parameters": "temperature 1\ntop_k 20\n",
            }
        return None

    monkeypatch.setattr(inspector, "_post_json", fake_post)
    monkeypatch.setattr(inspector, "_get_json", lambda path: None)

    result = inspector.inspect()

    assert result.profile_thinking_mode == "unknown"
    assert result.runtime_thinking_enforcement == "gateway_required"
    assert result.fingerprint_registration_ready is True


def test_ollama_prereq_infers_unknown_thinking_mode_without_parameters():
    assert OllamaPrereqInspector._infer_thinking_mode_from_parameters(None) == "unknown"


def test_ollama_prereq_infers_unknown_thinking_mode_without_think_false():
    assert (
        OllamaPrereqInspector._infer_thinking_mode_from_parameters("temperature 0.2")
        == "unknown"
    )


def test_ollama_prereq_extracts_name_and_model_fields():
    tags = {
        "models": [
            {"name": "qwen3:4b"},
            {"model": "llama3:8b"},
        ]
    }

    names = OllamaPrereqInspector._extract_model_names(tags)

    assert names == {"qwen3:4b", "llama3:8b"}
