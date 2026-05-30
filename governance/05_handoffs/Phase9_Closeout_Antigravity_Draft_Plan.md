# Phase 9 Closeout: Automatic Scheduler→Executor Integration Draft Plan

**From**: Antigravity (Chief Architect)  
**To**: Codex (Implementation Specialist)  
**Date**: 2026-05-29  
**ADR-0006 Step**: 1 — Antigravity produces the written task plan  

---

## 1. Goal and Scope

Establish the official closeout, audit verification, and documentation hardening for **Phase 9: Automatic Scheduler→Executor Integration**. This ensures that the newly implemented automatic execution for `manual_noop` tasks in the scheduler loop is fully reconciled, bounded, and audited for safety, while maintaining AXIOM's local-first, fail-closed, non-autonomous posture.

---

## 2. Affected Files

The closeout slice involves editing and creating the following files:
1. **[docs/phase9.md](file:///C:/axiom/docs/phase9.md)** (New) — Canonical closeout documentation detailing the scope, invariants, verified proof, and prohibitions.
2. **[tools/audit_phase9_closeout.py](file:///C:/axiom/tools/audit_phase9_closeout.py)** (New) — Read-only verification script auditing Phase 9 files, terminal commands, registry entries, and safety invariants.
3. **[tests/test_phase9_closeout.py](file:///C:/axiom/tests/test_phase9_closeout.py)** (New) — Pytest suite verifying the closeout audit tool runs and reports 0 violations.
4. **[tests/test_historical_docs.py](file:///C:/axiom/tests/test_historical_docs.py)** (Modified) — Assert that `docs/phase9.md` exists and contains all required security and boundary phrases.
5. **[ui/terminal/modules/20-axiom-tools.ps1](file:///C:/axiom/ui/terminal/modules/20-axiom-tools.ps1)** (Modified) — Add `axiom-phase9-closeout` function.
6. **[ui/terminal/modules/49-doctor.ps1](file:///C:/axiom/ui/terminal/modules/49-doctor.ps1)** (Modified) — Register the closeout command in the `axiom-doctor` verification checklist.
7. **[ui/terminal/modules/52-docs.ps1](file:///C:/axiom/ui/terminal/modules/52-docs.ps1)** (Modified) — Register Phase 9 help topics and mapping to `docs/phase9.md`.
8. **[ui/terminal/modules/90-safety-help.ps1](file:///C:/axiom/ui/terminal/modules/90-safety-help.ps1)** (Modified) — Document the closeout command under safety help display.
9. **[ui/terminal/registry/axiom-terminal-command-registry.json](file:///C:/axiom/ui/terminal/registry/axiom-terminal-command-registry.json)** (Modified) — Register command metadata and append to the `axiom-preflight` backing tools.

---

## 3. Proposed Approach & Key Decisions

### Documenting Phase 9 Boundaries
Create **[docs/phase9.md](file:///C:/axiom/docs/phase9.md)** containing these key phrases:
* `"Phase 9 is closed"`
* `"automatic scheduler-to-executor integration for manual_noop tasks"`
* `"fail_closed_non_autonomous"`
* `"one-running-task invariant remains enforced"`
* `"verification commands: pytest tests"`
* `"no real model, cloud, network, sandbox, memory, Telegram, agent, or general task scheduler authority is enabled"`

Update **[test_historical_docs.py](file:///C:/axiom/tests/test_historical_docs.py)** to assert the presence of these exact strings in `docs/phase9.md`.

### Closeout Audit Script
Implement **[tools/audit_phase9_closeout.py](file:///C:/axiom/tools/audit_phase9_closeout.py)** to check:
1. All required Phase 9 artifacts exist.
2. The terminal command `axiom-phase9-closeout` is registered in `axiom-terminal-command-registry.json` as a low-risk, non-mutating command backed by `tools/audit_phase9_closeout.py`.
3. `tools/audit_phase9_closeout.py` is listed in the `axiom-preflight` backing tools.
4. All terminal modules (`20-axiom-tools.ps1`, `49-doctor.ps1`, `52-docs.ps1`, `90-safety-help.ps1`) contain the correct registration hooks.
5. The closeout documentation contains all required security phrases.
6. Verify no unauthorized state changes or execution pathways (e.g. general task automation, background loops, autonomous enablement, or model promotion shortcuts) exist.

### Terminal Wiring
* **[20-axiom-tools.ps1](file:///C:/axiom/ui/terminal/modules/20-axiom-tools.ps1)**:
  ```powershell
  function axiom-phase9-closeout {
      Invoke-AxiomPython @('tools\audit_phase9_closeout.py')
  }
  ```
* **[49-doctor.ps1](file:///C:/axiom/ui/terminal/modules/49-doctor.ps1)**: Add `"axiom-phase9-closeout"` to the verification lists.
* **[52-docs.ps1](file:///C:/axiom/ui/terminal/modules/52-docs.ps1)**: Add mappings:
  ```powershell
  "phase9-closeout" = @{
      path = "docs\phase9.md"
  }
  "phase9-closeout-audit-tool" = @{
      path = "tools\audit_phase9_closeout.py"
  }
  ```

---

## 4. Verification Steps

To verify the closeout implementation:
```powershell
# 1. Run the foundation verification to confirm baseline state is clean
python tools/verify_foundation.py

# 2. Run the newly created closeout audit script
python tools/audit_phase9_closeout.py

# 3. Specifically run the closeout doc and historical doc tests
pytest tests/test_phase9_closeout.py tests/test_historical_docs.py -v

# 4. Run the full test suite
pytest tests -v
```

---

## 5. Rollback Plan

If the closeout slice introduces errors:
1. Revert edits on modified files and delete new files:
   ```powershell
   git checkout HEAD -- tests/test_historical_docs.py ui/terminal/modules/20-axiom-tools.ps1 ui/terminal/modules/49-doctor.ps1 ui/terminal/modules/52-docs.ps1 ui/terminal/modules/90-safety-help.ps1 ui/terminal/registry/axiom-terminal-command-registry.json
   Remove-Item docs/phase9.md, tools/audit_phase9_closeout.py, tests/test_phase9_closeout.py -ErrorAction SilentlyContinue
   ```
2. Verify that the original test suite passes successfully.

---

## 6. Risks and Constraints
* **No Runtime Modifications**: This slice must not modify any runtime Python modules (`axiom/**/*.py`). It is purely documentation, testing, and UI verification.
* **Preserve Invariants**: Ensure that safety limits (no-op only, single-running task) are not bypassed during terminal execution checks.
