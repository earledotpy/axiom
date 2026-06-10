from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from axiom.core.autonomous_gate import evaluate_autonomous_readiness
from axiom.core.boot_verifier import BootVerificationError, verify_boot_manifests
from axiom.core.tool_capability_map import get_all_tool_ids
from axiom.persistence.db import get_connection


@dataclass(frozen=True)
class BootstrapCheck:
    name: str
    passed: bool
    reason: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BootstrapValidationResult:
    passed: bool
    checks: list[BootstrapCheck]
    autonomous_readiness: dict[str, Any] = field(default_factory=dict)
    operational_mode: str = "unknown"

    @property
    def failures(self) -> list[BootstrapCheck]:
        return [check for check in self.checks if not check.passed]

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "checks": [check.to_dict() for check in self.checks],
            "autonomous_readiness": self.autonomous_readiness,
            "operational_mode": self.operational_mode,
        }


class BootstrapValidationError(RuntimeError):
    pass


class BootstrapValidator:
    """
    Passive bootstrap validator.

    This class checks whether the AXIOM foundation is safe to boot.
    It does not start agents, scheduler loops, Telegram, model calls, or tools.
    """

    REQUIRED_SCHEMA_VERSION = "v1.11.4"
    REQUIRED_TOOL_MAP_MANIFEST_ID = "security.tool_capability_map.v1"
    REQUIRED_MEMORY_VEC_TABLE = "memory_item_embeddings"

    def run(self, raise_on_failure: bool = False) -> BootstrapValidationResult:
        checks = [
            self.check_sqlite_pragmas(),
            self.check_schema_version(),
            self.check_sqlite_vec_table(),
            self.check_tool_capability_map(),
            self.check_manifest_fingerprints(),
        ]

        foundation_passed = all(check.passed for check in checks)
        readiness = evaluate_autonomous_readiness(profile_label="default")

        if not foundation_passed:
            operational_mode = "foundation_failed"
        elif readiness.allowed:
            operational_mode = "autonomous_available"
        else:
            operational_mode = "fail_closed_non_autonomous"

        result = BootstrapValidationResult(
            passed=foundation_passed,
            checks=checks,
            autonomous_readiness=readiness.to_dict(),
            operational_mode=operational_mode,
        )

        if raise_on_failure:
            if not result.passed:
                reasons = "; ".join(
                    f"{failure.name}: {failure.reason}" for failure in result.failures
                )
                raise BootstrapValidationError(reasons)
            if not readiness.allowed:
                reasons = ", ".join(readiness.blocking_reasons) or "unknown"
                raise BootstrapValidationError(f"autonomous_readiness_not_allowed: {reasons}")

        return result

    def check_sqlite_pragmas(self) -> BootstrapCheck:
        with get_connection() as conn:
            journal_mode = conn.execute("PRAGMA journal_mode;").fetchone()[0]
            synchronous = conn.execute("PRAGMA synchronous;").fetchone()[0]
            busy_timeout = conn.execute("PRAGMA busy_timeout;").fetchone()[0]
            foreign_keys = conn.execute("PRAGMA foreign_keys;").fetchone()[0]
            cache_size = conn.execute("PRAGMA cache_size;").fetchone()[0]

        details = {
            "journal_mode": journal_mode,
            "synchronous": synchronous,
            "busy_timeout": busy_timeout,
            "foreign_keys": foreign_keys,
            "cache_size": cache_size,
        }

        if str(journal_mode).lower() != "wal":
            return BootstrapCheck("sqlite_pragmas", False, "journal_mode_not_wal", details)

        if int(synchronous) != 2:
            return BootstrapCheck("sqlite_pragmas", False, "synchronous_not_full", details)

        if int(busy_timeout) < 5000:
            return BootstrapCheck("sqlite_pragmas", False, "busy_timeout_below_5000", details)

        if int(foreign_keys) != 1:
            return BootstrapCheck("sqlite_pragmas", False, "foreign_keys_disabled", details)

        if int(cache_size) >= 0:
            return BootstrapCheck(
                "sqlite_pragmas",
                False,
                "cache_size_not_bounded_negative_pages",
                details,
            )

        return BootstrapCheck("sqlite_pragmas", True, "sqlite_pragmas_valid", details)

    def check_schema_version(self) -> BootstrapCheck:
        with get_connection() as conn:
            rows = conn.execute("SELECT schema_version FROM schema_migrations").fetchall()

        versions = {row["schema_version"] for row in rows}
        details = {"schema_versions": sorted(versions)}

        if versions != {self.REQUIRED_SCHEMA_VERSION}:
            return BootstrapCheck("schema_version", False, "schema_version_mismatch", details)

        return BootstrapCheck("schema_version", True, "schema_version_valid", details)

    def check_sqlite_vec_table(self) -> BootstrapCheck:
        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE name = ?
                """,
                (self.REQUIRED_MEMORY_VEC_TABLE,),
            ).fetchone()

        if row is None:
            return BootstrapCheck(
                "sqlite_vec_table",
                False,
                "memory_vec_table_missing",
                {"required_table": self.REQUIRED_MEMORY_VEC_TABLE},
            )

        return BootstrapCheck(
            "sqlite_vec_table",
            True,
            "memory_vec_table_present",
            {"table": self.REQUIRED_MEMORY_VEC_TABLE},
        )

    def check_tool_capability_map(self) -> BootstrapCheck:
        try:
            tool_ids = sorted(get_all_tool_ids())
        except Exception as exc:
            return BootstrapCheck(
                "tool_capability_map",
                False,
                "tool_capability_map_load_failed",
                {"error": str(exc)},
            )

        if self.REQUIRED_TOOL_MAP_MANIFEST_ID is None:
            # Defensive no-op branch; keeps the check explicitly data-driven.
            pass

        if len(tool_ids) == 0:
            return BootstrapCheck(
                "tool_capability_map",
                False,
                "tool_capability_map_empty",
                {"tool_count": 0},
            )

        return BootstrapCheck(
            "tool_capability_map",
            True,
            "tool_capability_map_loaded",
            {
                "tool_count": len(tool_ids),
                "tool_ids": tool_ids,
            },
        )

    def check_manifest_fingerprints(self) -> BootstrapCheck:
        try:
            result = verify_boot_manifests()
        except BootVerificationError as exc:
            return BootstrapCheck(
                "manifest_fingerprints",
                False,
                "manifest_fingerprint_verification_failed",
                {"error": str(exc)},
            )

        if self.REQUIRED_TOOL_MAP_MANIFEST_ID not in result.manifest_ids:
            return BootstrapCheck(
                "manifest_fingerprints",
                False,
                "tool_capability_map_manifest_not_registered",
                {"manifest_ids": result.manifest_ids},
            )

        return BootstrapCheck(
            "manifest_fingerprints",
            True,
            "manifest_fingerprints_valid",
            {
                "verified_count": result.verified_count,
                "manifest_ids": result.manifest_ids,
            },
        )