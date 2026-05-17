# Evaluator Review — AXIOM Proposal v1.6

**Bottom line:** v1.6 closes seven of the eight v1.5 blockers cleanly. One new coherence issue was introduced in Item 4 (the ordered scanner rules contradict their own worked examples), and three smaller specifications remain. **One more targeted revision (v1.7) on these four points and the proposal is ready for the next stage.** Core Values 3 and 5 are now satisfied.

---

## What Holds

| v1.5 blocker | v1.6 resolution | Status |
|---|---|---|
| #1 Bootstrap executor | Dedicated `BootstrapValidationWorker` thread, narrow permissions, explicit non-coordination role | Closed |
| #2 OperatorControlInserter spoof protection | Three-layer architectural enforcement: thread identity + in-memory capability token + import boundary with static test | Closed (with one refinement noted below) |
| #3 Core Value 5 position on bootstrap | Explicit pre-agent infrastructure framing; write-allow/write-forbid table is concrete | Closed |
| #5 Telegram-thread crash | One-restart-then-safe-stop policy; operator-interface-down halts autonomous operation | Closed (with locus question noted) |
| #6 In-flight cloud call lifecycle | Synchronous calls on Scheduler thread; bounded cooperative cancellation; `started`/final usage row | Closed (with row semantics question noted) |
| #7 policy_approved lifecycle | Cleared on every recovered non-terminal task; preserved on terminal for audit | Closed |
| #8 `/enable_autonomous` + manifest source | Command added to bootstrap table with conditions; per-command static manifests; binding rule with four required conditions | Closed |

Items #1, #3, #7, #8 are unambiguously resolved. Items #2, #5, #6 are substantively resolved with minor gaps below.

---

## What Fails — One Blocker

### Item 4 — Worked examples contradict the ordered rules

This is the most significant issue in v1.6. The ordered rules and the worked examples produce different verdicts for the same artifact.

The worked example states:

> non-critical rule hit + classifier safe + confidence 0.94 = **allowed to continue** if no earlier rule matched

Walking the ordered rules for that artifact:

- Rule 5 requires a suspicious classifier label — does not match (label is `safe_data`).
- Rule 6 requires confidence < 0.90 — does not match (0.94).
- Rule 7 requires an *ordinary* artifact — does not match (the artifact is high-risk, because Item 2 of v1.5 makes any rule hit a high-risk trigger).
- **Rule 10 requires "No rule hits"** — does not match (there is a non-critical rule hit).
- The artifact falls through to Rule 11 → `needs_human_input`.

So under the rules as written, the artifact is **not** allowed to continue. The example expects `passed`; the rules produce `needs_human_input`.

This is exactly the precedence ambiguity v1.6 Item 4 was supposed to remove. It now exists in a different form: between the rules and the prose.

**Required fix (one of):**
1. Change Rule 10 to "No *critical* rule hits + valid schema + classifier safe with sufficient confidence → passed."
2. Or insert a new rule between 9 and 10: "High-risk artifact + classifier safe label + confidence ≥ 0.90 → passed."
3. Or change the worked example to acknowledge the artifact is sent to `needs_human_input` (and revisit whether that is the intended behavior).

Option 2 is most aligned with Item 2's threshold structure (0.90 is *the* high-risk pass threshold). Option 1 is simpler and probably correct.

This is a blocking issue. The whole point of the v1.5→v1.6 revision was to make the verdict pipeline deterministic. A contradiction between rules and examples means the implementer has to choose, which is precisely the failure mode the revision was meant to eliminate.

---

## What Needs Specification — Three Smaller Gaps

### Item 5 — SessionController locus is not placed in the thread model

> "SessionController attempts one Telegram restart"

If Telegram thread is dead and Scheduler thread is blocked on a cloud call (per Item 6, up to 90s), neither can run the restart. The implied answer is "main thread acts as supervisor" — that's plausible and standard, but v1.6 doesn't say it. Specify which thread runs SessionController and how it observes Telegram-thread death.

### Item 6 — provider_usage row semantics

The lifecycle text says ModelGateway "writes provider_usage row: status = started" then later "writes final provider_usage row/status". One row updated, or two rows inserted? And: if the process crashes between the two writes, an orphan `status=started` row exists. How does startup recovery reconcile it? Specify both.

### Item 2 — Thread identity check ordering

The conclusion in §3 claims operator-control creation is "architecturally restricted, not conventionally labeled." But the thread-identity check uses `threading.current_thread().name == "telegram_gateway_thread"` — and a thread name is just a string set at construction. Any code that does `Thread(name="telegram_gateway_thread", target=...)` defeats it.

The capability-token check (object identity, never serialized) is the actual security boundary, and the import-boundary test is the structural one. Both are sound. The thread-name check is the weakest of the three.

**Recommended refinement:** Either replace the name check with `threading.current_thread() is session.telegram_thread` (object identity), or list the layers in strength order so the name check is correctly framed as a tripwire rather than a primary boundary. This is not a Core Value 3 violation as long as the capability token and import boundary remain — but the doc's own phrasing overstates the strength of the first layer.

---

## Core Value Compliance

| Core Value | v1.6 status |
|---|---|
| 1 — Security baked in | ✓ Bootstrap mode, recovery clears stale approvals, three-layer operator-control, sync FULL pragmas |
| 2 — Local model in its lane | ✓ Bootstrap classifier uses local model for sanitizer purpose only |
| 3 — Zero-trust at agent boundaries | ✓ Architectural enforcement now in place (with thread-name caveat above) |
| 4 — Build simple | ✓ Worker thread chosen over limited Scheduler; sync calls chosen over background handler |
| 5 — Queue coordination | ✓ Bootstrap validation explicitly framed and bounded as pre-agent infrastructure |
| 6 — Sandbox/network separation | ✓ Preserved from v1.5; no regression |

No Core Value conflicts remain.

---

## Required Resolutions Before Approval

In priority order:

1. **Fix Item 4 internal contradiction** — adjust Rule 10 (or add a high-risk-passed rule) so the worked examples are consistent with the ordered rules. *Blocking.*
2. **Locate SessionController in the thread model** — name which thread observes and restarts on Telegram crash.
3. **Specify provider_usage row semantics** — one row UPDATEd vs two rows inserted, and orphan-row recovery on restart.
4. **Refine Item 2 thread-identity check** — replace name comparison with object identity, or reorder layers so the security claim is not overstated.

Items 2-4 are specifications, not contradictions. Item 1 is the contradiction.