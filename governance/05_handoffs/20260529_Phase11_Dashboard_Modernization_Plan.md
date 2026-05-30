# Phase 11: Dashboard Modernization — Textual TUI with psmux Orchestration

**From**: Claude Code (Governance Auditor)  
**To**: Codex (Implementation Specialist) & Jeremy (Operator)  
**Date**: 2026-05-29  
**ADR-0006 Step**: 1 — Planning phase for operator console modernization  
**Status**: PARKED - Ready for implementation when approved

---

## 1. Context & Rationale

**Current State:**
- Operator console is PowerShell-based text rendering via `axiom-dashboard` command
- Dashboard renders 6 panels (system posture, task queue, agent boundary, ledger, manifests, event stream)
- All data fetching uses inline Python queries embedded in PowerShell
- Color/styling defined in PowerShell ANSI codes
- Variant A/B switching based on autonomous mode
- psmux/tmux integration exists via `ipc/tmux_bridge.ps1` but underutilized

**Problem:**
- PowerShell text rendering is static and hard to extend
- Mockup created by Claude Design shows professional multi-panel layout that's difficult to achieve in PowerShell
- Current architecture mixes data fetching (Python) and presentation (PowerShell)
- No interactive widgets, limited real-time updates, no responsive layout

**Solution:**
Build a **Python Textual TUI** that:
1. Matches the operator console mockup visually and functionally
2. Uses psmux to orchestrate dashboard + logs + command input + agent chat in professional multi-pane layout
3. Extracts reusable Python data/formatting layer (shared by CLI commands, tests, TUI)
4. Migrates all CLI commands from PowerShell to Python with Rich formatting
5. Enables future enhancements (interactive selection, keyboard navigation, live updates)

**Why Now:**
- Phase 10 (PSMUX bridging + UI professionalization) is complete and tested
- Claude Design provided detailed mockup showing target design
- psmux is installed and working
- Python data layer is mature and stable
- Testing infrastructure is in place

**Outcome:**
Professional operator console matching mockup design, with staged migration path to minimize risk.

---

## 2. Implementation Strategy

### Phase 11A: Foundation & Data Layer (Week 1)

**Goal:** Extract reusable Python data modules and add Textual/Rich to dependencies.

**Files to Create:**
- `requirements.txt` — Add dependencies: `textual>=0.40.0`, `rich>=13.0.0`
- `ui/cli/__init__.py` — Python CLI module (new)
- `ui/cli/data.py` — Reusable data fetching (queries, formatting, shared utilities)
  - `class AxiomDataClient` — Database access wrapper
  - `fetch_session_data()`, `fetch_task_queue()`, `fetch_agent_boundary()`, `fetch_command_ledger()`, `fetch_manifest_integrity()`, `fetch_event_stream()`
  - `format_badge()`, `format_status()`, `format_table()` — Formatting helpers for Rich
- `ui/cli/colors.py` — Color scheme matching mockup
  ```python
  COLORS = {
      'bg_base': '#050A08',
      'bg_header': '#0D1F16',
      'bg_panel': '#07110D',
      'fg_base': '#C7F7C7',
      'fg_dim': '#5B7C6E',
      'green_bright': '#A8FF60',
      'green_accent': '#5CFFA4',
      'cyan_base': '#69D6C5',
      'blue_base': '#5AA7D8',
      'gold_base': '#FFD36E',
      'red_base': '#FF4B4B',
  }
  ```
- `ui/cli/commands.py` — Command utilities (help, doctor, status, etc.)
  - `class AxiomCommand` — Base class for CLI commands with Rich output
  - Subclasses: `StatusCommand`, `DoctorCommand`, `HelpCommand`, `ReadinessCommand`, etc.

**Migration from PowerShell:**
- Extract query logic from `40-dashboard.ps1` → Python `data.py`
- Extract color/styling from `39-operator-ui.ps1` → Python `colors.py`
- Extract command functions from `20-axiom-tools.ps1` → Python `commands.py`

**Update Files:**
- `requirements.txt` — Add `textual>=0.40.0`, `rich>=13.0.0`, `rich-tables` (optional)

**Testing:**
- Unit tests for `AxiomDataClient` (query functions)
- Unit tests for formatting functions
- Verify data structure compatibility with existing tests

---

### Phase 11B: Textual TUI Application (Week 2)

**Goal:** Build Textual app matching operator console mockup, feature-complete but not yet swapping the command.

**Files to Create:**
- `ui/tui/__init__.py` — TUI module entry
- `ui/tui/app.py` — Main Textual application
  ```python
  class AxiomConsoleApp(App):
      CSS = "ui/tui/styles.css"  # Textual CSS for layout, colors, positioning
      BINDINGS = [
          ("q", "quit", "Quit"),
          ("r", "refresh", "Refresh"),
          ("1", "variant_a", "Variant A"),
          ("2", "variant_b", "Variant B"),
          ("c", "command_input", "Command"),
      ]
      
      def compose(self) -> ComposeResult:
          """Yield child widgets (header, grid, footer)"""
          yield Header(...)
          yield SystemPosturePanel(...)
          yield TaskQueuePanel(...)
          # ... all 6 panels
          yield EventStreamPanel(...)
          yield Footer(...)
  ```
- `ui/tui/styles.css` — Layout and styling (grid 35%/65%, colors, fonts, spacing)
  ```css
  Screen {
      layout: vertical;
      background: $bg_base;
      color: $fg_base;
  }
  
  #grid {
      layout: grid;
      grid-size: 2 3;  /* 2 columns, 3 rows of panels */
      grid-columns: 35% 1fr;
      gap: 1 1;
  }
  ```
- `ui/tui/panels/` — Widget components for each panel
  - `header.py` — Header bar widget (sigils, title, status badge, timestamp, read-only indicator)
  - `system_posture.py` — System Posture panel
  - `task_queue.py` — Task Queue panel with table
  - `agent_boundary.py` — Agent Boundary panel with status dots
  - `command_ledger.py` — Operator Command Ledger panel (hash-chained, formatted)
  - `manifest_integrity.py` — Manifest Integrity panel with checkmarks
  - `event_stream.py` — Live Event Stream (tail -f style with badges)
  - `model_profile.py` — Model Profile / Trust section (full-width)
  - `next_actions.py` — Next Safe Actions footer
- `ui/tui/widgets/` — Reusable widget components
  - `badge.py` — Status badge widget (PASS, IDLE, WARN, BLOCK, FAIL, etc.)
  - `rule.py` — Horizontal rule (solid/dashed)
  - `panel.py` — Panel wrapper with title and body
  - `table.py` — Rich table with monospace font, proper alignment
  - `kv_row.py` — Key-value display (label + value with color coding)

**Variant Switching:**
- Query `autonomous_operation_enabled` from DB
- Dynamically show Variant A or Variant B layouts
  - Variant A: System Posture, Task Queue, Agent Boundary, Ledger, Manifests, Events
  - Variant B: System Posture, Execution Trace, Approval Gate, Autonomous Posture, Ledger, Manifests

**Interaction:**
- Keyboard shortcuts (r=refresh, 1/2=variant switch, q=quit)
- Real-time updates every 5 seconds (via background task)
- Mouse support for scrolling/selection (Textual built-in)
- Clickable panels for drill-down detail views

**Testing:**
- Pilot test with sample data
- Visual comparison to mockup
- Verify all panels render correctly
- Test variant switching
- Test refresh frequency (no excessive DB queries)

---

### Phase 11C: Multi-Pane psmux Orchestration with Agent Chat (Week 2)

**Goal:** Wire Textual app + event logs + agent chat + command input into professional 4-pane psmux session.

**Files to Create:**
- `ui/scripts/start_dashboard_session.ps1` — New startup script to launch psmux with Textual
  ```powershell
  function Start-AxiomConsoleSession {
      param([string]$SessionName = "axiom-operator-console")
      
      $tmux = Get-TmuxBinary
      if (-not $tmux) { Write-Error "psmux not found"; return }
      
      # Create main session with Textual dashboard
      & $tmux new-session -d -s $SessionName -c "C:\axiom" `
          -x 120 -y 40  # Standard terminal size
      
      # Pane 0: Textual TUI (dashboard)
      & $tmux send-keys -t $SessionName "python -m ui.tui.app" Enter
      
      # Pane 1: Event stream (right, 30%)
      & $tmux split-window -h -t $SessionName -p 30 -c "C:\axiom"
      & $tmux send-keys -t $SessionName "Get-Content C:\axiom\logs\axiom.log -Tail 50 -Wait | ForEach-Object { Write-Host `$_; Start-Sleep -Milliseconds 100 }" Enter
      
      # Pane 2: Agent chat (below dashboard, 30% height)
      & $tmux split-window -v -t $SessionName:0 -p 30 -c "C:\axiom"
      & $tmux send-keys -t $SessionName "python -m ui.tui.agent_chat" Enter
      
      # Pane 3: Command input (bottom, 10% height)
      & $tmux split-window -v -t $SessionName:0.0 -p 10 -c "C:\axiom"
      & $tmux send-keys -t $SessionName "PowerShell" Enter
      
      Write-Host "✓ Console session with agent chat started: $SessionName"
      Write-Host "  Attach: psmux attach-session -t $SessionName"
      Write-Host "  Agent shortcuts: Ctrl+C=Claude, Ctrl+X=Codex, Ctrl+A=Antigravity"
  }
  ```

- `ui/scripts/attach_dashboard_session.ps1` — Convenience script to attach to existing session
  ```powershell
  function Attach-AxiomConsoleSession {
      param([string]$SessionName = "axiom-operator-console")
      $tmux = Get-TmuxBinary
      & $tmux attach-session -t $SessionName
  }
  ```

- `ui/tui/panels/agent_chat.py` — Chat widget with agent routing
  ```python
  class AgentChatPanel(Container):
      DEFAULT_CSS = "..."
      
      def __init__(self):
          self.agents = ["claude", "codex", "antigravity"]
          self.active_agent = "claude"  # Default
          self.message_history = []
      
      def route_message(self, user_input: str):
          """Route user input to active agent via IPC"""
          # 1. Write to ipc/to_{agent}.md
          # 2. Wait for reply in ipc/from_{agent}.md
          # 3. Display reply in chat panel
          # 4. Add to message_history
      
      def render_chat(self):
          """Format chat thread with agent labels, colors, timestamps"""
          for msg in self.message_history:
              label = f"[{msg.agent}]".ljust(12)  # Align agent names
              color = self.agent_color(msg.agent)
              timestamp = msg.timestamp.strftime("%H:%M:%S")
              text = f"{color}{timestamp} {label} {msg.text}"
              # Render via Rich
  ```

- `ui/tui/components/agent_selector.py` — Tab/dropdown for agent selection
  ```python
  class AgentSelector(Static):
      """Switch between Claude, Codex, Antigravity with keyboard or click"""
      
      BINDINGS = [
          ("c", "select_claude", "Claude"),
          ("x", "select_codex", "Codex"),
          ("a", "select_antigravity", "Antigravity"),
      ]
      
      def post_message(self, action: str):
          self.emit_no_wait(AgentSelected(action.split('_')[1]))
  ```

**IPC Integration:**
- Chat pane connects to existing IPC message bus (`ipc/to_{agent}.md` files)
- User input routed to selected agent via keyboard shortcuts
- Responses displayed with agent labels, timestamps, and color coding
- Message history kept in memory (exportable to log)

**Pane Layout:**
```
┌─────────────────────────────────┬──────────────┐
│                                 │              │
│  Main Dashboard (Textual)       │ Event Stream │
│  - Header                       │ (tail -f)    │
│  - 6 Panels                     │              │
│  - Interactive controls         │ Live logs    │
│                                 │              │
├─────────────────────────────────┴──────────────┤
│ Agent Chat Pane (30% height)                    │
│ [Claude  ] Ctrl+C ┃ [Codex   ] Ctrl+X ┃       │
│ [Antigravity] Ctrl+A                          │
│                                                │
│ [Claude  ] 14:07:42 Status of current session?│
│ [System ] Claude is processing...            │
│ [Claude  ] ✓ 14:07:45 System status: idle... │
│                                                │
│ [Codex  ] > _                                  │ ← User typing
├─────────────────────────────────────────────────┤
│ Command Input (PowerShell REPL) (10% height)   │
│ $ axiom status                                 │
│ [output from last command]                    │
│ $                                               │
└─────────────────────────────────────────────────┘
```

**Update Files:**
- `ui/terminal/profile/profile-axiom.ps1` — Change `axiom-dashboard` function to launch psmux session
  ```powershell
  function axiom-dashboard {
      if (Test-CommandExists psmux -or Test-CommandExists tmux) {
          Start-AxiomConsoleSession
      } else {
          Write-Warning "psmux not found. Install with: winget install psmux"
          Write-Host "Falling back to legacy PowerShell dashboard..."
          # Call old dashboard function
      }
  }
  ```

**Testing:**
- Verify psmux session creates all 4 panes correctly
- Test pane focus switching (Ctrl+B arrow keys)
- Verify Textual app runs in Pane 0 without blocking
- Verify event stream updates independently in Pane 1
- Verify agent chat routes messages correctly in Pane 2
- Verify command input accepts keyboard input in Pane 3
- Test graceful fallback if psmux not found

---

### Phase 11D: Python CLI Commands Migration (Week 3)

**Goal:** Migrate `axiom-dashboard`, `axiom-help`, `axiom-doctor`, `axiom-status`, etc. from PowerShell to Python.

**Files to Create:**
- `tools/axiom_cli.py` — Unified CLI entry point
  ```python
  import argparse
  from ui.cli.commands import StatusCommand, DoctorCommand, HelpCommand, ...
  
  def main():
      parser = argparse.ArgumentParser(prog='axiom')
      subparsers = parser.add_subparsers(dest='command', help='AXIOM commands')
      
      # Register commands
      subparsers.add_parser('status', help='Show current status')
      subparsers.add_parser('doctor', help='Run system diagnostics')
      subparsers.add_parser('help', help='Show available commands')
      # ... etc
      
      args = parser.parse_args()
      cmd = resolve_command(args.command)
      result = cmd.execute()
      cmd.print_result(result)  # Rich output
  
  if __name__ == '__main__':
      main()
  ```

- `tools/axiom_dashboard.py` — New Python entry for dashboard
  ```python
  from ui.tui.app import AxiomConsoleApp
  
  if __name__ == '__main__':
      app = AxiomConsoleApp()
      app.run()
  ```

**Update Files:**
- `ui/terminal/modules/utilities/20-axiom-tools.ps1` — Functions now call Python CLI
  ```powershell
  function axiom-status {
      python tools/axiom_cli.py status
  }
  
  function axiom-doctor {
      python tools/axiom_cli.py doctor
  }
  
  function axiom-help {
      python tools/axiom_cli.py help
  }
  
  function axiom-dashboard {
      Start-AxiomConsoleSession  # Psmux orchestration
  }
  ```

**Command List to Migrate:**
1. `axiom-status` — Show session status
2. `axiom-doctor` — Run diagnostics
3. `axiom-help` — Show commands
4. `axiom-readiness` — Show execution readiness
5. `axiom-preflight` — Run pre-flight checks
6. `axiom-queue` — Show task queue
7. `axiom-model` — Show current model
8. `axiom-manifests` — Show manifests
9. `axiom-budget` — Show resource budget
10. `axiom-events` — Show recent events

Each should output Rich-formatted text with colors/tables.

**Testing:**
- Unit tests for each command (return correct data structure)
- Integration tests (command runs end-to-end)
- Verify Rich output renders in terminal
- Verify exit codes

---

### Phase 11E: Feature Parity Testing & Verification (Week 3)

**Goal:** Verify Textual TUI has all features of current dashboard, passes all tests, no regressions.

**Verification Checklist:**

1. **Data Accuracy:**
   - [ ] System Posture panel matches current dashboard
   - [ ] Task Queue table matches current output
   - [ ] Agent Boundary matches current output
   - [ ] Command Ledger displays correctly
   - [ ] Manifest Integrity shows all manifests
   - [ ] Event Stream shows latest events with correct timestamps
   - [ ] Model Profile section displays candidate model correctly

2. **Variant Switching:**
   - [ ] Variant A displays on `autonomous_operation_enabled=0`
   - [ ] Variant B displays on `autonomous_operation_enabled=1`
   - [ ] Switching between variants via keyboard (1/2 keys) works
   - [ ] Manual override flag works: `python ui/tui/app.py --variant A`

3. **Visual Fidelity:**
   - [ ] Colors match mockup palette (test with mockup side-by-side)
   - [ ] Layout matches 35%/65% grid
   - [ ] Badges display with correct colors
   - [ ] Tables align properly with monospace font
   - [ ] Text wrapping doesn't corrupt output
   - [ ] CRT scanline overlay effect renders correctly

4. **Interaction:**
   - [ ] Keyboard shortcuts work (r=refresh, q=quit, 1/2=variant, c=command)
   - [ ] Mouse scrolling works in panels
   - [ ] Clickable panels open detail views
   - [ ] Refresh every 5s updates all panels
   - [ ] No excessive DB queries (monitor with `tools/bootstrap_check.py`)

5. **psmux Session:**
   - [ ] `axiom-dashboard` launches psmux session with 4 panes
   - [ ] Textual app runs in Pane 0 without crashing
   - [ ] Event stream updates in Pane 1 independently
   - [ ] Agent chat routes messages in Pane 2 correctly
   - [ ] Command input in Pane 3 accepts keyboard input
   - [ ] Graceful fallback if psmux not found

6. **Agent Chat:**
   - [ ] Messages route to correct agent via IPC
   - [ ] Agent responses display with correct labels and timestamps
   - [ ] Agent selector works (keyboard shortcuts C/X/A)
   - [ ] Multi-agent conversation flows correctly (isolated responses)
   - [ ] Timeout handling: agent doesn't respond within 30s → show "no response" error
   - [ ] Chat history visible during session (scrollback)

7. **Python CLI Commands:**
   - [ ] `axiom status` returns formatted output
   - [ ] `axiom doctor` runs diagnostics with colors
   - [ ] `axiom help` shows available commands
   - [ ] All existing PowerShell commands have Python equivalents
   - [ ] Exit codes match expected values

8. **Test Suite:**
   - [ ] All 588 existing tests still pass
   - [ ] New unit tests for `ui.cli.data` module (80%+ coverage)
   - [ ] New unit tests for `ui.cli.commands` module
   - [ ] New integration tests for Textual app (data -> widgets)
   - [ ] psmux orchestration tested (bash script, not pytest)

9. **Fail-Closed Compliance:**
   - [ ] TUI respects `autonomous_allowed=False` (no unsafe shortcuts visible)
   - [ ] TUI respects `safe_pass_enabled=False` (safe pass not offered)
   - [ ] TUI respects fail-closed posture (no state-mutating commands in footer)
   - [ ] No runtime policy violations logged

**Test Commands:**
```bash
pytest tests/ -v
python tools/bootstrap_check.py
python tools/audit_task_lifecycle.py
python -m ui.tui.app --help  # Test app startup
python tools/axiom_cli.py status  # Test CLI commands
```

---

## 3. Critical Files & Dependencies

| Category | Files | Notes |
|----------|-------|-------|
| **New Python Modules** | `ui/cli/__init__.py`, `ui/cli/data.py`, `ui/cli/colors.py`, `ui/cli/commands.py` | Extracted from PowerShell; reusable across CLI, TUI, tests |
| **New TUI App** | `ui/tui/app.py`, `ui/tui/styles.css`, `ui/tui/panels/`, `ui/tui/widgets/` | Main Textual application; matches mockup design |
| **psmux Scripts** | `ui/scripts/start_dashboard_session.ps1`, `attach_dashboard_session.ps1` | Orchestration; launches multi-pane session |
| **Agent Chat** | `ui/tui/panels/agent_chat.py`, `ui/tui/components/agent_selector.py` | Chat widget with IPC routing; agent selection UI |
| **CLI Entry** | `tools/axiom_cli.py`, `tools/axiom_dashboard.py` | Python equivalents of PowerShell commands |
| **Updated** | `ui/terminal/modules/utilities/20-axiom-tools.ps1` | Functions now call Python CLI or psmux |
| **Dependencies** | `requirements.txt` | Add: `textual>=0.40.0`, `rich>=13.0.0` |

**Reusable Code from Codebase:**
- `axiom/persistence/repositories.py` — Use `get_connection()`, `get_session()` pattern
- `axiom/app/status_report.py` — Use `build_status_report()` for data fetching
- `ui/terminal/modules/shared/39-operator-ui.ps1` — ANSI color codes (migrate to `ui/cli/colors.py`)
- `ipc/tmux_bridge.ps1` — Use `Get-TmuxBinary()` function (already working)

---

## 4. Migration Strategy & Risk Management

### Staged Rollout:

**Phase 11A-11C (Weeks 1-2): Build in Parallel**
- Textual app runs in new `ui/tui/` directory
- PowerShell `axiom-dashboard` continues unchanged
- Python CLI commands in `tools/axiom_cli.py` (opt-in, not default)
- **Risk**: Minimal — no existing functionality disrupted

**Phase 11D-11E (Week 3): Feature Parity & Testing**
- Verify TUI matches all mockup requirements
- Verify all existing tests pass
- Compare visual output side-by-side with mockup
- Stress-test DB query performance
- **Risk**: Medium — need to ensure no data loss or performance regression

**Cutover (After approval):**
- Swap `axiom-dashboard` command to use psmux + Textual
- Deprecate PowerShell dashboard modules (keep for reference)
- Update documentation
- **Risk**: Low — if TUI has parity and tests pass

### Rollback Plan:

If issues found post-cutover:
```bash
# Restore PowerShell dashboard
git checkout HEAD -- ui/terminal/modules/operators/40-dashboard.ps1
# Disable Python TUI
mv ui/tui ui/tui.bak

# Verify fallback works
axiom-doctor
```

### Fail-Closed Considerations:

- Textual app **must** respect `autonomous_allowed=False` — no state mutations in UI
- All DB queries **must** be read-only (`?mode=ro`)
- Command suggestions (Next Safe Actions) **must** exclude dangerous commands
- Model profile section **must** respect `safe_pass_enabled=False`
- **Test**: `tools/audit_policy_security.py` must pass throughout

---

## 5. Timeline

| Phase | Duration | Owner | Deliverable |
|-------|----------|-------|-------------|
| **11A** | 5 days | Codex | `ui/cli/` module, dependencies added, data layer extracted |
| **11B** | 6 days | Codex | `ui/tui/` app complete, all panels functional, styles match mockup |
| **11C** | 3 days | Codex | psmux orchestration, multi-pane session, agent chat working |
| **11D** | 4 days | Codex | Python CLI commands, all PowerShell functions ported |
| **11E** | 4 days | Codex + Claude | Feature parity testing, visual comparison, audit compliance |
| **Cutover** | 1 day | Jeremy | Deploy, monitor, rollback if needed |
| **Total** | ~3 weeks | — | Professional operator console matching mockup |

---

## 6. User Preferences (Confirmed)

✓ **CRT Scanline Overlay**: YES — Implement CSS background pattern for visual authenticity  
✓ **Interactive Elements**: YES — Panels should be clickable (task details, manifest drill-down, etc.)  
✓ **Real-time Updates**: 5-second refresh interval (can be tuned later)  
✓ **Command History**: YES — readline history + autocomplete in command pane; live agent chat updates  
✓ **Multi-session**: Single session primary; support multi-session mode as secondary feature  

---

## 7. Success Criteria

- [ ] Textual TUI displays all 8 panels matching mockup colors/layout
- [ ] All 588 existing tests pass
- [ ] Feature parity: TUI shows same data as current dashboard
- [ ] psmux session launches with 4 panes (dashboard + logs + agent chat + input)
- [ ] Agent chat routes messages correctly to Claude, Codex, Antigravity
- [ ] All CLI commands migrated to Python with Rich formatting
- [ ] No fail-closed violations (audit tools pass)
- [ ] Performance: <2 queries per refresh cycle, <100ms response time
- [ ] Visual comparison: Side-by-side with mockup shows match
- [ ] Documentation: Updated README and help text
- [ ] Keyboard navigation: All shortcuts work (r, 1, 2, q, c, agent shortcuts)
- [ ] Graceful fallback: Works without psmux (single window mode)
- [ ] Variant switching: A/B modes display correctly based on DB state
