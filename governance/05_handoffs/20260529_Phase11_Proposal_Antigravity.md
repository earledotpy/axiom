# Antigravity Proposal & Assessment: Phase 11 Dashboard Modernization

**To:** Jeremy (Operator)  
**Cc:** Claude Code  
**From:** Antigravity  
**Date:** 2026-05-29  
**Subject:** Review of Phase 11 Dashboard Modernization Plan  

I have reviewed Claude's parked plan for the Phase 11 Dashboard Modernization (`20260529_Phase11_Dashboard_Modernization_Plan.md`). Below is my assessment and proposal regarding the strategy, technical details, timeline, and risks.

---

### 1. Overall Strategy Assessment & Approval
The proposed migration from a static PowerShell-based dashboard to a dynamic **Python Textual TUI** with a 4-pane **psmux** orchestration is an excellent direction. 
The 5-phase approach (11A through 11E) ensures that the foundational data layer is decoupled from presentation before the UI is built. Furthermore, the staged rollout strategy—keeping the legacy `axiom-dashboard` operational until cutover—effectively mitigates deployment risks. I am fully aligned with this strategy.

### 2. Technical Recommendations & Architectural Adjustments
While the plan is thorough, I recommend the following architectural refinements:
* **Asynchronous Data Fetching:** Textual operates on an async event loop. To ensure the UI remains snappy and responsive during the 5-second refresh cycle, the `AxiomDataClient` methods should either use `asyncio` or be dispatched via Textual's Worker API. This will prevent the UI from freezing while waiting for SQLite queries.
* **Fallback Strategy:** The plan suggests falling back to the legacy PowerShell dashboard if `psmux` is not found. Instead, I recommend maintaining a single source of truth by having the Python TUI gracefully degrade to a single-pane, full-screen Textual app (omitting the logs/chat panes) if `psmux` is absent. This eliminates the need to maintain legacy PowerShell code long-term.
* **IPC Chat Optimization:** The agent chat routing relies on reading/writing to `ipc/` markdown files. To avoid excessive disk I/O, we should utilize efficient file watchers (e.g., `watchdog` or asyncio-based polling) rather than aggressive polling loops.

### 3. Timeline and Resource Assessment
The 3-week timeline (approximately 22 days of implementation and testing) is realistic given the scope. However, Phase 11B (Building the TUI components) and Phase 11D (CLI migration) involve migrating a significant surface area of legacy code. I recommend budgeting an additional **2-3 days of contingency** for Phase 11B to ensure the advanced styling (CRT scanlines, responsive 35/65 grid) achieves the premium aesthetic you desire without cutting corners.

### 4. Gaps & Risks Identified
* **Performance / Main-Thread Blocking:** High risk if DB queries block the Textual event loop. This must be mitigated early in Phase 11A.
* **Database Concurrency & Read-Only Enforcement:** With multiple components (dashboard, CLI, background tasks) querying the DB simultaneously, SQLite locking could become an issue. We must rigidly enforce `?mode=ro` (read-only mode) on the dashboard's connection string, which also acts as a hard failsafe for our fail-closed posture.
* **Dependency Footprint:** Introducing `textual` and `rich` will slightly increase the project's complexity. We should pin specific stable versions in `requirements.txt` to avoid upstream breakages.

### 5. Ratification Assessment
The Phase 11 plan is well-conceived and aligns perfectly with the goal of creating a professional, unified operator console. 

**Recommendation:** I advise that we **ratify** this plan with the minor architectural adjustments noted above. 

---
**Next Steps:**
Please review this proposal. Once you explicitly approve it, we can release the hold on the parked document and I will authorize Codex to commence Phase 11A.
