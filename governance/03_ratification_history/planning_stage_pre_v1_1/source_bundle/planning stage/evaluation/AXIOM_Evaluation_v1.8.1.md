# Evaluator Review — AXIOM Proposal v1.8.1

**Bottom line:** Both patches resolve the items I flagged in v1.8 cleanly. Patch 1 closes the sandbox/heartbeat math gap; Patch 2 makes §16 canonical and pre-empts future prose/table drift. Architecture spine unchanged, no new gaps introduced. **Approve to advance.** v1.8 + v1.8.1 together constitute the proposal that goes to Critic / Arbiter / Constraints for delta-confirmation and then to Kimi for implementation planning.

---

## Patch 1 — Sandbox Duration Cap

| Required | Delivered | Verdict |
|---|---|---|
| Per-sandbox-execution duration cap | `max_sandbox_execution_seconds = 60` | ✓ |
| Derived to fit within 120s heartbeat threshold | Math shown: 60s cap + 30s margin = 90s, inside 120s threshold | ✓ |
| Enforced via Windows Job Object | "Job Object timeout / process termination" | ✓ |
| Parallel to existing 256 MB RAM cap | Listed alongside RAM in same enforcement table | ✓ |
| Updates to §2 binding conditions | Explicit replacement text provided | ✓ |
| Updates to §12 resource limits table | New row added with pre-dispatch gate + post-dispatch action | ✓ |
| Acceptance test | `test_sandbox_duration_cap.py` with four assertions, including the heartbeat false-positive check | ✓ |

**Math audit.** I traced the worst-case heartbeat gap independently:

- Sandbox runs the full 60s. Heartbeat last updated at sandbox start. Gap = 60s. < 120s threshold → safe.
- Cloud call runs the full 90s. Heartbeat last updated immediately before call. Gap = 90s. < 120s threshold → safe.
- Sandbox (60s) → heartbeat update → cloud call (90s). Each blocking op individually within bounds; heartbeat update between them. Max gap = 90s. Safe.

There is no operation sequence in the v1.8 architecture that produces a heartbeat gap >90s under normal operation, given the 60s sandbox cap and 90s cloud-call ceiling. The 30s margin is preserved.

**Side effect worth recording (not blocking):** The 60s cap is a meaningful constraint on what generated code can do in the sandbox. Heavy computation, multi-step tool sequences inside the sandbox, or anything I/O-bound at the duration boundary will need to decompose into multiple sandbox tasks. This is consistent with Core Value 4 (build simple) and Core Value 5 (queue-mediated coordination). The constraint is documented and revisable in a later phase if it proves too tight.

---

## Patch 2 — §11 Aligned to §16

| Required | Delivered | Verdict |
|---|---|---|
| Align §11 prose with §16 table OR remove §11 rules in favor of §16 | §11 replaced with explicit deference to §16 | ✓ |
| Resolve the 5A/5B/5C ambiguity | All three rules accurately summarized matching §16 verbatim | ✓ |
| Address `needs_cloud_review` handling | Explicitly stated: does not safe-pass; falls through to Rule 12 → `needs_human_input` | ✓ (above ask) |
| Acceptance test update | Six new assertions covering every classifier label / risk_class combination, including `needs_cloud_review` via Rule 12 | ✓ |

The Architect went beyond the minimum: the new "canonicality rule" — *"If any prose summary conflicts with §16, §16 wins"* — is a structural fix that prevents this class of bug recurring as the document evolves. Worth keeping.

The explicit `needs_cloud_review` handling closes the one gap I noted in passing in §3.2 of the v1.8 review (where I observed it fell through to Rule 12 implicitly). It is now explicit.

---

## Core Value Compliance

No changes from v1.8 status. Both patches reinforce existing positions:

- **Core Value 1 (security baked in):** Sandbox duration cap is a defense-in-depth boundary; canonicality rule is a documentation-level invariant against drift.
- **Core Value 4 (build simple):** Patch 1 chose the simpler option (Job Object timeout) over the more complex one (heartbeat-during-sandbox via watchdog thread). Patch 2 chose the simpler option (canonical reference to one table) over the more complex one (maintaining synchronized prose and table descriptions).

No conflicts.