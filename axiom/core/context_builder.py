from __future__ import annotations

import json
from typing import Any

from axiom.persistence.repositories import record_resource_usage


class ContextBundleTooLargeError(RuntimeError):
    pass


class ContextBuilder:
    """
    Builds serialized context bundles with a hard byte cap.

    Binding rule:
    - context bundles capped at 500 KB serialized size.
    """

    def __init__(self, max_bundle_kb: int = 500):
        if max_bundle_kb <= 0:
            raise ValueError("max_bundle_kb must be positive")
        self.max_bundle_bytes = max_bundle_kb * 1024
        self.max_bundle_kb = max_bundle_kb

    def build_bundle(self, payload: dict[str, Any]) -> dict[str, Any]:
        serialized = self.serialize(payload)
        size_bytes = len(serialized.encode("utf-8"))

        if size_bytes > self.max_bundle_bytes:
            raise ContextBundleTooLargeError(
                f"Context bundle is {size_bytes} bytes; limit is {self.max_bundle_bytes} bytes"
            )

        return {
            "payload": payload,
            "serialized": serialized,
            "size_bytes": size_bytes,
            "size_kb": size_bytes / 1024,
            "max_bundle_bytes": self.max_bundle_bytes,
            "max_bundle_kb": self.max_bundle_kb,
        }

    def record_bundle_size(
        self,
        task_id: int,
        payload: dict[str, Any],
    ) -> int:
        bundle = self.build_bundle(payload)

        return record_resource_usage(
            task_id=task_id,
            resource_type="context_bundle_kb",
            amount=bundle["size_kb"],
            limit_value=self.max_bundle_kb,
            status="within_limit",
            details={
                "size_bytes": bundle["size_bytes"],
                "max_bundle_bytes": bundle["max_bundle_bytes"],
            },
        )

    @staticmethod
    def serialize(payload: dict[str, Any]) -> str:
        return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))