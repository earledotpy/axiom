# OQ-006: Codex Investigation - `fail_closed_coherent` False

**Reviewer**: Codex  
**Date**: 2026-05-28  
**Question ID**: OQ-006  
**Role Lens**: Implementation Specialist and Troubleshooter  
**Status**: Investigation complete; fix not applied in this artifact  

---

## Question

Why does `tools/verify_foundation.py` report:

- `foundation_passed: True`
- `operational_mode: fail_closed_non_autonomous`
- `autonomous_allowed: False`
- `fail_closed_coherent: False`
- `blocking_reasons: autonomous_operation_disabled`

and what is the correct fix?

---

## Short Answer

`fail_closed_coherent` is false because `tools/verify_foundation.py` still uses an older, narrower definition of coherent fail-closed posture. It only treats the state as coherent when autonomous readiness is blocked by both:

- `no_current_trusted_model_profile`
- `safe_pass_disabled`

The current live state is more advanced: the database has a current trusted model profile, safe-pass is enabled, and autonomous operation alone is disabled. Under AB-002 and the active operating context, that is a valid fail-closed, non-autonomous posture.

**The correct fix is to update the verifier's coherence predicate. Do not enable autonomous operation to make the flag pass.**

---

## Reproduction Evidence

Command run:

```powershell
.\venv\Scripts\python.exe tools\verify_foundation.py
```

Observed output:

```text
foundation_passed: True
operational_mode: fail_closed_non_autonomous
session_repair_completed: True
autonomous_allowed: False
fail_closed_coherent: False

blocking_reasons:
- autonomous_operation_disabled
```

Command run:

```powershell
.\venv\Scripts\python.exe tools\verify_foundation.py --json
```

Relevant JSON facts:

- `foundation_passed` is `true`
- `operational_mode` is `fail_closed_non_autonomous`
- `autonomous_allowed` is `false`
- `status.current_trusted_model_profile_present` is `true`
- `status.safe_pass_enabled` is `true`
- `status.autonomous_operation_enabled` is `false`
- `blocking_reasons` is exactly `["autonomous_operation_disabled"]`

This means the foundation is valid, model trust material is present, safe-pass is enabled, and the only remaining gate is the explicit non-autonomous setting.

---

## Root Cause

In `tools/verify_foundation.py`, the current coherence check is:

```python
fail_closed_coherent = (
    not readiness.allowed
    and "no_current_trusted_model_profile" in readiness.blocking_reasons
    and "safe_pass_disabled" in readiness.blocking_reasons
)
```

That predicate was appropriate for an earlier unpromoted-model state, where fail-closed readiness depended on missing trusted profile material and disabled safe-pass.

It is now stale because AXIOM can be coherently fail-closed for a different reason: autonomous operation is explicitly disabled while the rest of the foundation is valid.

---

## Safety Interpretation

The observed state is not evidence of accidental autonomy. It is the opposite:

- `autonomous_operation_enabled = false`
- `autonomous_available = false`
- `operational_mode = fail_closed_non_autonomous`
- `blocking_reasons = ["autonomous_operation_disabled"]`

This aligns with AB-002: AXIOM remains local-first, fail-closed, and non-autonomous unless Jeremy explicitly approves a future binding change.

The unsafe fix would be to flip `autonomous_operation_enabled` to true just to satisfy the verifier. That would weaken the runtime posture and contradict the open question.

---

## Recommended Fix

Update `tools/verify_foundation.py` so `fail_closed_coherent` means:

1. foundation checks passed,
2. autonomous readiness is not allowed,
3. bootstrap selected `fail_closed_non_autonomous`,
4. readiness blockers are recognized fail-closed gates, and
5. the current status does not contain a contradiction, such as safe-pass enabled with no current trusted model profile.

The recognized fail-closed blockers should include:

- `no_current_trusted_model_profile`
- `safe_pass_disabled`
- `autonomous_operation_disabled`

That allows both valid states:

- early fail-closed state: no trusted profile, safe-pass disabled, autonomous disabled;
- current governed state: trusted profile present, safe-pass enabled, autonomous disabled.

---

## Suggested Implementation Shape

Add a small helper in `tools/verify_foundation.py`, for example:

```python
EXPECTED_FAIL_CLOSED_BLOCKERS = {
    "no_current_trusted_model_profile",
    "safe_pass_disabled",
    "autonomous_operation_disabled",
}


def _is_fail_closed_coherent(
    *,
    foundation_passed: bool,
    operational_mode: str,
    readiness: AutonomousReadinessDecision,
) -> bool:
    blockers = set(readiness.blocking_reasons)
    status = readiness.status

    if not foundation_passed:
        return False

    if readiness.allowed:
        return False

    if operational_mode != "fail_closed_non_autonomous":
        return False

    if not blockers or blockers - EXPECTED_FAIL_CLOSED_BLOCKERS:
        return False

    if (
        not status.get("current_trusted_model_profile_present", False)
        and status.get("safe_pass_enabled", False)
    ):
        return False

    return True
```

Then replace the current hard-coded `fail_closed_coherent = (...)` predicate with a call to that helper.

---

## Recommended Regression Tests

Add focused tests for `tools.verify_foundation`:

1. Current governed state:
   - current trusted model profile present,
   - safe-pass enabled,
   - autonomous operation disabled,
   - expected `fail_closed_coherent is True`.

2. Early fail-closed state:
   - no current trusted model profile,
   - safe-pass disabled,
   - autonomous operation disabled,
   - expected `fail_closed_coherent is True`.

3. Unknown blocker state:
   - blocker outside the expected fail-closed set,
   - expected `fail_closed_coherent is False`.

4. Autonomous-ready state:
   - `readiness.allowed is True`,
   - expected `fail_closed_coherent is False`, because the system is not fail-closed.

---

## Verification Performed

Commands run:

```powershell
.\venv\Scripts\python.exe tools\verify_foundation.py
.\venv\Scripts\python.exe tools\verify_foundation.py --json
```

Files inspected:

- `governance/01_live_spine/AXIOM_Open_Questions.md`
- `governance/01_live_spine/AXIOM_Current_Context_Packet.md`
- `governance/01_live_spine/AXIOM_Active_Bindings.md`
- `governance/02_cli_surfaces/codex/AGENTS.governance.md`
- `tools/verify_foundation.py`
- `tools/repair_session_state.py`
- `axiom/app/status_report.py`
- `axiom/app/bootstrap_validation.py`
- `axiom/core/autonomous_gate.py`
- `tests/test_verify_foundation.py`
- `tests/test_autonomous_gate.py`
- `tests/test_status_report.py`

No executable code was changed during this investigation.

---

## Disposition

OQ-006 is ready for a narrow implementation slice if Jeremy authorizes the fix.

Recommended implementation scope:

- update `tools/verify_foundation.py`;
- add focused tests in `tests/test_verify_foundation.py`;
- run focused tests for `verify_foundation`, `status_report`, and `autonomous_gate`;
- rerun `.\venv\Scripts\python.exe tools\verify_foundation.py`;
- optionally run the standard audit commands before closing the question.
