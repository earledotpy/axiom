import ast
from pathlib import Path

from axiom.core.orchestrator.integration import run_offline_integration_file


FIXTURE_PATH = Path("tests/level2a/orchestrator/fixtures/integration_scenarios.json")
HARNESS_PATH = Path("axiom/core/orchestrator/integration/offline_harness.py")


def _parse_harness() -> ast.Module:
    return ast.parse(HARNESS_PATH.read_text(encoding="utf-8"))


def test_harness_imports_no_runtime_authority_surfaces():
    tree = _parse_harness()
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module)

    banned_prefixes = {
        "subprocess",
        "socket",
        "requests",
        "urllib",
        "http",
        "openai",
        "anthropic",
        "google",
        "axiom.gateways",
        "axiom.agents",
    }
    assert not any(
        module == banned or module.startswith(banned + ".")
        for module in imported_modules
        for banned in banned_prefixes
    )


def test_harness_contains_no_filesystem_mutation_calls_or_process_calls():
    tree = _parse_harness()
    banned_calls = {
        "write_text",
        "write_bytes",
        "mkdir",
        "unlink",
        "rename",
        "replace",
        "rmdir",
        "open",
        "run",
        "Popen",
        "system",
    }
    called_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                called_names.add(node.func.attr)
            elif isinstance(node.func, ast.Name):
                called_names.add(node.func.id)

    assert called_names.isdisjoint(banned_calls)


def test_offline_report_never_activates_runtime_authority():
    report = run_offline_integration_file(FIXTURE_PATH)

    assert report["runtime_authority_activated"] is False
    assert report["verified_commit_emitted"] is False
    assert report["authority_status"] == "offline_fixture_evidence_only"
