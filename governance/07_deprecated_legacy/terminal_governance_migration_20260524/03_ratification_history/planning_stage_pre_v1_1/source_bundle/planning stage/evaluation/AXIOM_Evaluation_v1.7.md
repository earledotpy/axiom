# Evaluator Review — AXIOM Proposal v1.7

**Bottom line:** v1.7 closes all four v1.6 items cleanly. The architecture spine is stable, Core Values 1–6 are satisfied, no contradictions remain, and the worked examples now match the rules they document. **Approve to advance to the next panel stage.** Two minor specification touch-ups are noted below — neither blocks approval; both can be folded into implementation planning.

---

## What Holds

| v1.6 blocker | v1.7 resolution | Status |
|---|---|---|
| #1 Scanner rules ↔ examples contradiction | Added Rule 10 (high-risk passed at ≥0.90) and split Rule 11 (ordinary passed at ≥0.80); all six worked examples now trace through the ordered rules to the stated decisions | Closed |
| #2 SessionController locus | Placed on main supervisor thread; observes Telegram via `is_alive()`; runs while Scheduler is blocked on synchronous cloud calls | Closed |
| #3 provider_usage row semantics | One row per call, INSERTed as `started`, UPDATEd to final status; orphan recovery marks pre-existing `started` rows as `abandoned_session_crash` and charges estimates to budget | Closed |
| #4 Thread-identity check strength | Object identity (`current_thread() is session.telegram_thread`) replaces name comparison; capability-object identity is now correctly named as the primary boundary; component-name string explicitly demoted to audit-only | Closed |

I traced every worked example in §2 through the new ordered rules independently. They all produce the stated decisions — including the boundary cases at exactly 0.90 (high-risk passes via Rule 10) and exactly 0.80 (ordinary passes via Rule 11), since the strict `<` in Rules 6 and 7 leaves the boundary to the `≥` rules below.

---

## Minor Specifications Worth Tightening

Neither blocks approval. Both can be addressed during implementation planning by Kimi or in a non-revision clarification.

### Orphan provider_usage recovery scope is too narrow

The recovery query targets:

```
WHERE status = 'started' AND session_id = previous_session_id
```

This catches orphans from the immediately-previous session only. If the system crashed in session N-1 *and* session N-2 (e.g., a recurring bug across two restarts), the older orphan is missed.

Recommended rewrite:

```
WHERE status = 'started' AND session_id != current_session_id
```

Or equivalently: `WHERE status = 'started' AND session_id IN (SELECT id FROM sessions WHERE ended_at IS NOT NULL OR status = 'crashed')`. The conservative-budgeting intent is preserved either way; the scope just needs to be "not me" rather than "the one before me."

### Classifier-only suspicious detection falls through to `needs_human_input`

This emerged once Rules 10 and 11 were split. Consider an artifact with **no rule hit**, classifier label `embedded_instruction`, confidence 0.95:

- Rule 5 doesn't fire (requires both a rule hit *and* a suspicious classifier label).
- Rule 6 doesn't fire (confidence 0.95 ≥ 0.90).
- Rules 10–11 don't fire (require `safe_data` or `untrusted_data` label).
- Falls to Rule 12 → `needs_human_input`.

The result is safe in Phase 1 — the operator reviews it — but it treats a confident classifier judgment of `embedded_instruction` as merely advisory rather than authoritative. There is a defensible design reading here: rules-or-double-confirmation auto-quarantine; classifier-alone defers to human. If that's the intent, document it. If not, consider adding a rule between 5 and 6:

> Classifier label in `{embedded_instruction, tool_request, quarantine, needs_cloud_review}` + confidence ≥ 0.80 → quarantined

I lean toward "this is a design choice, not a defect" — but the choice should be made explicit somewhere in the document, since v1.7 doesn't currently address what happens when the classifier catches something the rules miss.

---

## Core Value Compliance

| Core Value | v1.7 status |
|---|---|
| 1 — Security baked in | ✓ Strengthened: orphan recovery preserves budget integrity; capability-object identity is the primary boundary |
| 2 — Local model in its lane | ✓ Unchanged from v1.6 |
| 3 — Zero-trust at agent boundaries | ✓ Object identity, not name convention |
| 4 — Build simple | ✓ One-row provider_usage simpler than two-row; main supervisor is standard Python pattern |
| 5 — Queue coordination | ✓ Unchanged from v1.6 |
| 6 — Sandbox/network separation | ✓ Unchanged from v1.6 |

No conflicts.