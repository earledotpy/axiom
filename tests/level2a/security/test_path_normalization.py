import pytest

from axiom.security.level2a.pathing import (
    PathNormalizationError,
    enforce_allowed_not_blocked,
    normalize_control_path,
)


ANCHORS = {"$WORKSPACE_ROOT": "/axiom"}


def test_workspace_token_paths_are_normalized_and_case_folded():
    assert normalize_control_path("$WORKSPACE_ROOT/Governance/05_handoffs/", ANCHORS) == "/axiom/governance/05_handoffs"


def test_traversal_and_unanchored_absolute_paths_are_rejected():
    with pytest.raises(PathNormalizationError):
        normalize_control_path("$WORKSPACE_ROOT/governance/../ipc", ANCHORS)
    with pytest.raises(PathNormalizationError):
        normalize_control_path("C:/axiom/ipc", ANCHORS)


def test_t05_blocked_path_precedence_over_allowed_ancestor():
    path = normalize_control_path("$WORKSPACE_ROOT/governance/01_live_spine/file.md", ANCHORS)
    assert not enforce_allowed_not_blocked(
        path,
        allowed_paths=["/axiom/governance"],
        blocked_paths=["/axiom/governance/01_live_spine"],
    )


def test_allowed_path_passes_when_not_blocked():
    path = normalize_control_path("$WORKSPACE_ROOT/governance/05_handoffs/file.md", ANCHORS)
    assert enforce_allowed_not_blocked(
        path,
        allowed_paths=["/axiom/governance/05_handoffs"],
        blocked_paths=["/axiom/governance/01_live_spine"],
    )
