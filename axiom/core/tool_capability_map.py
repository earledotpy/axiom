from __future__ import annotations

from pathlib import Path
from typing import Any

from axiom.core.manifest_binder import ManifestBinder

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_SCHEMA = ROOT / "policy" / "schemas" / "manifest_schema.json"
TOOL_MAP_SCHEMA = ROOT / "policy" / "schemas" / "tool_capability_map_schema.json"
TOOL_MAP = ROOT / "policy" / "security_artifacts" / "tool_capability_map.json"


class ToolCapabilityMap:
    def __init__(self) -> None:
        binder = ManifestBinder(MANIFEST_SCHEMA, TOOL_MAP_SCHEMA, TOOL_MAP)
        self._map = binder.tool_capability_map

    @property
    def tools(self) -> dict[str, Any]:
        return self._map["tools"]

    def get(self, tool_id: str) -> dict[str, Any] | None:
        return self.tools.get(tool_id)

    def contains(self, tool_id: str) -> bool:
        return tool_id in self.tools


_TOOL_MAP: ToolCapabilityMap | None = None


def get_tool_capability_map() -> ToolCapabilityMap:
    global _TOOL_MAP
    if _TOOL_MAP is None:
        _TOOL_MAP = ToolCapabilityMap()
    return _TOOL_MAP


def get_tool_entry(tool_id: str) -> dict[str, Any] | None:
    return get_tool_capability_map().get(tool_id)


def get_all_tool_ids() -> set[str]:
    return set(get_tool_capability_map().tools.keys())
