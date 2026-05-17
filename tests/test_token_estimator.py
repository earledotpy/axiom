import pytest

from axiom.core.token_estimator import TokenEstimator, TokenLimitError


def test_token_estimator_returns_zero_for_empty_text():
    assert TokenEstimator().estimate_tokens("") == 0


def test_token_estimator_applies_fallback_margin():
    estimator = TokenEstimator(fallback_margin=1.5)

    assert estimator.estimate_tokens("a" * 100) == 38


def test_token_estimator_rejects_margin_below_one():
    with pytest.raises(ValueError):
        TokenEstimator(fallback_margin=0.5)


def test_token_estimator_require_within_limit_returns_estimate():
    estimate = TokenEstimator().require_within_limit("a" * 100, max_tokens=100)

    assert estimate == 38


def test_token_estimator_require_within_limit_raises_when_exceeded():
    with pytest.raises(TokenLimitError):
        TokenEstimator().require_within_limit("a" * 1000, max_tokens=10)