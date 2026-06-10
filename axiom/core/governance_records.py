from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RECORD_ROOT = ROOT / "governance" / "80_records"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def id_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def slug(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "-", value.strip().upper()).strip("-")
    return cleaned[:32] or "AXIOM"


def unique(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        value = item.strip() if isinstance(item, str) else ""
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def record_dir(record_root: Path, directory: str) -> Path:
    return Path(record_root) / directory


def write_record(record_root: Path, directory: str, filename: str, payload: dict[str, Any]) -> Path:
    target = record_dir(record_root, directory)
    target.mkdir(parents=True, exist_ok=True)
    path = target / filename
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def read_record(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"governance record root is not an object: {path}")
    return payload


def list_records(record_root: Path, directory: str) -> list[tuple[Path, dict[str, Any]]]:
    target = record_dir(record_root, directory)
    if not target.exists():
        return []
    records: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted(target.glob("*.json")):
        records.append((path, read_record(path)))
    return records


def load_record_by_id(record_root: Path, directory: str, record_id: str) -> dict[str, Any]:
    path = record_dir(record_root, directory) / f"{record_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"governance record not found: {record_id}")
    return read_record(path)


def find_record_by_id(record_root: Path, directory: str, id_field: str, record_id: str) -> dict[str, Any] | None:
    for _, payload in list_records(record_root, directory):
        if payload.get(id_field) == record_id:
            return payload
    return None


def source_ref(record_id: str, directory: str, *, path: str = "", authority_status: str = "") -> dict[str, Any]:
    return {
        "source_id": record_id,
        "source_path": path or f"governance/80_records/{directory}/{record_id}.json",
        "source_type": directory,
        "authority_status": authority_status,
    }
