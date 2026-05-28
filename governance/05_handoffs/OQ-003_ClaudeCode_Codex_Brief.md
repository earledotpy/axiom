# OQ-003 Implementation Brief: Test Suite and Log Optimization

**From**: Claude Code (Governance Auditor)
**To**: Codex (Implementation Specialist)
**Date**: 2026-05-28
**ADR-0006 Step**: 2 — Codex implements

---

## Operator Authorization

Jeremy has approved the OQ-003 proposal (`OQ-003_Antigravity_Test_Log_Optimization_Proposal.md`) on 2026-05-28.

---

## Scope Correction — Read Before Implementing

Antigravity's proposal was drafted before the phase doc consolidation (`6409e03`), which reduced the doc test file count from 25+ to 9. The consolidation scope in the proposal is stale.

**Current file counts (verified 2026-05-28):**

| Category | Pattern | Count | Action |
|---|---|---|---|
| Pure doc tests | `test_phase*_doc.py` + `test_phase5_docs.py` | 9 | Consolidate into `test_historical_docs.py` |
| Functional phase tests | `test_phase6_telegram_gateway.py`, `test_phase7_e2e_readiness_approval.py`, etc. | 16 | **Do not touch** |

The 16 functional tests import live modules, run DB and gateway logic, and cover real behavior. They must remain as separate files. Only the 9 doc-only tests are candidates for consolidation.

**Files to consolidate** (the 9 doc-only tests):
- `tests/test_phase2_closeout_doc.py`
- `tests/test_phase3_closeout_doc.py`
- `tests/test_phase3_policy_security_audit_doc.py`
- `tests/test_phase4_closeout_doc.py`
- `tests/test_phase4_gateway_readiness_doc.py`
- `tests/test_phase5_docs.py`
- `tests/test_phase6_entry_gate_doc.py`
- `tests/test_phase8a_release_freeze_documentation_reconciliation_doc.py`
- `tests/test_phase8b_repository_cleanup_plan_doc.py`

---

## Approved Implementation Steps

### 1. Log isolation (`tests/conftest.py`)

Add an autouse fixture to redirect tool log output to `tmp_path` during tests:

```python
@pytest.fixture(autouse=True)
def isolate_tool_logs(tmp_path, monkeypatch):
    monkeypatch.setattr("tools.snapshot_project_state.LOG_DIR", tmp_path)
    monkeypatch.setattr("tools.generate_handoff.LOG_DIR", tmp_path)
    monkeypatch.setattr("tools.generate_handoff_bundle.LOG_DIR", tmp_path)
```

Before adding: verify that `LOG_DIR` is a module-level name in each of those tools. If a tool uses a different attribute name, match it exactly.

### 2. Consolidate doc tests (`tests/test_historical_docs.py`)

Create `tests/test_historical_docs.py` that reproduces all assertions from the 9 files listed above, then delete those 9 files. No test coverage may be dropped.

### 3. Fast verification target

The approved fast target is:

```powershell
pytest tests -k "not doc and not cli" -v
```

This is the answer to OQ-003. No `pytest.ini` marker changes are required — the `-k` filter on the existing naming convention is sufficient.

---

## Files to Create or Modify

| File | Change |
|---|---|
| `tests/conftest.py` | Add `isolate_tool_logs` fixture |
| `tests/test_historical_docs.py` | New file — consolidated doc assertions |
| `tests/test_phase2_closeout_doc.py` | Delete |
| `tests/test_phase3_closeout_doc.py` | Delete |
| `tests/test_phase3_policy_security_audit_doc.py` | Delete |
| `tests/test_phase4_closeout_doc.py` | Delete |
| `tests/test_phase4_gateway_readiness_doc.py` | Delete |
| `tests/test_phase5_docs.py` | Delete |
| `tests/test_phase6_entry_gate_doc.py` | Delete |
| `tests/test_phase8a_release_freeze_documentation_reconciliation_doc.py` | Delete |
| `tests/test_phase8b_repository_cleanup_plan_doc.py` | Delete |

**Do not modify** `pytest.ini`, `axiom/`, `tools/` (except following the log fixture check above), or any of the 16 functional phase test files.

---

## Verification Bar

After implementing:

```powershell
pytest tests -v                                    # full suite — all tests pass
pytest tests -k "not doc and not cli" -v           # fast target — passes and is meaningfully faster
python tools/verify_foundation.py                  # foundation_passed: True, fail_closed_coherent: True
```

Claude Code will review the uncommitted diff and run `pytest` before Jeremy approves.
