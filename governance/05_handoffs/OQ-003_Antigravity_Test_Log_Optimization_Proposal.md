# Proposal: AXIOM Test Suite and Logs Directory Optimization

**From**: Antigravity (Chief Architect)  
**To**: Jeremy (Operator), Claude Code (Auditor), Codex (Implementation Specialist)  
**Date**: 2026-05-28  
**Question ID**: OQ-003 (Verification Commands and Test Preflights)

---

## 1. Requested Decision

Approve the execution of a test and log directory optimization workflow to reduce test runtimes by 70%, eliminate test file pollution in the repository, and improve developer/CI iteration speed.

---

## 2. Affected Scope

* **Files to Modify**:
  * [tests/conftest.py](file:///C:/axiom/tests/conftest.py) — to mock/monkeypatch `LOG_DIR` for tools, routing test logs to temporary directories rather than the workspace.
  * [pytest.ini](file:///C:/axiom/pytest.ini) — to add speed markers or custom filters.
  * `tests/` — consolidate 25+ documentation-checking test modules into a single `tests/test_historical_docs.py` file, and refactor slow `subprocess.run` CLI tests to call internal functions.
* **Roles Affected**: None.
* **Bindings Affected**: None (runtime safety checks remain identical; this is an implementation-only optimization).
* **Runtime Behavior**: No changes to the operational app.

---

## 3. Classification

This is an **Implementation** and **Verification** optimization. It does not alter active bindings or runtime safety policies.

---

## 4. Supporting Evidence

* **Process Overhead**: In our test audit, executing CLI test cases on Windows using `subprocess.run([sys.executable, ...])` dominates the test runtime, accumulating 2–3 seconds per test block.
* **Log Pollution**: Currently, test runs write temporary output files (snapshots, manifests, and handoff markdown files) directly to [logs/](file:///C:/axiom/logs/), generating untracked clutter.
* **Archiving Success**: Manual execution of `tools/archive_logs.py` confirmed we can clean up older logs effectively (zipped 76 files and left only the safety buffer).

---

## 5. Proposed Approach & Implementation Plan

If approved, the optimization will be performed in a single Step 2 (Implement) pass by Codex:

1. **Log Isolation (conftest.py)**:
   Add an autouse fixture to [tests/conftest.py](file:///C:/axiom/tests/conftest.py) to redirect log output from tools during tests:
   ```python
   @pytest.fixture(autouse=True)
   def isolate_tool_logs(tmp_path, monkeypatch):
       monkeypatch.setattr("tools.snapshot_project_state.LOG_DIR", tmp_path)
       monkeypatch.setattr("tools.generate_handoff.LOG_DIR", tmp_path)
       monkeypatch.setattr("tools.generate_handoff_bundle.LOG_DIR", tmp_path)
   ```
2. **Selective Execution Command**:
   Add a fast verification target. Developers can run:
   ```powershell
   pytest tests -k "not doc and not cli" -v
   ```
   to execute all core unit tests in **< 60 seconds** while reserving the full `pytest tests -v` for final preflight checks.
3. **Consolidation**:
   Consolidate the 25 `test_phase*_doc.py` files into a single, clean test module (`tests/test_historical_docs.py`), reducing discovery overhead.

---

## 6. Risks and Unresolved Assumptions

* **Risk of Regression**: Inadvertently modifying or consolidating core tests could skip critical coverage.
* **Mitigation**: The consolidation is strictly limited to static document checking tests (`test_phase*_doc.py`). Active code tests (gateways, scheduler, database, state machine) will not be touched or combined.

---

## 7. Handoff & Next Steps

* **Current Step**: Antigravity has drafted this proposal (saved to `governance/05_handoffs/OQ-003_Antigravity_Test_Log_Optimization_Proposal.md`).
* **Next Step**: **Jeremy** to review and approve. Upon approval, **Codex** will own the implementation step (Step 2) to apply the optimization.
