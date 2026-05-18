from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from axiom.gateways.ollama_prereq import OllamaPrereqInspector
from axiom.persistence.db import get_connection


TOOL_VERSION = "register_model_fingerprint.v1"


class ModelFingerprintRegistrationError(RuntimeError):
    pass


def sha256_text(value: Any) -> str | None:
    if value is None:
        return None

    if not isinstance(value, str):
        value = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )

    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def stable_sha256_json(payload: dict[str, Any]) -> str:
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_profile_payload(
    result,
    calibration_run_id: str,
    profile_label: str,
) -> dict[str, Any]:
    raw_show = result.raw_show or {}
    details = raw_show.get("details") or {}

    return {
        "profile_label": profile_label,
        "ollama_host": result.host,
        "model_name": result.model,
        "ollama_model_tag": result.model,
        "ollama_model_digest": (
            raw_show.get("digest")
            or raw_show.get("model_info", {}).get("general.basename")
            or f"unavailable:{result.model}"
        ),
        "quantization": result.quantization_level,
        "parameter_size": details.get("parameter_size"),
        "model_family": details.get("family"),
        "model_format": details.get("format"),
        "thinking_mode": result.profile_thinking_mode,
        "runtime_thinking_enforcement": result.runtime_thinking_enforcement,
        "template": raw_show.get("template"),
        "system": raw_show.get("system"),
        "parameters": raw_show.get("parameters"),
        "details": details,
        "calibration_run_id": calibration_run_id,
    }


def ensure_classifier_calibration_run(
    calibration_run_id: str,
    model: str,
    host: str,
) -> None:
    """
    Require a real, pre-existing, passed calibration run before a model
    profile can be registered.

    This function must not create synthetic calibration rows.
    """
    if calibration_run_id == "pending_calibration":
        raise ModelFingerprintRegistrationError(
            "Calibration run is pending; refusing trusted model registration."
        )

    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT calibration_run_id, model_name, ollama_host, passed
            FROM classifier_calibration_runs
            WHERE calibration_run_id = ?
            """,
            (calibration_run_id,),
        ).fetchone()

    if row is None:
        raise ModelFingerprintRegistrationError(
            f"Calibration run not found: {calibration_run_id}"
        )

    if row["model_name"] != model:
        raise ModelFingerprintRegistrationError(
            "Calibration run model mismatch: "
            f"expected {model}, got {row['model_name']}"
        )

    if row["ollama_host"] != host:
        raise ModelFingerprintRegistrationError(
            "Calibration run host mismatch: "
            f"expected {host}, got {row['ollama_host']}"
        )

    if int(row["passed"]) != 1:
        raise ModelFingerprintRegistrationError(
            f"Calibration run has not passed: {calibration_run_id}"
        )


def resolve_registration_state(
    profile_thinking_mode: str,
    requested_registration_status: str,
) -> tuple[int, str]:
    """
    Resolve model-profile registration state without silently promoting
    candidate profiles.

    Rules:
    - thinking_mode='unknown' can only be candidate/non-current.
    - requested candidate remains candidate/non-current.
    - requested current requires thinking_mode='disabled'.
    - superseded/rejected are always non-current.
    """
    if requested_registration_status == "candidate":
        return 0, "candidate"

    if requested_registration_status in {"superseded", "rejected"}:
        return 0, requested_registration_status

    if requested_registration_status == "current":
        if profile_thinking_mode != "disabled":
            return 0, "candidate"
        return 1, "current"

    return 0, "candidate"


def register_model_fingerprint(
    host: str = "http://localhost:11434",
    model: str = "qwen3:4b",
    profile_label: str = "default",
    calibration_run_id: str = "pending_calibration",
    timeout_seconds: int = 5,
    registration_status: str = "candidate",
) -> int:
    result = OllamaPrereqInspector(
        host=host,
        model=model,
        timeout_seconds=timeout_seconds,
    ).inspect()

    if not result.reachable:
        raise ModelFingerprintRegistrationError("Ollama host is not reachable")

    if not result.model_present:
        raise ModelFingerprintRegistrationError(f"Ollama model is not present: {model}")

    if not result.show_available:
        raise ModelFingerprintRegistrationError(
            f"Ollama /api/show unavailable for model: {model}"
        )

    if not result.details_present:
        raise ModelFingerprintRegistrationError("/api/show details missing")

    if not result.quantization_level:
        raise ModelFingerprintRegistrationError(
            "/api/show details.quantization_level missing"
        )

    if result.runtime_thinking_enforcement not in {"profile_verified", "gateway_required"}:
        raise ModelFingerprintRegistrationError(
            f"Invalid runtime thinking enforcement: {result.runtime_thinking_enforcement}"
        )

    if registration_status not in {"candidate", "current", "superseded", "rejected"}:
        raise ModelFingerprintRegistrationError(
            f"Invalid registration_status: {registration_status}"
        )

    raw_show = result.raw_show or {}
    details = raw_show.get("details") or {}

    profile_payload = build_profile_payload(
        result=result,
        calibration_run_id=calibration_run_id,
        profile_label=profile_label,
    )
    selected_profile_sha256 = stable_sha256_json(profile_payload)

    template_sha256 = sha256_text(raw_show.get("template"))
    system_sha256 = sha256_text(raw_show.get("system"))
    parameters_sha256 = sha256_text(raw_show.get("parameters"))
    details_sha256 = sha256_text(details)

    ollama_model_digest = (
        raw_show.get("digest")
        or raw_show.get("model_info", {}).get("general.basename")
        or f"unavailable:{model}"
    )

    requested_current, effective_registration_status = resolve_registration_state(
        profile_thinking_mode=result.profile_thinking_mode,
        requested_registration_status=registration_status,
    )

    thinking_mode_rule_version = (
        "gateway_required_v1"
        if result.runtime_thinking_enforcement == "gateway_required"
        else "profile_verified_v1"
    )

    notes = json.dumps(
        {
            "runtime_thinking_enforcement": result.runtime_thinking_enforcement,
            "profile_thinking_mode": result.profile_thinking_mode,
            "fingerprint_registration_ready": result.fingerprint_registration_ready,
            "raw_show_digest_available": raw_show.get("digest") is not None,
            "registration_note": (
                "Profiles with thinking_mode='unknown' are recorded as "
                "candidate/non-current due to canonical schema constraints."
            ),
        },
        sort_keys=True,
        ensure_ascii=False,
    )

    ensure_classifier_calibration_run(
        calibration_run_id=calibration_run_id,
        model=model,
        host=host,
    )

    with get_connection() as conn:
        existing = conn.execute(
            """
            SELECT profile_id
            FROM model_profile_fingerprints
            WHERE selected_profile_sha256 = ?
            """,
            (selected_profile_sha256,),
        ).fetchone()

        if existing is not None:
            return int(existing["profile_id"])

        if requested_current == 1:
            conn.execute(
                """
                UPDATE model_profile_fingerprints
                SET is_current = 0,
                    registration_status = 'superseded'
                WHERE profile_label = ?
                  AND is_current = 1
                """,
                (profile_label,),
            )

        cur = conn.execute(
            """
            INSERT INTO model_profile_fingerprints
            (profile_label, model_name, ollama_host, ollama_model_tag,
             ollama_model_digest, quantization, parameter_size, model_family,
             model_format, thinking_mode, thinking_mode_rule_version,
             template_sha256, system_sha256, parameters_sha256, details_sha256,
             selected_profile_sha256, calibration_run_id, is_current,
             registration_status, registered_by_tool_version, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                profile_label,
                model,
                host,
                model,
                ollama_model_digest,
                result.quantization_level,
                details.get("parameter_size"),
                details.get("family"),
                details.get("format"),
                result.profile_thinking_mode,
                thinking_mode_rule_version,
                template_sha256,
                system_sha256,
                parameters_sha256,
                details_sha256,
                selected_profile_sha256,
                calibration_run_id,
                requested_current,
                effective_registration_status,
                TOOL_VERSION,
                notes,
            ),
        )

        return int(cur.lastrowid)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Register AXIOM local Ollama model fingerprint."
    )
    parser.add_argument("--host", default="http://localhost:11434")
    parser.add_argument("--model", default="qwen3:4b")
    parser.add_argument("--profile-label", default="default")
    parser.add_argument("--calibration-run-id", default="pending_calibration")
    parser.add_argument("--registration-status", default="candidate")
    parser.add_argument("--timeout", type=int, default=5)
    args = parser.parse_args()

    try:
        profile_id = register_model_fingerprint(
            host=args.host,
            model=args.model,
            profile_label=args.profile_label,
            calibration_run_id=args.calibration_run_id,
            registration_status=args.registration_status,
            timeout_seconds=args.timeout,
        )
    except ModelFingerprintRegistrationError as exc:
        print(f"registration failed: {exc}", file=sys.stderr)
        return 1

    print(f"registered model profile fingerprint {profile_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())