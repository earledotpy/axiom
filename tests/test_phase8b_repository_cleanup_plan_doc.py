from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "phase8b_repository_cleanup_plan.md"


def test_phase8b_doc_records_audit_only_scope_and_boundaries():
    text = DOC.read_text(encoding="utf-8")

    required = [
        "Phase 8B is audit/planning only.",
        "This audit does not rename files, delete files, move files",
        "enable autonomy",
        "add Telegram default runtime",
        "add scheduler-to-agent automation",
        "add scheduler-to-executor automation",
        "expand gateway authority",
        "Phase 8A boundaries remain intact.",
    ]

    for phrase in required:
        assert phrase in text


def test_phase8b_doc_classifies_high_risk_cleanup_candidates():
    text = DOC.read_text(encoding="utf-8")

    required = [
        "axiom\\agents\\_init_.py",
        "axiom\\agents\\__init__.py",
        "inspect_*.py",
        "Set-Location",
        "orColor...#A8FF60...,",
        "package-lock.json",
        "project_state_snapshot_2026-05-24T20-45-36Z.json",
        "Tracked `venv\\` paths",
        "Tracked `logs\\` handoff/snapshot paths",
        "Governance archive/deprecated paths",
    ]

    for phrase in required:
        assert phrase in text


def test_phase8b_doc_records_reference_maps_and_future_verification():
    text = DOC.read_text(encoding="utf-8")

    required = [
        "git ls-files --deleted",
        "git ls-files --ignored --others --exclude-standard",
        "rg \"<candidate-name-or-symbol>\"",
        "Python imports",
        "Terminal command or registry rename",
        "Generated handoff/snapshot references must be classified separately",
        "python -m pytest tests -k \"phase8 or docs or terminal\" -v",
        "python tools\\run_phase7_acceptance.py --json",
        "axiom-preflight",
        "axiom-phase7",
        "pytest tests -v",
    ]

    for phrase in required:
        assert phrase in text
