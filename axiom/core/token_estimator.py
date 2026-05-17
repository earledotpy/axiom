from __future__ import annotations

import math

from axiom.persistence.repositories import record_resource_usage


class TokenLimitError(RuntimeError):
    pass


class TokenEstimator:
    """
    Conservative fallback estimator.

    Binding rule:
    - fallback estimators use 1.5x margin.
    """

    def __init__(self, fallback_margin: float = 1.5):
        if fallback_margin < 1.0:
            raise ValueError("fallback_margin must be >= 1.0")
        self.fallback_margin = fallback_margin

    def estimate_tokens(self, text: str) -> int:
        if not text:
            return 0

        raw_estimate = math.ceil(len(text) / 4)
        return math.ceil(raw_estimate * self.fallback_margin)

    def require_within_limit(self, text: str, max_tokens: int) -> int:
        estimated = self.estimate_tokens(text)

        if estimated > max_tokens:
            raise TokenLimitError(
                f"Estimated token count {estimated} exceeds limit {max_tokens}"
            )

        return estimated

    def record_estimated_input_tokens(
        self,
        task_id: int,
        text: str,
        limit_value: int | float | None = None,
    ) -> int:
        estimated = self.estimate_tokens(text)
        status = self._status_for_limit(estimated, limit_value)

        return record_resource_usage(
            task_id=task_id,
            resource_type="estimated_input_tokens",
            amount=estimated,
            limit_value=limit_value,
            status=status,
            details={
                "estimator": "fallback_chars_per_token",
                "fallback_margin": self.fallback_margin,
                "text_length": len(text),
            },
        )

    def record_estimated_output_tokens(
        self,
        task_id: int,
        text: str,
        limit_value: int | float | None = None,
    ) -> int:
        estimated = self.estimate_tokens(text)
        status = self._status_for_limit(estimated, limit_value)

        return record_resource_usage(
            task_id=task_id,
            resource_type="estimated_output_tokens",
            amount=estimated,
            limit_value=limit_value,
            status=status,
            details={
                "estimator": "fallback_chars_per_token",
                "fallback_margin": self.fallback_margin,
                "text_length": len(text),
            },
        )

    @staticmethod
    def _status_for_limit(amount: int | float, limit_value: int | float | None) -> str:
        if limit_value is None:
            return "unknown"

        if amount <= limit_value:
            return "within_limit"

        return "exceeded"
