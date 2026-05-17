from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from axiom.core.manifest_binder import ManifestBinder
from axiom.persistence.repositories import (
    get_active_manifest_fingerprints,
    log_security_event,
)


class BootVerificationError(RuntimeError):
    pass


@dataclass(frozen=True)
class BootVerificationResult:
    verified_count: int
    manifest_ids: list[str]


ROOT = Path(__file__).resolve().parents[1]
POLICY_DIR = ROOT / "policy"

MANIFEST_SCHEMA = POLICY_DIR / "schemas" / "manifest_schema.json"
TOOL_MAP_SCHEMA = POLICY_DIR / "schemas" / "tool_capability_map_schema.json"
TOOL_MAP = POLICY_DIR / "security_artifacts" / "tool_capability_map.json"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()

    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)

    return h.hexdigest()


def resolve_registered_path(relative_path: str) -> Path:
    return ROOT / relative_path


def verify_boot_manifests() -> BootVerificationResult:
    rows = get_active_manifest_fingerprints()

    if not rows:
        _log_boot_failure("no_active_manifest_fingerprints", {"active_count": 0})
        raise BootVerificationError("No active manifest fingerprints registered")

    manifest_ids: list[str] = []

    try:
        # Validates the tool-capability map schema and semantic requirements first.
        ManifestBinder(MANIFEST_SCHEMA, TOOL_MAP_SCHEMA, TOOL_MAP)

        for row in rows:
            manifest_id = row["manifest_id"]
            manifest_type = row["manifest_type"]
            relative_path = row["relative_path"]
            expected_sha = row["sha256"]

            path = resolve_registered_path(relative_path)

            if not path.exists():
                _log_boot_failure(
                    "registered_manifest_file_missing",
                    {
                        "manifest_id": manifest_id,
                        "manifest_type": manifest_type,
                        "relative_path": relative_path,
                    },
                )
                raise BootVerificationError(f"Registered manifest file missing: {relative_path}")

            actual_sha = sha256_file(path)

            if actual_sha != expected_sha:
                _log_boot_failure(
                    "manifest_sha256_mismatch",
                    {
                        "manifest_id": manifest_id,
                        "manifest_type": manifest_type,
                        "relative_path": relative_path,
                        "expected_sha256": expected_sha,
                        "actual_sha256": actual_sha,
                    },
                )
                raise BootVerificationError(f"Manifest SHA256 mismatch: {manifest_id}")

            manifest_ids.append(manifest_id)

    except BootVerificationError:
        raise
    except Exception as exc:
        _log_boot_failure(
            "manifest_boot_validation_error",
            {"error": str(exc)},
        )
        raise BootVerificationError(str(exc)) from exc

    log_security_event(
        event_type="manifest_boot_verification_passed",
        severity="info",
        reason="all_active_manifest_fingerprints_valid",
        details={
            "verified_count": len(manifest_ids),
            "manifest_ids": manifest_ids,
        },
    )

    return BootVerificationResult(
        verified_count=len(manifest_ids),
        manifest_ids=manifest_ids,
    )


def _log_boot_failure(reason: str, details: dict) -> None:
    log_security_event(
        event_type="manifest_boot_verification_failed",
        severity="critical",
        reason=reason,
        details=details,
    )
