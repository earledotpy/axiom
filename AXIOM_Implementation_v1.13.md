# AXIOM_Implementation_v1.13

## Status

Proposal stack consumed: v1.10 → v1.10.1 → v1.10.2 → v1.11.1 → v1.11.2 → v1.11.3 → v1.11.4 patched final addendum.

Implementation ruling: accepted as the complete v1.13 implementation artifact after applying the targeted v1.13 defect repairs to the v1.12 base.

This revision replaces the inferred v1.11 database schema and inferred v1.11 manifest structure. The operator must not run `init_db()` against the prior inferred schema under any circumstance.

## v1.13 Patch Integration

This file uses `AXIOM_Implementation_v1.12.md` as the base artifact and applies the targeted `AXIOM_Implementation_v1.13_Patched.md` repairs in place. The patch is not appended as a delta; it is integrated into the canonical sections below.

Applied repairs:

1. **Defect 1 — Manifest ID regex:** `$defs.manifest_id.pattern` is corrected to `^(role|operator)\.[a-z0-9_]+\.v[0-9]+$`.
2. **Defects 2 and 3 — PlanInjectionScanner contract:** `scan()` now accepts explicit `risk_class`, uses enums that exactly match database CHECK domains, and maps safe-pass-disabled, deterministic-block, and classifier-block outcomes to the canonical artifact/task status pairs.
3. **Defect 4 — Acceptance tests:** the MVP acceptance suite is updated to assert the v1.13 scanner contract, manifest ID regex behavior, enum completeness, and risk-class disposition pairs.
4. **Verification snippet:** Task 3 verification now checks the v1.13 scanner return contract and enum domains.

## Binding Corrections from v1.11

1. The database schema is now canonical. Use `axiom/persistence/schema.sql` from Appendix A.
2. The manifest JSON Schema is now canonical. Use `axiom/policy/schemas/manifest_schema.json` from Appendix B.
3. The tool-capability map is a registered security artifact. Use `axiom/policy/security_artifacts/tool_capability_map.json` from Appendix C.
4. `tools/register_manifests.py` registers role manifests, operator-control manifests, and the tool-capability map in one atomic transaction.
5. `tools/register_model_fingerprint.py` is required after calibration and before autonomous boot.
6. `ModelFingerprintGuard._infer_thinking_mode()` inspects only `parameters` and returns `disabled` only when `(?i)^\s*think\s+false\s*$` matches with `re.MULTILINE`; otherwise it returns `unknown`.
7. `ModelGateway` injects `think: false` into every local Ollama `/api/chat` and `/api/generate` request and rejects caller attempts to set `think: true`.
8. `PlanInjectionScanner.scan()` returns `scanner_result`, `risk_class`, `artifact_status`, `parent_task_status`, `reason`, and `details`.
9. `PolicyEngine`, `ManifestBinder`, and tool-capability lookups are stateless at runtime and use validators/capability maps cached at boot.
10. The first implementation task is reversible setup only. Database initialization happens only after the canonical `schema.sql` has been written to disk.

## Binding Constraints Applied

The implementation must preserve all twelve Qwen binding conditions:

1. Strict sequential execution. No concurrent agent subprocesses.
2. `qwen3:4b` remains Q4-or-lower quantized and memory-mapped via Ollama.
3. Context bundles capped at 500 KB serialized size.
4. Sandbox execution capped at 256 MB RAM and 60 seconds wall-clock.
5. sqlite-vec operations capped at 100 vectors per query/batch.
6. Brave Search API, or panel-approved free-tier equivalent, must be confirmed before web search is enabled.
7. Token estimation margins: 2.0× for calibrated tokenizers, 1.5× for fallback estimators.
8. PolicyEngine, ManifestBinder, and tool-capability lookups remain stateless and use boot-time-cached validators.
9. Runtime thread count limited to four: main supervisor, Telegram, Scheduler, BootstrapValidationWorker.
10. Classifier safe-pass disabled until calibration passes against panel-authored test sets.
11. Model fingerprint mismatch, manifest SHA256 mismatch, or operator-control cross-field mismatch fail closed.
12. SQLite page cache explicitly bounded.

## Overall Implementation Sequence

### Phase 1 — Foundational Runtime

1. Create directory structure, requirements, and database connection layer.
2. Write canonical `schema.sql`, then run `init_db()` only after the schema file exists.
3. Write manifest schema, tool-capability map, manifest registration CLI, and boot-time verifier.
4. Write model fingerprint registration CLI, fingerprint guard, and local ModelGateway thinking-mode enforcement.
5. Write repository methods for sessions, tasks, events, manifests, calibration, model profiles, and resource usage.

### Phase 2 — Core State Machine

6. Implement StateMachine, Scheduler, SupervisorMonitor, TaskCommitter, ContextBuilder, TokenEstimator.
7. Enforce one running task at a time.
8. Enforce `tasks.manifest_id` non-null before any transition to `running`.
9. Enforce heartbeat write ordering before and after blocking operations.

### Phase 3 — Policy and Security Layer

10. Implement ManifestBinder with JSON Schema validation, SHA256 verification, semantic validation, tool ID map validation, and effective-capability derivation.
11. Implement stateless PolicyEngine with seven-step tool authorization.
12. Implement PlanInjectionScanner deterministic checks, classifier-safe-pass path, fail-closed fingerprint handling, and explicit return contract.

### Phase 4 — Gateways

13. Implement ModelGateway cloud cascade after provider configuration is approved.
14. Implement MemoryGateway and sqlite-vec sparse index invariant.
15. Implement NetworkGateway only after Brave Search or a panel-approved free-tier alternative is confirmed.
16. Implement SandboxGateway only after Windows Job Object specifics are approved for Phase 4.

### Phase 5 — Agents

17. Implement GoalPlanner, TaskPlanner, ToolExecutor, and ResultVerifier as manifest-bound executors.
18. Keep local model in sanitizer/router/classifier lane only.
19. Send all cognitive planning/synthesis to cloud cascade.

### Phase 6 — Telegram Control Plane

20. Implement Telegram Gateway after operator whitelist mechanism is specified.
21. Implement CommandParser and OperatorControlInserter.
22. Enforce operator-control manifests and capability-token boundaries.

### Phase 7 — Acceptance

23. Run the canonical MVP acceptance suite listed below.
24. Run `tests/e2e/test_full_goal_flow_minimum.py` only after classifier calibration and model fingerprint registration are complete.

---

# First Three Executable Implementation Tasks

## Task 1 — Foundation: Directory Structure, Requirements, and DB Connection Layer

### Objective

Create the filesystem skeleton and reversible Python foundation. Do not initialize the database in this task.

### Files to create

```text
C:\axiom\
├── axiom\
│   ├── __init__.py
│   ├── app\__init__.py
│   ├── core\__init__.py
│   ├── agents\__init__.py
│   ├── gateways\__init__.py
│   ├── security\__init__.py
│   ├── persistence\__init__.py
│   └── policy\
│       ├── role_manifests\
│       ├── operator_control_manifests\
│       ├── security_artifacts\
│       └── schemas\
├── config\
├── logs\
├── tools\
├── tests\
│   ├── e2e\
│   └── __init__.py
└── requirements.txt
```

### Exact PowerShell commands

```powershell
New-Item -ItemType Directory -Force C:\axiom | Out-Null
Set-Location C:\axiom

$dirs = @(
  "axiom",
  "axiom\app",
  "axiom\core",
  "axiom\agents",
  "axiom\gateways",
  "axiom\security",
  "axiom\persistence",
  "axiom\policy\role_manifests",
  "axiom\policy\operator_control_manifests",
  "axiom\policy\security_artifacts",
  "axiom\policy\schemas",
  "config",
  "logs",
  "tools",
  "tests",
  "tests\e2e"
)

foreach ($d in $dirs) { New-Item -ItemType Directory -Force $d | Out-Null }

$initFiles = @(
  "axiom\__init__.py",
  "axiom\app\__init__.py",
  "axiom\core\__init__.py",
  "axiom\agents\__init__.py",
  "axiom\gateways\__init__.py",
  "axiom\security\__init__.py",
  "axiom\persistence\__init__.py",
  "tests\__init__.py"
)

foreach ($f in $initFiles) { New-Item -ItemType File -Force $f | Out-Null }
```

### Write `requirements.txt`

```text
python-telegram-bot>=20.0,<22.0
aiohttp>=3.9,<4.0
requests>=2.31,<3.0
PyYAML>=6.0,<7.0
jsonschema>=4.22,<5.0
pywin32>=306; platform_system == "Windows"
ollama>=0.3,<1.0
sqlite-vec>=0.1,<1.0
pytest>=8.0,<9.0
```

### Write `config/axiom.yaml`

```yaml
database:
  path: "C:\\axiom\\axiom.db"
  cache_size_kb: 32768

ollama:
  host: "http://localhost:11434"
  model: "qwen3:4b"
  fingerprint_timeout_seconds: 5

runtime:
  max_threads: 4
  sequential_execution: true

context:
  max_bundle_kb: 500

sandbox:
  max_ram_mb: 256
  max_wall_clock_seconds: 60
  network_access: "denied"

sqlite_vec:
  max_vector_batch: 100

scheduler:
  stale_threshold_seconds: 120
```

### Write `axiom/persistence/db.py`

```python
from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

DEFAULT_DB_PATH = r"C:\axiom\axiom.db"
DB_PATH = Path(os.environ.get("AXIOM_DB_PATH", DEFAULT_DB_PATH))
SCHEMA_PATH = Path(__file__).with_name("schema.sql")
SQLITE_CACHE_SIZE_KB = int(os.environ.get("AXIOM_SQLITE_CACHE_SIZE_KB", "32768"))


def apply_pragmas(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = FULL;")
    conn.execute("PRAGMA busy_timeout = 5000;")
    conn.execute(f"PRAGMA cache_size = -{SQLITE_CACHE_SIZE_KB};")


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), timeout=5.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    apply_pragmas(conn)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(
            f"Canonical schema file missing: {SCHEMA_PATH}. Do not initialize AXIOM without schema.sql."
        )

    sql = SCHEMA_PATH.read_text(encoding="utf-8")
    if "v1.11.4" not in sql:
        raise RuntimeError("Refusing to initialize database: schema.sql does not identify v1.11.4.")
    if "tool_capability_map" not in sql:
        raise RuntimeError("Refusing to initialize database: schema.sql lacks v1.11.4 tool_capability_map amendment.")

    with get_connection() as conn:
        conn.executescript(sql)
        mode = conn.execute("PRAGMA journal_mode;").fetchone()[0]
        if str(mode).lower() != "wal":
            raise RuntimeError(f"WAL mode not enabled; got {mode!r}")
```

### Exact commands to run

```powershell
Set-Location C:\axiom
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -c "from axiom.persistence.db import get_connection; c=get_connection(); conn=c.__enter__(); print(conn.execute('PRAGMA journal_mode;').fetchone()[0]); print(conn.execute('PRAGMA busy_timeout;').fetchone()[0]); c.__exit__(None,None,None)"
```

Expected output includes:

```text
wal
5000
```

### Do not run in Task 1

```powershell
python -c "from axiom.persistence.db import init_db; init_db()"
```

That command is intentionally deferred until Task 2, after `axiom/persistence/schema.sql` has been written.

### Acceptance criteria

- Directory structure exists.
- Virtual environment exists.
- Requirements install successfully.
- `axiom.persistence.db` imports successfully.
- `get_connection()` applies WAL, FULL synchronous, 5000 ms busy timeout, foreign keys, and bounded cache.
- `init_db()` refuses to run when `schema.sql` is missing.

### Ambiguity before proceeding

None. This task is reversible and does not commit database schema.

---

## Task 2 — Canonical Database Schema and First Initialization

### Objective

Write the canonical v1.11.4-amended `schema.sql`, then initialize the database. This task is the first non-reversible persistence step.

### File to write

`C:\axiom\axiom\persistence\schema.sql`

Use Appendix A exactly.

### Exact PowerShell command to write schema

Use a text editor, or use this command after copying Appendix A into `schema.sql`:

```powershell
notepad C:\axiom\axiom\persistence\schema.sql
```

### Exact command to initialize database

```powershell
Set-Location C:\axiom
.\venv\Scripts\Activate.ps1
python -c "from axiom.persistence.db import init_db; init_db(); print('AXIOM database initialized')"
```

### Exact verification commands

```powershell
sqlite3 C:\axiom\axiom.db "PRAGMA journal_mode;"
sqlite3 C:\axiom\axiom.db "SELECT schema_version FROM schema_migrations;"
sqlite3 C:\axiom\axiom.db "SELECT name FROM sqlite_master WHERE type IN ('table','index') ORDER BY name;"
sqlite3 C:\axiom\axiom.db "SELECT sql FROM sqlite_master WHERE name='manifest_fingerprints';"
```

Expected values:

```text
wal
v1.11.4
```

The `manifest_fingerprints` SQL must include:

```text
'tool_capability_map'
```

### Write `tests/test_sqlite_wal_mode.py`

```python
from axiom.persistence.db import get_connection, init_db


def test_sqlite_wal_mode_and_pragmas():
    init_db()
    with get_connection() as conn:
        assert conn.execute("PRAGMA journal_mode;").fetchone()[0].lower() == "wal"
        assert conn.execute("PRAGMA synchronous;").fetchone()[0] == 2
        assert conn.execute("PRAGMA busy_timeout;").fetchone()[0] >= 5000
        assert conn.execute("PRAGMA foreign_keys;").fetchone()[0] == 1
        assert conn.execute("PRAGMA cache_size;").fetchone()[0] < 0
```

### Write `tests/test_schema_v1114_amendments.py`

```python
from axiom.persistence.db import get_connection, init_db


def test_schema_version_is_v1114():
    init_db()
    with get_connection() as conn:
        rows = conn.execute("SELECT schema_version FROM schema_migrations").fetchall()
        assert {row["schema_version"] for row in rows} == {"v1.11.4"}


def test_manifest_fingerprints_accepts_tool_capability_map_type():
    init_db()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO manifest_fingerprints
            (manifest_id, manifest_type, relative_path, sha256, schema_version,
             manifest_version, role_name, command_name, approved_by_panel_version,
             active, registered_by_tool_version)
            VALUES (?, ?, ?, ?, ?, ?, NULL, NULL, ?, 1, ?)
            """,
            (
                "security.tool_capability_map.v1",
                "tool_capability_map",
                "policy/security_artifacts/tool_capability_map.json",
                "0" * 64,
                "axiom.tool_capability_map.v1",
                "1.0.0",
                "v1.11.4",
                "test",
            ),
        )


def test_provider_enum_rejects_unknown_provider():
    init_db()
    with get_connection() as conn:
        session_id = conn.execute("INSERT INTO sessions DEFAULT VALUES").lastrowid
        try:
            conn.execute(
                "INSERT INTO provider_usage (session_id, provider, status) VALUES (?, ?, ?)",
                (session_id, "paid_unknown_provider", "started"),
            )
        except Exception as exc:
            assert "CHECK" in str(exc).upper() or "constraint" in str(exc).lower()
        else:
            raise AssertionError("unknown provider was accepted")
```

### Exact test command

```powershell
pytest tests\test_sqlite_wal_mode.py tests\test_schema_v1114_amendments.py -v
```

### Acceptance criteria

- `init_db()` succeeds only after canonical `schema.sql` exists.
- WAL mode is active.
- `schema_migrations` contains `v1.11.4`.
- `manifest_fingerprints` accepts `tool_capability_map` rows.
- `provider_usage.provider` rejects unknown providers.
- `idx_scheduler_heartbeat_latest` exists.
- `idx_tasks_commit_batch` exists.
- `memory_item_embeddings` exists as a `vec0` virtual table.

### Ambiguity before proceeding

None. The schema is now panel-approved by the supplied proposal stack.

---

## Task 3 — Manifest Schema, Tool-Capability Map, and Manifest Registration CLI

### Objective

Create the manifest schema, tool-capability-map security artifact, semantic validators, and setup-only manifest registration CLI. This task does not create role/operator manifest instances beyond the tool-capability map; those come after role-specific manifest content is authored.

### Files to write

```text
C:\axiom\axiom\policy\schemas\manifest_schema.json
C:\axiom\axiom\policy\schemas\tool_capability_map_schema.json
C:\axiom\axiom\policy\security_artifacts\tool_capability_map.json
C:\axiom\axiom\core\manifest_binder.py
C:\axiom\axiom\core\tool_capability_map.py
C:\axiom\axiom\security\audit.py
C:\axiom\axiom\persistence\repositories.py
C:\axiom\tools\register_manifests.py
```

### Write `axiom/policy/schemas/manifest_schema.json`

Use Appendix B exactly.

### Write `axiom/policy/security_artifacts/tool_capability_map.json`

Use Appendix C exactly.

### Write `axiom/core/manifest_binder.py`

```python
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


class ManifestValidationError(RuntimeError):
    pass


SESSION_CONTROLLER_TOOL_COMMANDS = {
    "session_controller.status": "status",
    "session_controller.cancel_current_chain": "cancel_current_chain",
    "session_controller.pause_after_current": "pause_after_current",
    "session_controller.resume": "resume",
    "session_controller.shutdown_after_current": "shutdown_after_current",
    "session_controller.run_classifier_validation": "run_classifier_validation",
    "session_controller.enable_autonomous": "enable_autonomous",
    "session_controller.reconcile_provider_usage": "reconcile_provider_usage",
}


class ManifestBinder:
    def __init__(self, manifest_schema_path: Path, tool_map_schema_path: Path, tool_map_path: Path):
        self.manifest_schema_path = Path(manifest_schema_path)
        self.tool_map_schema_path = Path(tool_map_schema_path)
        self.tool_map_path = Path(tool_map_path)
        self.manifest_validator = Draft202012Validator(self._load_json(self.manifest_schema_path))
        self.tool_map_validator = Draft202012Validator(self._load_json(self.tool_map_schema_path))
        self.tool_capability_map = self.load_and_validate_tool_capability_map()
        self.tool_ids = set(self.tool_capability_map["tools"].keys())

    @staticmethod
    def _load_json(path: Path) -> dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))

    def load_and_validate_tool_capability_map(self) -> dict[str, Any]:
        tool_map = self._load_json(self.tool_map_path)
        self.tool_map_validator.validate(tool_map)
        self.validate_tool_capability_map_semantics(tool_map)
        return tool_map

    def validate_manifest(self, manifest: dict[str, Any]) -> None:
        self.manifest_validator.validate(manifest)
        self.validate_operator_control_binding(manifest)
        self.validate_tool_ids(manifest)

    def validate_tool_ids(self, manifest: dict[str, Any]) -> None:
        for field_name in ("allowed_tools", "forbidden_tools"):
            for tool_id in manifest.get(field_name, []):
                if tool_id not in self.tool_ids:
                    raise ManifestValidationError(f"{tool_id} is not in loaded tool_capability_map")

    @staticmethod
    def validate_operator_control_binding(manifest: dict[str, Any]) -> None:
        manifest_type = manifest["manifest_type"]
        allowed_commands = manifest["allowed_capabilities"]["operator_control"]["allowed_commands"]

        if manifest_type == "role":
            if allowed_commands != []:
                raise ManifestValidationError("Role manifests may not declare operator-control commands")
            return

        if manifest_type == "operator_control":
            command_name = manifest["operator_command"]["command_name"]
            if allowed_commands != [command_name]:
                raise ManifestValidationError(
                    "Operator-control manifest allowed_commands must equal [operator_command.command_name]"
                )
            return

        raise ManifestValidationError(f"Unknown manifest_type: {manifest_type}")

    @staticmethod
    def validate_tool_capability_map_semantics(tool_map: dict[str, Any]) -> None:
        tools = tool_map["tools"]
        for tool_id, expected_command in SESSION_CONTROLLER_TOOL_COMMANDS.items():
            entry = tools[tool_id]
            if entry["source"] != "allowed_capabilities.operator_control.allowed_commands":
                raise ManifestValidationError(f"{tool_id} must use operator_control allowed_commands source")
            if entry["required_command"] != expected_command:
                raise ManifestValidationError(f"{tool_id} required_command must be {expected_command}")
            if entry["requires_manifest_type"] != "operator_control":
                raise ManifestValidationError(f"{tool_id} must require operator_control manifest type")
```

### Write `axiom/core/tool_capability_map.py`

```python
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
```

### Write `tools/register_manifests.py`

```python
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from axiom.core.manifest_binder import ManifestBinder
from axiom.persistence.db import get_connection, init_db

TOOL_VERSION = "register_manifests.v1.12"
POLICY_DIR = ROOT / "axiom" / "policy"
MANIFEST_SCHEMA = POLICY_DIR / "schemas" / "manifest_schema.json"
TOOL_MAP_SCHEMA = POLICY_DIR / "schemas" / "tool_capability_map_schema.json"
TOOL_MAP = POLICY_DIR / "security_artifacts" / "tool_capability_map.json"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def row_for_tool_map() -> dict[str, Any]:
    return {
        "manifest_id": "security.tool_capability_map.v1",
        "manifest_type": "tool_capability_map",
        "relative_path": "policy/security_artifacts/tool_capability_map.json",
        "sha256": sha256_file(TOOL_MAP),
        "schema_version": "axiom.tool_capability_map.v1",
        "manifest_version": "1.0.0",
        "role_name": None,
        "command_name": None,
        "approved_by_panel_version": "v1.11.4",
        "registered_by_tool_version": TOOL_VERSION,
    }


def row_for_manifest(path: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    manifest_type = manifest["manifest_type"]
    if manifest_type == "role":
        rel = f"policy/role_manifests/{path.name}"
        role_name = manifest["role"]["role_name"]
        command_name = None
    elif manifest_type == "operator_control":
        rel = f"policy/operator_control_manifests/{path.name}"
        role_name = None
        command_name = manifest["operator_command"]["command_name"]
    else:
        raise RuntimeError(f"Unsupported manifest_type: {manifest_type}")

    return {
        "manifest_id": manifest["manifest_id"],
        "manifest_type": manifest_type,
        "relative_path": rel,
        "sha256": sha256_file(path),
        "schema_version": manifest["schema_version"],
        "manifest_version": manifest["manifest_version"],
        "role_name": role_name,
        "command_name": command_name,
        "approved_by_panel_version": manifest["approved_by_panel_version"],
        "registered_by_tool_version": TOOL_VERSION,
    }


def build_registration_rows() -> list[dict[str, Any]]:
    binder = ManifestBinder(MANIFEST_SCHEMA, TOOL_MAP_SCHEMA, TOOL_MAP)
    rows = [row_for_tool_map()]

    for subdir in ("role_manifests", "operator_control_manifests"):
        for path in sorted((POLICY_DIR / subdir).glob("*.json")):
            manifest = load_json(path)
            binder.validate_manifest(manifest)
            rows.append(row_for_manifest(path, manifest))

    return rows


def register() -> None:
    init_db()
    rows = build_registration_rows()
    with get_connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        conn.execute("UPDATE manifest_fingerprints SET active = 0")
        for row in rows:
            conn.execute(
                """
                INSERT OR REPLACE INTO manifest_fingerprints
                (manifest_id, manifest_type, relative_path, sha256, schema_version,
                 manifest_version, role_name, command_name, approved_by_panel_version,
                 active, registered_by_tool_version)
                VALUES
                (:manifest_id, :manifest_type, :relative_path, :sha256, :schema_version,
                 :manifest_version, :role_name, :command_name, :approved_by_panel_version,
                 1, :registered_by_tool_version)
                """,
                row,
            )
    print(f"registered {len(rows)} active security artifacts")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.parse_args()
    register()
```

### Exact commands to run

```powershell
Set-Location C:\axiom
.\venv\Scripts\Activate.ps1
notepad C:\axiom\axiom\policy\schemas\manifest_schema.json
notepad C:\axiom\axiom\policy\schemas\tool_capability_map_schema.json
notepad C:\axiom\axiom\policy\security_artifacts\tool_capability_map.json
python tools\register_manifests.py
sqlite3 C:\axiom\axiom.db "SELECT manifest_id, manifest_type, relative_path FROM manifest_fingerprints WHERE active = 1;"
```

Expected row:

```text
security.tool_capability_map.v1|tool_capability_map|policy/security_artifacts/tool_capability_map.json
```

### Acceptance criteria

- Manifest schema rejects `allowed_capabilities.network`, `allowed_capabilities.sandbox`, and `allowed_capabilities.memory`.
- Tool-capability map validates against its own schema.
- `register_manifests.py` validates the tool-capability map first.
- Registration is atomic: one invalid artifact changes no active fingerprint rows.
- Tool-capability map is registered as `manifest_type = 'tool_capability_map'`.
- Boot-time verifier checks role manifests, operator-control manifests, and tool-capability map.
- Any SHA256 mismatch, schema failure, semantic validation failure, missing registration, or unregistered file fails closed.

### Ambiguity before proceeding

No panel ambiguity for the security-artifact mechanism itself. Role-specific manifest contents beyond the tool-capability map still require concrete role manifest files before role execution can proceed.

---

# Required Later Implementation Items

## Model Fingerprint Registration CLI

File: `tools/register_model_fingerprint.py`

Required command:

```powershell
python tools\register_model_fingerprint.py `
  --profile-label default `
  --calibration-run-id injection_classifier_v1_2026_05_03 `
  --approved-by-panel-version v1.11.4
```

Required sequence:

1. Schema initialized.
2. Manifests registered.
3. Classifier calibration run completed manually.
4. Passing `classifier_calibration_runs` row exists.
5. `tools/register_model_fingerprint.py` queries Ollama `/api/show`.
6. Quantization extracted from `details.quantization_level`, never hardcoded.
7. Thinking mode inferred only from `parameters`.
8. `thinking_mode = unknown` rejects registration.
9. Previous current profile superseded and new current profile inserted in one transaction.
10. `security_events.event_type = 'model_fingerprint_registered'` written.

Core implementation rule:

```python
def _infer_thinking_mode(self, data: dict) -> str:
    import re
    params = str(data.get("parameters", ""))
    if re.search(r"(?i)^\s*think\s+false\s*$", params, re.MULTILINE):
        return "disabled"
    return "unknown"
```

## ModelGateway Local Ollama Enforcement

File: `axiom/gateways/model_gateway.py`

```python
class PolicyDeniedError(RuntimeError):
    pass


def prepare_local_ollama_payload(payload: dict) -> dict:
    if payload.get("think") is True:
        raise PolicyDeniedError("Caller may not override local Ollama thinking mode")
    prepared = dict(payload)
    prepared["think"] = False
    return prepared
```

Apply this to every local `/api/chat` and `/api/generate` request.

## PlanInjectionScanner Return Contract — v1.13 Defects 2 and 3 Repair

Source: v1.11.1 Section 1.3 as amended by v1.10.2 Section 1, with v1.13 repairs applied.

Repair summary:

- `scan()` accepts an explicit `risk_class` parameter.
- `ArtifactStatus` values exactly equal the `plan_artifacts.artifact_status` CHECK domain.
- `ParentTaskStatus` values exactly equal the `tasks.status` CHECK domain. `BLOCKED` is not a valid member.
- Safe-pass-disabled, deterministic-block, and classifier-block branches dispatch by `risk_class` with canonical disposition pairs.

File: `axiom/security/plan_injection_scanner.py`

```python
from enum import Enum
from typing import Dict, Any, Optional


class ScannerResult(str, Enum):
    NOT_SCANNED = "not_scanned"
    PASSED = "passed"
    DETERMINISTIC_BLOCK = "deterministic_block"
    CLASSIFIER_BLOCK = "classifier_block"
    FINGERPRINT_MISMATCH = "fingerprint_mismatch"
    VERIFICATION_TIMEOUT = "verification_timeout"
    CONNECTION_ERROR = "connection_error"
    MALFORMED_RESPONSE = "malformed_response"
    SCHEMA_CHANGE = "schema_change"
    MODEL_UNAVAILABLE = "model_unavailable"
    SAFE_PASS_DISABLED = "safe_pass_disabled"


class RiskClass(str, Enum):
    ORDINARY = "ordinary"
    HIGH_RISK = "high_risk"


class ArtifactStatus(str, Enum):
    """
    Defect 3 repair: Must equal plan_artifacts.artifact_status CHECK domain exactly.
    """
    DRAFT = "draft"
    SCANNER_PASSED = "scanner_passed"
    CHECKPOINT_PASSED = "checkpoint_passed"
    CHECKPOINT_FAILED = "checkpoint_failed"
    CHECKPOINT_BLOCKED = "checkpoint_blocked"
    QUARANTINED = "quarantined"
    COMMITTED = "committed"


class ParentTaskStatus(str, Enum):
    """
    Defect 3 repair: Must equal tasks.status CHECK domain exactly.
    BLOCKED removed. completed, failed, quarantined, blocked_resource_limit, cancelled added.
    """
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    QUARANTINED = "quarantined"
    NEEDS_HUMAN_INPUT = "needs_human_input"
    BLOCKED_RESOURCE_LIMIT = "blocked_resource_limit"
    CANCELLED = "cancelled"


class PlanInjectionScanner:
    """
    v1.11.1 Section 1.3 return contract with v1.10.2 two-tier lifecycle table.
    Defect 2 repair: scan() accepts explicit risk_class; dispatches by risk_class.
    """

    def __init__(self, safe_pass_enabled: bool = False):
        self.safe_pass_enabled = safe_pass_enabled

    def scan(
        self,
        artifact_json: Dict[str, Any],
        risk_class: str = "ordinary",
        parent_task_status: str = "running",
    ) -> Dict[str, Any]:
        """
        Returns a structured scanner result per the v1.11.1 Section 1.3 contract,
        with v1.10.2 two-tier lifecycle disposition.

        Defect 2: risk_class is now an explicit input parameter. The scanner does not
        decide the risk class; it receives it from upstream (e.g., artifact creation
        or prior heuristic) and maps it to the canonical disposition pair.

        Defect 2: All block branches (safe_pass_disabled, deterministic_block,
        classifier_block) now dispatch by risk_class.
        """
        # --- Safe-pass disabled branch (v1.10.2 §1 lifecycle table) ---
        if not self.safe_pass_enabled:
            if risk_class == RiskClass.HIGH_RISK:
                return {
                    "scanner_result": ScannerResult.SAFE_PASS_DISABLED,
                    "risk_class": RiskClass.HIGH_RISK,
                    "artifact_status": ArtifactStatus.QUARANTINED,
                    "parent_task_status": ParentTaskStatus.QUARANTINED,
                    "reason": (
                        "Safe-pass is disabled. High-risk artifact quarantined. "
                        "Operator must resolve model/fingerprint issue and resubmit goal."
                    ),
                    "details": {
                        "safe_pass_enabled": False,
                        "risk_class": risk_class,
                        "note": "v1.10.2: high-risk artifacts may not rehabilitate in-session",
                    },
                }
            else:
                return {
                    "scanner_result": ScannerResult.SAFE_PASS_DISABLED,
                    "risk_class": RiskClass.ORDINARY,
                    "artifact_status": ArtifactStatus.CHECKPOINT_BLOCKED,
                    "parent_task_status": ParentTaskStatus.NEEDS_HUMAN_INPUT,
                    "reason": (
                        "Safe-pass is disabled. Ordinary artifact checkpoint-blocked. "
                        "Operator may retry after safe-pass re-enabled and fingerprint verified."
                    ),
                    "details": {
                        "safe_pass_enabled": False,
                        "risk_class": risk_class,
                        "note": "v1.10.2: ordinary artifacts may be re-scanned after safe-pass re-enabled",
                    },
                }

        # --- Deterministic scan (always-run phase) ---
        det_result = self._deterministic_scan(artifact_json)
        if det_result["blocked"]:
            if risk_class == RiskClass.HIGH_RISK:
                return {
                    "scanner_result": ScannerResult.DETERMINISTIC_BLOCK,
                    "risk_class": RiskClass.HIGH_RISK,
                    "artifact_status": ArtifactStatus.QUARANTINED,
                    "parent_task_status": ParentTaskStatus.QUARANTINED,
                    "reason": det_result["reason"],
                    "details": det_result.get("details"),
                }
            else:
                return {
                    "scanner_result": ScannerResult.DETERMINISTIC_BLOCK,
                    "risk_class": RiskClass.ORDINARY,
                    "artifact_status": ArtifactStatus.CHECKPOINT_BLOCKED,
                    "parent_task_status": ParentTaskStatus.NEEDS_HUMAN_INPUT,
                    "reason": det_result["reason"],
                    "details": det_result.get("details"),
                }

        # --- Classifier scan (requires calibration to be available) ---
        clf_result = self._classifier_scan(artifact_json)
        if clf_result["blocked"]:
            if risk_class == RiskClass.HIGH_RISK:
                return {
                    "scanner_result": ScannerResult.CLASSIFIER_BLOCK,
                    "risk_class": RiskClass.HIGH_RISK,
                    "artifact_status": ArtifactStatus.QUARANTINED,
                    "parent_task_status": ParentTaskStatus.QUARANTINED,
                    "reason": clf_result["reason"],
                    "details": clf_result.get("details"),
                }
            else:
                return {
                    "scanner_result": ScannerResult.CLASSIFIER_BLOCK,
                    "risk_class": RiskClass.ORDINARY,
                    "artifact_status": ArtifactStatus.CHECKPOINT_BLOCKED,
                    "parent_task_status": ParentTaskStatus.NEEDS_HUMAN_INPUT,
                    "reason": clf_result["reason"],
                    "details": clf_result.get("details"),
                }

        # --- Passed ---
        return {
            "scanner_result": ScannerResult.PASSED,
            "risk_class": RiskClass.ORDINARY,
            "artifact_status": ArtifactStatus.SCANNER_PASSED,
            "parent_task_status": ParentTaskStatus.RUNNING,
            "reason": "No injection indicators detected by deterministic or classifier scan.",
            "details": {
                "deterministic_checks_passed": det_result["checks"],
                "classifier_score": clf_result.get("score"),
            },
        }

    def _deterministic_scan(self, artifact_json: Dict[str, Any]) -> Dict[str, Any]:
        """Placeholder for deterministic pattern scanning."""
        return {"blocked": False, "reason": None, "checks": []}

    def _classifier_scan(self, artifact_json: Dict[str, Any]) -> Dict[str, Any]:
        """Placeholder for local classifier inference."""
        return {"blocked": False, "reason": None, "score": None}
```

## PolicyEngine Seven-Step Authorization Rule

Tool execution is allowed only if all checks pass:

1. `tool_id in allowed_tools`.
2. `tool_id not in forbidden_tools`.
3. `tool_id in loaded tool_capability_map.tools`.
4. Mapped capability source permits operation.
5. Every listed additional check passes.
6. If `tool_id.startswith("session_controller.")`, `manifest_type == "operator_control"`.
7. Missing policy objects fail closed and log policy denial.

Canonical implementation for `axiom/core/policy_engine.py`:

```python
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from axiom.core.tool_capability_map import get_tool_entry, get_all_tool_ids


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str
    details: Optional[Dict[str, Any]] = None

    @classmethod
    def denied(cls, reason: str, details: Optional[Dict[str, Any]] = None):
        return cls(allowed=False, reason=reason, details=details)

    @classmethod
    def allowed(cls, reason: str, details: Optional[Dict[str, Any]] = None):
        return cls(allowed=True, reason=reason, details=details)


class PolicyEngine:
    """
    Stateless policy evaluator with boot-time cached validators.
    Binding conditions: 8 (stateless + cached), 10 (fail-closed).
    """

    def __init__(self):
        # Boot-time cache of all valid tool IDs from registered artifact
        self._valid_tool_ids = get_all_tool_ids()

    def authorize_tool_use(
        self,
        tool_id: str,
        manifest: Dict[str, Any],
        task_context: Dict[str, Any],
    ) -> PolicyDecision:
        """
        Seven-step tool authorization per v1.11.3 Section 5.
        """
        # --- Step 1: Known tool ID ---
        if tool_id not in self._valid_tool_ids:
            return PolicyDecision.denied(
                reason="unknown_tool_id",
                details={"tool_id": tool_id, "valid_tools": sorted(self._valid_tool_ids)},
            )

        tool_entry = get_tool_entry(tool_id)
        source_path = tool_entry["source"]

        # --- Step 2: Manifest type compatibility ---
        required_manifest_type = tool_entry.get("requires_manifest_type")
        manifest_type = manifest.get("manifest_type")
        if required_manifest_type and manifest_type != required_manifest_type:
            return PolicyDecision.denied(
                reason="manifest_type_mismatch",
                details={
                    "tool_id": tool_id,
                    "required_manifest_type": required_manifest_type,
                    "actual_manifest_type": manifest_type,
                },
            )

        # --- Step 3: Tool present in manifest allowed_tools ---
        allowed_tools = manifest.get("allowed_tools", [])
        if tool_id not in allowed_tools:
            return PolicyDecision.denied(
                reason="tool_not_in_allowed_tools",
                details={"tool_id": tool_id, "allowed_tools": allowed_tools},
            )

        # --- Step 4: Tool NOT in manifest forbidden_tools ---
        forbidden_tools = manifest.get("forbidden_tools", [])
        if tool_id in forbidden_tools:
            return PolicyDecision.denied(
                reason="tool_in_forbidden_tools",
                details={"tool_id": tool_id, "forbidden_tools": forbidden_tools},
            )

        # --- Step 5: Mapped capability source permits operation ---
        source_value = self._resolve_source_path(manifest, source_path)
        if not source_value:
            return PolicyDecision.denied(
                reason="capability_source_not_granted",
                details={"tool_id": tool_id, "source_path": source_path, "source_value": source_value},
            )

        # --- Step 6: v1.11.3 addition — session_controller.* requires operator_control manifest ---
        if tool_id.startswith("session_controller."):
            if manifest_type != "operator_control":
                return PolicyDecision.denied(
                    reason="session_controller_requires_operator_control_manifest",
                    details={"tool_id": tool_id, "manifest_type": manifest_type},
                )
            # v1.11.3 cross-field: command_name must be in allowed_commands
            command_name = manifest.get("operator_command", {}).get("command_name")
            allowed_commands = manifest.get("allowed_capabilities", {}).get("operator_control", {}).get("allowed_commands", [])
            if command_name not in allowed_commands:
                return PolicyDecision.denied(
                    reason="operator_command_not_in_allowed_commands",
                    details={"command_name": command_name, "allowed_commands": allowed_commands},
                )

        # --- Step 7: Additional checks (additive gating, not bypass) ---
        additional_checks = tool_entry.get("additional_checks", [])
        for check in additional_checks:
            check_result = self._run_additional_check(check, manifest, task_context)
            if not check_result["passed"]:
                return PolicyDecision.denied(
                    reason=f"additional_check_failed:{check}",
                    details={"check": check, "info": check_result.get("info")},
                )

        return PolicyDecision.allowed(
            reason="all_authorization_steps_passed",
            details={"tool_id": tool_id, "steps_executed": 7},
        )

    def _resolve_source_path(self, manifest: Dict[str, Any], path: str) -> Any:
        """Resolve dot-notation source path against manifest dict."""
        parts = path.split(".")
        current = manifest
        for part in parts:
            if not isinstance(current, dict):
                return None
            current = current.get(part)
        return current

    def _run_additional_check(
        self,
        check_name: str,
        manifest: Dict[str, Any],
        task_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Placeholder for additional check implementations."""
        # Deferred to gateway implementation phases
        return {"passed": True, "info": "check_not_yet_implemented"}
```

Required fail-closed helper:

```python
def require_policy(manifest: dict, policy_name: str) -> dict:
    policy = manifest.get(policy_name)
    if not isinstance(policy, dict):
        raise PolicyDeniedError(f"Missing or invalid required policy object: {policy_name}")
    return policy
```

Mandatory policy objects:

```text
budget_policy
allowed_capabilities
network_policy
sandbox_policy
memory_policy
audit_policy
```

Operator-control manifests additionally require:

```text
operator_command
authorization_policy
```

Role manifests additionally require:

```text
role
```

---

# Canonical MVP Acceptance Test Suite — v1.13

Source: union of v1.10.2, v1.11.1-v1.11.4, v1.11.4 Final Patch, and v1.13 defect repairs.

Repair summary: Tests 47–49 and surrounding rows updated to assert canonical v1.11.1 §1.3 values. New rows added for regex validation, enum completeness, and risk-class disposition pairs.

The following list is canonical for v1.13. The numbering is stable; do not renumber without panel approval.

1. **Phase 2** — Schema migration table contains exactly one row with version `v1.11.4` after `init_db()`  
   Source: `v1.11.4`
2. **Phase 2** — `init_db()` does not execute when `schema.sql` is not on disk  
   Source: `v1.11`
3. **Phase 2** — `schema.sql` contains `memory_item_embeddings` virtual table using `vec0(embedding float[768])`  
   Source: `v1.11`
4. **Phase 2** — `schema.sql` contains `PRAGMA cache_size = -32768` (32 MiB)  
   Source: `v1.11.3`
5. **Phase 2** — `manifest_fingerprints.manifest_type` CHECK allows `tool_capability_map`  
   Source: `v1.11.4`
6. **Phase 2** — `manifest_fingerprints` CHECK constraint enforces role \| operator_control \| tool_capability_map row-level validity  
   Source: `v1.11.4`
7. **Phase 2** — `manifest_fingerprints` contains one `tool_capability_map` row after `register_manifests.py`  
   Source: `v1.11.4`
8. **Phase 2** — Manifest schema validates a correctly formed role manifest  
   Source: `v1.10.2`
9. **Phase 2** — Manifest schema rejects role manifest with operator-control commands in `allowed_capabilities.operator_control.allowed_commands`  
   Source: `v1.11.3`
10. **Phase 2** — Manifest schema validates a correctly formed operator-control manifest  
   Source: `v1.10.2`
11. **Phase 2** — Manifest schema rejects operator-control manifest with `allowed_commands.maxItems != 1`  
   Source: `v1.11.3`
12. **Phase 2** — Manifest schema validates `network_policy` with `mode=deny_all` and `allowlist=[]`  
   Source: `v1.11.4`
13. **Phase 2** — Manifest schema rejects `network_policy` with `mode=deny_all` and non-empty `allowlist`  
   Source: `v1.11.4`
14. **Phase 2** — Manifest schema validates `network_policy` with `mode=allowlist_only` and `allowlist.minItems >= 1`  
   Source: `v1.11.4`
15. **Phase 2** — Manifest schema rejects `network_policy` with `mode=allowlist_only` and `allowlist=[]`  
   Source: `v1.11.4`
16. **Phase 2** — Manifest schema validates `tool_id` enum values (all 14 canonical tool IDs)  
   Source: `v1.11.4`
17. **Phase 2** — Manifest schema rejects unknown `tool_id` strings  
   Source: `v1.11.4`
18. **Phase 2** — Manifest schema accepts `max_response_bytes` up to 5242880 (5 MiB)  
   Source: `v1.11.4`
19. **Phase 2** — Manifest schema rejects `max_response_bytes > 5242880`  
   Source: `v1.11.4`
20. **Phase 2** — Defect 4 new: `manifest_id` regex accepts `role.goal_planner.v1`  
   Source: `v1.13`
21. **Phase 2** — Defect 4 new: `manifest_id` regex rejects `rolegoal_planner.v1`  
   Source: `v1.13`
22. **Phase 2** — `register_manifests.py` computes correct SHA256 per file  
   Source: `v1.10.1`
23. **Phase 2** — `register_manifests.py` validates all manifests against JSON Schema  
   Source: `v1.10.1`
24. **Phase 2** — `register_manifests.py` writes all rows atomically (transaction)  
   Source: `v1.10.1`
25. **Phase 2** — `register_manifests.py` rolls back on any single validation failure  
   Source: `v1.10.1`
26. **Phase 2** — `register_manifests.py` performs semantic cross-field validation (operator_control binding)  
   Source: `v1.11.3`
27. **Phase 2** — `register_manifests.py` validates tool IDs against tool-capability map  
   Source: `v1.11.4`
28. **Phase 2** — `register_manifests.py` writes canonical `tool_capability_map` row with NULL role_name and NULL command_name  
   Source: `v1.11.4`
29. **Phase 2** — `register_model_fingerprint.py` requires passing calibration_run_id  
   Source: `v1.11.1`
30. **Phase 2** — `register_model_fingerprint.py` rejects if calibration_run_id does not exist  
   Source: `v1.11.1`
31. **Phase 2** — `register_model_fingerprint.py` rejects if calibration did not pass  
   Source: `v1.11.1`
32. **Phase 2** — `register_model_fingerprint.py` queries Ollama `/api/show` and extracts profile data  
   Source: `v1.11.1`
33. **Phase 2** — `register_model_fingerprint.py` sets `thinking_mode` per Arbiter rule (parameters field only)  
   Source: `v1.11.4`
34. **Phase 2** — `register_model_fingerprint.py` rejects registration if `thinking_mode != "disabled"`  
   Source: `v1.11.4`
35. **Phase 2** — `register_model_fingerprint.py` sets `is_current = 1`, `registration_status = 'current'`  
   Source: `v1.11.1`
36. **Phase 2** — `register_model_fingerprint.py` atomically supersedes prior `is_current = 1` row  
   Source: `v1.11.1`
37. **Phase 2** — `ModelFingerprintGuard._infer_thinking_mode()` returns "disabled" when `parameters` contains `think false`  
   Source: `v1.11.4`
38. **Phase 2** — `ModelFingerprintGuard._infer_thinking_mode()` returns "disabled" when `parameters` contains `THINK FALSE`  
   Source: `v1.11.4`
39. **Phase 2** — `ModelFingerprintGuard._infer_thinking_mode()` returns "disabled" when `parameters` contains `  think  false  `  
   Source: `v1.11.4`
40. **Phase 2** — `ModelFingerprintGuard._infer_thinking_mode()` returns "unknown" when `parameters` does not contain `think false`  
   Source: `v1.11.4`
41. **Phase 2** — `ModelFingerprintGuard._infer_thinking_mode()` does NOT inspect `template` field  
   Source: `v1.11.4 / Arbiter`
42. **Phase 2** — `ModelFingerprintGuard._infer_thinking_mode()` does NOT inspect `system` field  
   Source: `v1.11.4 / Arbiter`
43. **Phase 2** — `ModelFingerprintGuard.verify_ollama_profile()` fails when `thinking_mode` mismatches stored fingerprint  
   Source: `v1.11.4`
44. **Phase 2** — `ModelFingerprintGuard.verify_ollama_profile()` fails when any section hash mismatches  
   Source: `v1.11.4`
45. **Phase 2** — `ModelFingerprintGuard.verify_ollama_profile()` passes when all fields match stored fingerprint  
   Source: `v1.11.4`
46. **Phase 2** — `ModelGateway.call_local_ollama()` injects `"think": false` into options  
   Source: `v1.11.4`
47. **Phase 2** — `ModelGateway.call_local_ollama()` rejects caller override `"think": true`  
   Source: `v1.11.4`
48. **Phase 2** — `ModelGateway.call_local_ollama()` preserves other caller options when injecting think=false  
   Source: `v1.11.4`
49. **Phase 2** — Defect 4 repair: `PlanInjectionScanner.scan(risk_class="ordinary")` returns `parent_task_status="needs_human_input"` and `artifact_status="checkpoint_blocked"` when safe-pass disabled  
   Source: `v1.13`
50. **Phase 2** — Defect 4 repair: `PlanInjectionScanner.scan(risk_class="high_risk")` returns `parent_task_status="quarantined"` and `artifact_status="quarantined"` when safe-pass disabled  
   Source: `v1.13`
51. **Phase 2** — Defect 4 new: `ArtifactStatus` enum members exactly equal `plan_artifacts.artifact_status` CHECK domain  
   Source: `v1.13`
52. **Phase 2** — Defect 4 new: `ParentTaskStatus` enum members exactly equal `tasks.status` CHECK domain; `BLOCKED` is not a member  
   Source: `v1.13`
53. **Phase 2** — Defect 4 new: `PlanInjectionScanner.scan(risk_class="ordinary")` returns `parent_task_status="needs_human_input"` and `artifact_status="checkpoint_blocked"` on deterministic_block  
   Source: `v1.13`
54. **Phase 2** — Defect 4 new: `PlanInjectionScanner.scan(risk_class="high_risk")` returns `parent_task_status="quarantined"` and `artifact_status="quarantined"` on deterministic_block  
   Source: `v1.13`
55. **Phase 2** — Defect 4 new: `PlanInjectionScanner.scan(risk_class="ordinary")` returns `parent_task_status="needs_human_input"` and `artifact_status="checkpoint_blocked"` on classifier_block  
   Source: `v1.13`
56. **Phase 2** — Defect 4 new: `PlanInjectionScanner.scan(risk_class="high_risk")` returns `parent_task_status="quarantined"` and `artifact_status="quarantined"` on classifier_block  
   Source: `v1.13`
57. **Phase 2** — `PolicyEngine.authorize_tool_use()` returns denied for unknown tool_id  
   Source: `v1.11.2`
58. **Phase 2** — `PolicyEngine.authorize_tool_use()` returns denied when tool_id not in manifest allowed_tools  
   Source: `v1.11.2`
59. **Phase 2** — `PolicyEngine.authorize_tool_use()` returns denied when tool_id in manifest forbidden_tools  
   Source: `v1.11.2`
60. **Phase 2** — `PolicyEngine.authorize_tool_use()` returns denied when capability source is false  
   Source: `v1.11.2`
61. **Phase 2** — `PolicyEngine.authorize_tool_use()` returns allowed when all seven steps pass  
   Source: `v1.11.2`
62. **Phase 2** — `PolicyEngine.authorize_tool_use()` Step 6: session_controller. denied with role manifest  
   Source: `v1.11.3`
63. **Phase 2** — `PolicyEngine.authorize_tool_use()` Step 6: session_controller. allowed with operator_control manifest  
   Source: `v1.11.3`
64. **Phase 2** — `PolicyEngine.validate_manifest_completeness()` denied on missing required policy field  
   Source: `v1.11.4`
65. **Phase 2** — `ManifestBinder._bootstrap()` raises if tool_capability_map not registered  
   Source: `v1.11.4`
66. **Phase 2** — `ManifestBinder.verify_file_integrity()` denied on SHA256 mismatch  
   Source: `v1.11.4`
67. **Phase 2** — `ManifestBinder.verify_file_integrity()` allowed on matching SHA256  
   Source: `v1.11.4`
68. **Phase 2** — `tasks.manifest_id` FOREIGN KEY points to `manifest_fingerprints.manifest_id`  
   Source: `v1.10.2`
69. **Phase 2** — `task_permissions.manifest_id` FOREIGN KEY points to `manifest_fingerprints.manifest_id`  
   Source: `v1.10.2`
70. **Phase 2** — `plan_artifacts.manifest_id` FOREIGN KEY points to `manifest_fingerprints.manifest_id`  
   Source: `v1.10.2`
71. **Phase 2** — `provider_usage.provider` CHECK rejects invalid provider enum value  
   Source: `v1.10.2`
72. **Phase 2** — `scheduler_heartbeat` index on `session_id, last_freshness_at DESC` exists  
   Source: `v1.11.2`
73. **Phase 2** — `tasks` index on `commit_batch_id` exists  
   Source: `v1.11.3`
74. **Phase 2** — `tool_capability_map.json` validates against `tool_capability_map_schema.json`  
   Source: `v1.11.4`
75. **Phase 2** — `tool_capability_map.json` contains all 14 tool IDs  
   Source: `v1.11.4`
76. **Phase 2** — `tool_capability_map.json` operator-control entries have correct required_command values  
   Source: `v1.11.4`
77. **Phase 2** — Database has at most one `model_profile_fingerprints` row with `is_current = 1` per `profile_label`  
   Source: `v1.11.1`
78. **Phase 2** — `model_profile_fingerprints` CHECK prevents `is_current = 1` with `thinking_mode = 'unknown'`  
   Source: `v1.11.4`
79. **Phase 2** — `model_profile_fingerprints` CHECK enforces `is_current = 1` implies `registration_status = 'current'`  
   Source: `v1.11.4`
80. **Phase 2** — `sessions.safe_pass_disabled_reason` CHECK rejects invalid enum values  
   Source: `v1.10.2`
81. **Phase 2** — `sessions.safe_pass_disabled_reason` accepts `'manifest_integrity_mismatch'`  
   Source: `v1.11.4`
82. **Phase 2** — `plan_artifacts.scanner_result` CHECK accepts all canonical scanner_result values  
   Source: `v1.11.1`
83. **Phase 2** — `tasks.task_class` CHECK rejects invalid task class values  
   Source: `v1.10.2`
84. **Phase 2** — `register_manifests.py` command-line invocation completes in under 30 seconds for 10 manifests  
   Source: `v1.10.1`
85. **Phase 2** — `register_model_fingerprint.py` command-line invocation completes in under 30 seconds  
   Source: `v1.11.1`
86. **Phase 2** — `db.py` applies `PRAGMA cache_size = -32768` on every connection  
   Source: `v1.11.3`
87. **Phase 2** — `db.py` applies WAL + synchronous=FULL + busy_timeout=5000 on every connection  
   Source: `v1.10.2`
88. **Phase 2** — `register_manifests.py` sets `tool_capability_map` row with `manifest_id = 'security.tool_capability_map.v1'`  
   Source: `v1.11.4`
89. **Phase 2** — `register_manifests.py` command-line tool exits with code 0 on success, code 1 on failure  
   Source: `v1.10.1`
90. **Phase 2** — `register_model_fingerprint.py` command-line tool exits with code 0 on success, code 1 on failure  
   Source: `v1.11.1`
91. **Phase 2** — `register_manifests.py` leaves table empty on rollback  
   Source: `v1.10.1`
92. **Phase 2** — `register_manifests.py` validates `tool_capability_map.json` before any manifest  
   Source: `v1.11.4`
93. **Phase 2** — `ManifestBinder` boot-time load logs `info` event when all fingerprints valid  
   Source: `v1.11.4`
94. **Phase 2** — `ManifestBinder` boot-time load logs `critical` event when fingerprint mismatch detected  
   Source: `v1.11.4`
95. **Phase 2** — `network_policy` redirect_policy `same_host_only` validates correctly  
   Source: `v1.11.4`
96. **Phase 2** — `network_policy` redirect_policy `deny` validates correctly  
   Source: `v1.11.4`
97. **Phase 2** — `network_deny_entry` with all wildcards (`*`) validates correctly  
   Source: `v1.11.4`
98. **Phase 2** — `network_deny_entry` with specific host/port/path validates correctly  
   Source: `v1.11.4`
99. **Phase 2** — `register_manifests.py` rejects manifest with unknown tool_id in `allowed_tools`  
   Source: `v1.11.4`
100. **Phase 2** — `register_manifests.py` rejects manifest with unknown tool_id in `forbidden_tools`  
   Source: `v1.11.4`
101. **Phase 2** — `operator_command_manifest` `authorization_policy.telegram_operator_whitelist_required` is const `true`  
   Source: `v1.11.2`
102. **Phase 2** — `operator_command_manifest` `audit_policy.log_task_id` is const `true`  
   Source: `v1.11.2`
103. **Phase 2** — `operator_command_manifest` `audit_policy.log_manifest_id` is const `true`  
   Source: `v1.11.2`
104. **Phase 2** — `operator_command_manifest` `audit_policy.log_policy_denials` is const `true`  
   Source: `v1.11.2`
105. **Phase 2** — `role_manifest` `allowed_capabilities.operator_control.allowed_commands.maxItems` is const `0`  
   Source: `v1.11.3`
106. **Phase 2** — `operator_control_manifest` `allowed_capabilities.operator_control.allowed_commands.minItems` is const `1`  
   Source: `v1.11.3`
107. **Phase 2** — `operator_control_manifest` `allowed_capabilities.operator_control.allowed_commands.maxItems` is const `1`  
   Source: `v1.11.3`
108. **Phase 2** — `register_manifests.py` can read `tool_capability_map_schema.json` at the chosen schema path  
   Source: `v1.13 final integration pass`

## Task 3 Verification Shell Snippet — v1.13 Scanner Contract

Source: v1.12 Section 12.3.2 with v1.13 repairs applied.

```bash
# 5. Run PlanInjectionScanner return contract tests (tests 49-56)
python -c "
from axiom.security.plan_injection_scanner import PlanInjectionScanner, RiskClass

scanner = PlanInjectionScanner(safe_pass_enabled=False)

# Test 49: ordinary safe-pass disabled → checkpoint_blocked / needs_human_input
result = scanner.scan({'plan': 'test'}, risk_class=RiskClass.ORDINARY)
assert result['scanner_result'] == 'safe_pass_disabled'
assert result['artifact_status'] == 'checkpoint_blocked'
assert result['parent_task_status'] == 'needs_human_input'
assert result['risk_class'] == 'ordinary'

# Test 50: high_risk safe-pass disabled → quarantined / quarantined
result = scanner.scan({'plan': 'test'}, risk_class=RiskClass.HIGH_RISK)
assert result['scanner_result'] == 'safe_pass_disabled'
assert result['artifact_status'] == 'quarantined'
assert result['parent_task_status'] == 'quarantined'
assert result['risk_class'] == 'high_risk'

# Test 51: ArtifactStatus enum completeness
from axiom.security.plan_injection_scanner import ArtifactStatus
expected_statuses = {
    'draft', 'scanner_passed', 'checkpoint_passed', 'checkpoint_failed',
    'checkpoint_blocked', 'quarantined', 'committed'
}
actual_statuses = {m.value for m in ArtifactStatus}
assert actual_statuses == expected_statuses, f'Mismatch: {actual_statuses ^ expected_statuses}'

# Test 52: ParentTaskStatus enum completeness; BLOCKED must not exist
from axiom.security.plan_injection_scanner import ParentTaskStatus
expected_statuses = {
    'pending', 'running', 'completed', 'failed', 'quarantined',
    'needs_human_input', 'blocked_resource_limit', 'cancelled'
}
actual_statuses = {m.value for m in ParentTaskStatus}
assert actual_statuses == expected_statuses, f'Mismatch: {actual_statuses ^ expected_statuses}'
assert not hasattr(ParentTaskStatus, 'BLOCKED'), 'BLOCKED must not be a ParentTaskStatus member'

# Tests 53-56: deterministic/classifier block by risk_class
# (Verified by mock injection into _deterministic_scan / _classifier_scan returning blocked=True)

print('All PlanInjectionScanner v1.13 contract tests passed')
"
```

# Deferred But Still Valid Gaps

These remain real implementation concerns but are not blockers for MVP foundational work:

1. Calibration test set authoring. This is a panel workflow dependency. Safe-pass remains disabled until the panel-authored test set exists and calibration passes.
2. Windows Job Object specifics. This belongs to Phase 4 SandboxGateway.
3. Cloud cascade configuration. This belongs to Phase 4 ModelGateway.
4. Telegram operator whitelist mechanism. This belongs to Phase 6 control plane.

---

# Appendix A — `axiom/persistence/schema.sql`

```sql
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA synchronous = FULL;
PRAGMA busy_timeout = 5000;
PRAGMA cache_size = -32768;

-- ============================================================
-- AXIOM CANONICAL DATABASE SCHEMA
-- Version: v1.11.4 canonical
-- ============================================================

-- ------------------------------------------------------------
-- 1. Schema migration ledger
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS schema_migrations (
    migration_id INTEGER PRIMARY KEY AUTOINCREMENT,
    schema_version TEXT NOT NULL UNIQUE,
    applied_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    notes TEXT
);

-- ------------------------------------------------------------
-- 2. Sessions
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sessions (
    session_id INTEGER PRIMARY KEY AUTOINCREMENT,

    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    ended_at TEXT,

    operator_id TEXT,
    current_chain_id TEXT,

    autonomous_operation_enabled INTEGER NOT NULL DEFAULT 0
        CHECK (autonomous_operation_enabled IN (0, 1)),

    scheduler_status TEXT NOT NULL DEFAULT 'initializing'
        CHECK (scheduler_status IN (
            'initializing',
            'ready',
            'running',
            'paused_after_current',
            'safe_disabled',
            'shutdown_requested',
            'stopped',
            'error'
        )),

    shutdown_requested INTEGER NOT NULL DEFAULT 0
        CHECK (shutdown_requested IN (0, 1)),

    safe_pass_enabled INTEGER NOT NULL DEFAULT 0
        CHECK (safe_pass_enabled IN (0, 1)),

    safe_pass_disabled_reason TEXT
        CHECK (
            safe_pass_disabled_reason IS NULL OR
            safe_pass_disabled_reason IN (
                'fingerprint_mismatch',
                'verification_timeout',
                'connection_error',
                'malformed_response',
                'schema_change',
                'model_unavailable',
                'no_stored_profile',
                'calibration_missing',
                'calibration_failed',
                'operator_disabled',
                'manifest_integrity_mismatch'
            )
        ),

    safe_pass_disabled_at TEXT,

    safe_pass_alert_sent INTEGER NOT NULL DEFAULT 0
        CHECK (safe_pass_alert_sent IN (0, 1))
);

-- ------------------------------------------------------------
-- 3. Task queue
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tasks (
    task_id INTEGER PRIMARY KEY AUTOINCREMENT,

    session_id INTEGER NOT NULL,
    parent_task_id INTEGER,

    chain_id TEXT NOT NULL,
    task_class TEXT NOT NULL
        CHECK (task_class IN (
            'operator_control',
            'goal_planning',
            'task_planning',
            'tool_execution',
            'result_verification',
            'memory_operation',
            'system_maintenance'
        )),

    task_type TEXT NOT NULL,

    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN (
            'pending',
            'running',
            'completed',
            'failed',
            'quarantined',
            'needs_human_input',
            'blocked_resource_limit',
            'cancelled'
        )),

    priority INTEGER NOT NULL DEFAULT 5
        CHECK (priority BETWEEN 0 AND 10),

    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    started_at TEXT,
    completed_at TEXT,

    goal_text TEXT,
    input_json TEXT,
    result_text TEXT,
    result_json TEXT,
    error_info TEXT,

    manifest_id TEXT,

    commit_batch_id TEXT,

    cancel_requested INTEGER NOT NULL DEFAULT 0
        CHECK (cancel_requested IN (0, 1)),

    blocked_reason TEXT,

    FOREIGN KEY (session_id)
        REFERENCES sessions(session_id)
        ON DELETE RESTRICT
        ON UPDATE RESTRICT,

    FOREIGN KEY (parent_task_id)
        REFERENCES tasks(task_id)
        ON DELETE RESTRICT
        ON UPDATE RESTRICT,

    FOREIGN KEY (manifest_id)
        REFERENCES manifest_fingerprints(manifest_id)
        ON DELETE RESTRICT
        ON UPDATE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_tasks_session_status_priority
    ON tasks(session_id, status, priority, created_at);

CREATE INDEX IF NOT EXISTS idx_tasks_chain
    ON tasks(chain_id);

CREATE INDEX IF NOT EXISTS idx_tasks_parent
    ON tasks(parent_task_id);

CREATE INDEX IF NOT EXISTS idx_tasks_commit_batch
    ON tasks(commit_batch_id);

-- ------------------------------------------------------------
-- 4. Task permissions / manifest binding
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS task_permissions (
    permission_id INTEGER PRIMARY KEY AUTOINCREMENT,

    task_id INTEGER NOT NULL,
    manifest_id TEXT NOT NULL,

    granted_capabilities_json TEXT NOT NULL,
    granted_tools_json TEXT NOT NULL,

    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),

    FOREIGN KEY (task_id)
        REFERENCES tasks(task_id)
        ON DELETE RESTRICT
        ON UPDATE RESTRICT,

    FOREIGN KEY (manifest_id)
        REFERENCES manifest_fingerprints(manifest_id)
        ON DELETE RESTRICT
        ON UPDATE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_task_permissions_task
    ON task_permissions(task_id);

-- ------------------------------------------------------------
-- 5. Session events
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS session_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,

    session_id INTEGER NOT NULL,

    event_type TEXT NOT NULL,
    details_json TEXT,

    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),

    FOREIGN KEY (session_id)
        REFERENCES sessions(session_id)
        ON DELETE RESTRICT
        ON UPDATE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_session_events_session_created
    ON session_events(session_id, created_at);

-- ------------------------------------------------------------
-- 6. Security events
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS security_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,

    session_id INTEGER,
    task_id INTEGER,

    event_type TEXT NOT NULL,
    reason TEXT,

    severity TEXT NOT NULL
        CHECK (severity IN ('info', 'warning', 'critical')),

    details_json TEXT,

    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),

    FOREIGN KEY (session_id)
        REFERENCES sessions(session_id)
        ON DELETE RESTRICT
        ON UPDATE RESTRICT,

    FOREIGN KEY (task_id)
        REFERENCES tasks(task_id)
        ON DELETE RESTRICT
        ON UPDATE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_security_events_session_created
    ON security_events(session_id, created_at);

CREATE INDEX IF NOT EXISTS idx_security_events_task
    ON security_events(task_id);

CREATE INDEX IF NOT EXISTS idx_security_events_type
    ON security_events(event_type);

-- ------------------------------------------------------------
-- 7. Scheduler heartbeat
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS scheduler_heartbeat (
    heartbeat_id INTEGER PRIMARY KEY AUTOINCREMENT,

    session_id INTEGER NOT NULL,

    last_freshness_at TEXT NOT NULL,
    last_tick_started_at TEXT,
    last_tick_completed_at TEXT,

    last_blocking_operation_started_at TEXT,
    last_blocking_operation_completed_at TEXT,
    last_blocking_operation_type TEXT,

    active_task_id INTEGER,
    active_chain_id TEXT,

    scheduler_state TEXT,
    last_action TEXT,

    tick_count INTEGER NOT NULL DEFAULT 0,

    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),

    FOREIGN KEY (session_id)
        REFERENCES sessions(session_id)
        ON DELETE RESTRICT
        ON UPDATE RESTRICT,

    FOREIGN KEY (active_task_id)
        REFERENCES tasks(task_id)
        ON DELETE SET NULL
        ON UPDATE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_scheduler_heartbeat_session
    ON scheduler_heartbeat(session_id);

CREATE INDEX IF NOT EXISTS idx_scheduler_heartbeat_latest
    ON scheduler_heartbeat(session_id, last_freshness_at DESC, heartbeat_id DESC);

-- ------------------------------------------------------------
-- 8. Classifier calibration runs
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS classifier_calibration_runs (
    calibration_run_id TEXT PRIMARY KEY,

    calibration_set_id TEXT NOT NULL,
    calibration_set_sha256 TEXT NOT NULL,

    model_name TEXT NOT NULL,
    ollama_host TEXT NOT NULL,

    threshold REAL NOT NULL
        CHECK (threshold >= 0.0 AND threshold <= 1.0),

    passed INTEGER NOT NULL
        CHECK (passed IN (0, 1)),

    true_positive_count INTEGER NOT NULL DEFAULT 0,
    true_negative_count INTEGER NOT NULL DEFAULT 0,
    false_positive_count INTEGER NOT NULL DEFAULT 0,
    false_negative_count INTEGER NOT NULL DEFAULT 0,

    false_positive_rate REAL,
    false_negative_rate REAL,

    approved_by_panel_version TEXT NOT NULL,

    details_json TEXT,

    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_classifier_calibration_runs_model_created
    ON classifier_calibration_runs(model_name, created_at);

-- ------------------------------------------------------------
-- 9. Model profile fingerprints
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS model_profile_fingerprints (
    profile_id INTEGER PRIMARY KEY AUTOINCREMENT,

    profile_label TEXT NOT NULL DEFAULT 'default',

    model_name TEXT NOT NULL,
    ollama_host TEXT NOT NULL,

    ollama_model_tag TEXT NOT NULL,
    ollama_model_digest TEXT NOT NULL,

    quantization TEXT NOT NULL,
    parameter_size TEXT,
    model_family TEXT,
    model_format TEXT,

    thinking_mode TEXT NOT NULL
        CHECK (thinking_mode IN ('disabled', 'enabled', 'unknown')),

    thinking_mode_rule_version TEXT,

    template_sha256 TEXT,
    system_sha256 TEXT,
    parameters_sha256 TEXT,
    details_sha256 TEXT,

    selected_profile_sha256 TEXT NOT NULL UNIQUE,

    calibration_run_id TEXT NOT NULL,

    is_current INTEGER NOT NULL DEFAULT 0
        CHECK (is_current IN (0, 1)),

    registration_status TEXT NOT NULL DEFAULT 'candidate'
        CHECK (registration_status IN (
            'candidate',
            'current',
            'superseded',
            'rejected'
        )),

    registered_by_tool_version TEXT NOT NULL,
    registered_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),

    notes TEXT,

    CHECK (is_current = 0 OR thinking_mode != 'unknown'),
    CHECK (
        (is_current = 1 AND registration_status = 'current')
        OR
        (is_current = 0)
    ),

    FOREIGN KEY (calibration_run_id)
        REFERENCES classifier_calibration_runs(calibration_run_id)
        ON DELETE RESTRICT
        ON UPDATE RESTRICT
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_model_profile_one_current
    ON model_profile_fingerprints(profile_label)
    WHERE is_current = 1;

CREATE INDEX IF NOT EXISTS idx_model_profile_calibration
    ON model_profile_fingerprints(calibration_run_id);

-- ------------------------------------------------------------
-- 10. Manifest integrity fingerprints
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS manifest_fingerprints (
    fingerprint_id INTEGER PRIMARY KEY AUTOINCREMENT,

    manifest_id TEXT NOT NULL UNIQUE,
    manifest_type TEXT NOT NULL
        CHECK (manifest_type IN ('role', 'operator_control', 'tool_capability_map')),

    relative_path TEXT NOT NULL UNIQUE,
    sha256 TEXT NOT NULL,

    schema_version TEXT NOT NULL,
    manifest_version TEXT NOT NULL,

    role_name TEXT,
    command_name TEXT,

    approved_by_panel_version TEXT NOT NULL,

    active INTEGER NOT NULL DEFAULT 1
        CHECK (active IN (0, 1)),

    registered_by_tool_version TEXT NOT NULL,
    registered_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),

    CHECK (
        (manifest_type = 'role' AND role_name IS NOT NULL AND command_name IS NULL)
        OR
        (manifest_type = 'operator_control' AND command_name IS NOT NULL AND role_name IS NULL)
        OR
        (manifest_type = 'tool_capability_map' AND role_name IS NULL AND command_name IS NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_manifest_fingerprints_type_active
    ON manifest_fingerprints(manifest_type, active);

-- ------------------------------------------------------------
-- 11. Provider usage tracking
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS provider_usage (
    usage_id INTEGER PRIMARY KEY AUTOINCREMENT,

    session_id INTEGER NOT NULL,
    task_id INTEGER,

    provider TEXT NOT NULL
        CHECK (provider IN (
            'cerebras',
            'groq',
            'openrouter',
            'sambanova',
            'ollama_local'
        )),
    model TEXT,

    status TEXT NOT NULL DEFAULT 'started'
        CHECK (status IN (
            'started',
            'completed',
            'failed',
            'rate_limited',
            'quota_exhausted',
            'abandoned_session_crash'
        )),

    estimated_input_tokens INTEGER,
    estimated_output_tokens INTEGER,

    actual_input_tokens INTEGER,
    actual_output_tokens INTEGER,

    actuals_unavailable INTEGER NOT NULL DEFAULT 0
        CHECK (actuals_unavailable IN (0, 1)),

    charged_input_estimate INTEGER,
    charged_output_estimate INTEGER,

    error_info TEXT,

    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    completed_at TEXT,

    FOREIGN KEY (session_id)
        REFERENCES sessions(session_id)
        ON DELETE RESTRICT
        ON UPDATE RESTRICT,

    FOREIGN KEY (task_id)
        REFERENCES tasks(task_id)
        ON DELETE RESTRICT
        ON UPDATE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_provider_usage_session_created
    ON provider_usage(session_id, created_at);

CREATE INDEX IF NOT EXISTS idx_provider_usage_provider_status
    ON provider_usage(provider, status);

-- ------------------------------------------------------------
-- 12. Provider usage reconciliations
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS provider_usage_reconciliations (
    reconciliation_id INTEGER PRIMARY KEY AUTOINCREMENT,

    provider TEXT NOT NULL,

    date_range_start TEXT NOT NULL,
    date_range_end TEXT NOT NULL,

    operator_reported_input_tokens INTEGER,
    operator_reported_output_tokens INTEGER,

    local_estimated_tokens INTEGER,
    adjustment_tokens INTEGER,

    discrepancy_percent REAL,

    confirmed_large_adjustment INTEGER NOT NULL DEFAULT 0
        CHECK (confirmed_large_adjustment IN (0, 1)),

    operator_confirmation_timestamp TEXT,

    notes TEXT,

    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_provider_usage_reconciliations_provider_dates
    ON provider_usage_reconciliations(provider, date_range_start, date_range_end);

-- ------------------------------------------------------------
-- 13. Plan artifacts
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS plan_artifacts (
    artifact_id INTEGER PRIMARY KEY AUTOINCREMENT,

    task_id INTEGER NOT NULL,
    parent_task_id INTEGER,

    artifact_type TEXT NOT NULL
        CHECK (artifact_type IN (
            'goal_plan',
            'task_plan',
            'tool_plan',
            'memory_write_candidate',
            'operator_control_plan'
        )),

    artifact_status TEXT NOT NULL DEFAULT 'draft'
        CHECK (artifact_status IN (
            'draft',
            'scanner_passed',
            'checkpoint_passed',
            'checkpoint_failed',
            'checkpoint_blocked',
            'quarantined',
            'committed'
        )),

    commit_status TEXT NOT NULL DEFAULT 'not_started'
        CHECK (commit_status IN (
            'not_started',
            'committing',
            'committed',
            'commit_failed',
            'rolled_back'
        )),

    risk_class TEXT NOT NULL DEFAULT 'ordinary'
        CHECK (risk_class IN ('ordinary', 'high_risk')),

    scanner_result TEXT NOT NULL DEFAULT 'not_scanned'
        CHECK (scanner_result IN (
            'not_scanned',
            'passed',
            'deterministic_block',
            'classifier_block',
            'fingerprint_mismatch',
            'verification_timeout',
            'connection_error',
            'malformed_response',
            'schema_change',
            'model_unavailable',
            'safe_pass_disabled'
        )),

    checkpoint_verdict TEXT NOT NULL DEFAULT 'not_run'
        CHECK (checkpoint_verdict IN (
            'not_run',
            'passed',
            'failed',
            'blocked'
        )),

    artifact_json TEXT NOT NULL,
    scanner_details_json TEXT,
    checkpoint_details_json TEXT,

    manifest_id TEXT,

    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),

    FOREIGN KEY (task_id)
        REFERENCES tasks(task_id)
        ON DELETE RESTRICT
        ON UPDATE RESTRICT,

    FOREIGN KEY (parent_task_id)
        REFERENCES tasks(task_id)
        ON DELETE RESTRICT
        ON UPDATE RESTRICT,

    FOREIGN KEY (manifest_id)
        REFERENCES manifest_fingerprints(manifest_id)
        ON DELETE RESTRICT
        ON UPDATE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_plan_artifacts_task
    ON plan_artifacts(task_id);

CREATE INDEX IF NOT EXISTS idx_plan_artifacts_status
    ON plan_artifacts(artifact_status);

-- ------------------------------------------------------------
-- 14. Operator commands
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS operator_commands (
    command_id INTEGER PRIMARY KEY AUTOINCREMENT,

    task_id INTEGER NOT NULL,

    command_name TEXT NOT NULL,
    command_payload_json TEXT,

    manifest_id TEXT NOT NULL,

    authorization_status TEXT NOT NULL DEFAULT 'pending'
        CHECK (authorization_status IN (
            'pending',
            'authorized',
            'rejected'
        )),

    command_status TEXT NOT NULL DEFAULT 'pending'
        CHECK (command_status IN (
            'pending',
            'inserted_task',
            'completed',
            'failed',
            'rejected'
        )),

    rejection_reason TEXT,

    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    completed_at TEXT,

    FOREIGN KEY (task_id)
        REFERENCES tasks(task_id)
        ON DELETE RESTRICT
        ON UPDATE RESTRICT,

    FOREIGN KEY (manifest_id)
        REFERENCES manifest_fingerprints(manifest_id)
        ON DELETE RESTRICT
        ON UPDATE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_operator_commands_task
    ON operator_commands(task_id);

CREATE INDEX IF NOT EXISTS idx_operator_commands_name_status
    ON operator_commands(command_name, command_status);

-- ------------------------------------------------------------
-- 15. Semantic memory items
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS memory_items (
    memory_item_id INTEGER PRIMARY KEY AUTOINCREMENT,

    session_id INTEGER,
    source_task_id INTEGER,

    content TEXT NOT NULL,
    content_sha256 TEXT NOT NULL,

    metadata_json TEXT,

    embedding_model TEXT NOT NULL DEFAULT 'nomic-embed-text',
    embedding_dim INTEGER NOT NULL DEFAULT 768
        CHECK (embedding_dim = 768),

    embedding_status TEXT NOT NULL DEFAULT 'pending'
        CHECK (embedding_status IN (
            'pending',
            'indexed',
            'failed',
            'soft_deleted'
        )),

    dedupe_score REAL,
    dedupe_source_memory_item_id INTEGER,

    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),

    FOREIGN KEY (session_id)
        REFERENCES sessions(session_id)
        ON DELETE RESTRICT
        ON UPDATE RESTRICT,

    FOREIGN KEY (source_task_id)
        REFERENCES tasks(task_id)
        ON DELETE RESTRICT
        ON UPDATE RESTRICT,

    FOREIGN KEY (dedupe_source_memory_item_id)
        REFERENCES memory_items(memory_item_id)
        ON DELETE RESTRICT
        ON UPDATE RESTRICT
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_memory_items_content_model
    ON memory_items(content_sha256, embedding_model);

CREATE INDEX IF NOT EXISTS idx_memory_items_session
    ON memory_items(session_id);

-- Logical memory_items.embedding is stored here.
-- Application invariant:
--     memory_item_embeddings.rowid == memory_items.memory_item_id
CREATE VIRTUAL TABLE IF NOT EXISTS memory_item_embeddings
USING vec0(
    embedding float[768]
);

-- ------------------------------------------------------------
-- 16. Resource usage
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS resource_usage (
    usage_id INTEGER PRIMARY KEY AUTOINCREMENT,

    task_id INTEGER NOT NULL,

    resource_type TEXT NOT NULL
        CHECK (resource_type IN (
            'sandbox_ram_mb',
            'sandbox_wall_clock_seconds',
            'context_bundle_kb',
            'estimated_input_tokens',
            'estimated_output_tokens',
            'provider_calls',
            'network_response_bytes'
        )),

    amount REAL NOT NULL,
    limit_value REAL,

    status TEXT NOT NULL
        CHECK (status IN (
            'within_limit',
            'exceeded',
            'unknown'
        )),

    details_json TEXT,

    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),

    FOREIGN KEY (task_id)
        REFERENCES tasks(task_id)
        ON DELETE RESTRICT
        ON UPDATE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_resource_usage_task
    ON resource_usage(task_id);

-- ------------------------------------------------------------
-- 17. Provider budget windows
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS provider_budget_windows (
    window_id INTEGER PRIMARY KEY AUTOINCREMENT,

    provider TEXT NOT NULL
        CHECK (provider IN (
            'cerebras',
            'groq',
            'openrouter',
            'sambanova',
            'ollama_local'
        )),

    window_start TEXT NOT NULL,
    window_end TEXT NOT NULL,

    budget_tokens INTEGER,
    used_tokens INTEGER NOT NULL DEFAULT 0,

    budget_requests INTEGER,
    used_requests INTEGER NOT NULL DEFAULT 0,

    status TEXT NOT NULL DEFAULT 'open'
        CHECK (status IN (
            'open',
            'exhausted',
            'closed'
        )),

    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),

    UNIQUE (provider, window_start, window_end)
);

CREATE INDEX IF NOT EXISTS idx_provider_budget_windows_provider_status
    ON provider_budget_windows(provider, status);

INSERT OR IGNORE INTO schema_migrations (schema_version, notes)
VALUES (
    'v1.11.4',
    'Initial AXIOM MVP canonical schema with manifest schemas, tool-capability security artifact, network response ceiling, and Ollama think=false verification.'
);

```

# Appendix B — `axiom/policy/schemas/manifest_schema.json`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "axiom.manifest.schema.v1",
  "title": "AXIOM Manifest Schema v1.11.4",
  "oneOf": [
    { "$ref": "#/$defs/role_manifest" },
    { "$ref": "#/$defs/operator_control_manifest" }
  ],
  "$defs": {
    "manifest_id": {
      "type": "string",
      "pattern": "^(role|operator)\\.[a-z0-9_]+\\.v[0-9]+$"
    },
    "tool_id": {
      "type": "string",
      "enum": [
        "model_gateway.call",
        "memory_gateway.query",
        "memory_gateway.write",
        "network_gateway.fetch",
        "sandbox_gateway.execute",
        "filesystem.read",
        "filesystem.write",
        "session_controller.status",
        "session_controller.cancel_current_chain",
        "session_controller.pause_after_current",
        "session_controller.resume",
        "session_controller.shutdown_after_current",
        "session_controller.run_classifier_validation",
        "session_controller.enable_autonomous",
        "session_controller.reconcile_provider_usage"
      ]
    },
    "budget_policy": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "max_estimated_input_tokens",
        "max_estimated_output_tokens",
        "max_provider_calls",
        "max_wall_clock_seconds"
      ],
      "properties": {
        "max_estimated_input_tokens": { "type": "integer", "minimum": 0 },
        "max_estimated_output_tokens": { "type": "integer", "minimum": 0 },
        "max_provider_calls": { "type": "integer", "minimum": 0 },
        "max_wall_clock_seconds": { "type": "integer", "minimum": 0 }
      }
    },
    "allowed_capabilities": {
      "type": "object",
      "additionalProperties": false,
      "required": [ "model", "task_queue", "filesystem", "operator_control" ],
      "properties": {
        "model": {
          "type": "object",
          "additionalProperties": false,
          "required": [ "allow_model_calls", "allowed_provider_groups", "allow_local_classifier" ],
          "properties": {
            "allow_model_calls": { "type": "boolean" },
            "allowed_provider_groups": {
              "type": "array",
              "items": { "type": "string", "enum": [ "cloud_cascade", "local_classifier" ] },
              "uniqueItems": true
            },
            "allow_local_classifier": { "type": "boolean" }
          }
        },
        "task_queue": {
          "type": "object",
          "additionalProperties": false,
          "required": [ "read_scope", "write_scope", "may_create_tasks", "may_update_own_result", "may_update_other_tasks" ],
          "properties": {
            "read_scope": { "type": "string", "enum": [ "none", "assigned_task", "own_chain" ] },
            "write_scope": { "type": "string", "enum": [ "none", "own_result", "create_child_tasks", "operator_control_insert" ] },
            "may_create_tasks": { "type": "boolean" },
            "may_update_own_result": { "type": "boolean" },
            "may_update_other_tasks": { "type": "boolean" }
          }
        },
        "filesystem": {
          "type": "object",
          "additionalProperties": false,
          "required": [ "read", "write", "allowed_roots" ],
          "properties": {
            "read": { "type": "boolean" },
            "write": { "type": "boolean" },
            "allowed_roots": { "type": "array", "items": { "type": "string" }, "uniqueItems": true }
          }
        },
        "operator_control": {
          "type": "object",
          "additionalProperties": false,
          "required": [ "allowed_commands" ],
          "properties": {
            "allowed_commands": { "type": "array", "items": { "type": "string" }, "uniqueItems": true }
          }
        }
      }
    },
    "network_allow_entry": {
      "type": "object",
      "additionalProperties": false,
      "required": [ "scheme", "host", "port", "path_prefix", "methods", "purpose" ],
      "properties": {
        "scheme": { "type": "string", "enum": [ "https" ] },
        "host": { "type": "string", "pattern": "^[a-z0-9.-]+$" },
        "port": { "type": "integer", "minimum": 1, "maximum": 65535 },
        "path_prefix": { "type": "string", "pattern": "^/" },
        "methods": { "type": "array", "minItems": 1, "items": { "type": "string", "enum": [ "GET", "POST" ] }, "uniqueItems": true },
        "purpose": { "type": "string" }
      }
    },
    "network_deny_entry": {
      "type": "object",
      "additionalProperties": false,
      "required": [ "scheme", "host", "port", "path_prefix", "methods", "reason" ],
      "properties": {
        "scheme": { "oneOf": [ { "const": "*" }, { "const": "https" } ] },
        "host": { "oneOf": [ { "const": "*" }, { "type": "string", "pattern": "^[a-z0-9.-]+$" } ] },
        "port": { "oneOf": [ { "const": "*" }, { "type": "integer", "minimum": 1, "maximum": 65535 } ] },
        "path_prefix": { "oneOf": [ { "const": "*" }, { "type": "string", "pattern": "^/" } ] },
        "methods": { "type": "array", "minItems": 1, "items": { "oneOf": [ { "const": "*" }, { "type": "string", "enum": [ "GET", "POST" ] } ] }, "uniqueItems": true },
        "reason": { "type": "string", "minLength": 1 }
      }
    },
    "network_policy": {
      "type": "object",
      "additionalProperties": false,
      "required": [ "mode", "allowlist", "denylist", "redirect_policy", "timeout_seconds", "max_response_bytes" ],
      "properties": {
        "mode": { "type": "string", "enum": [ "deny_all", "allowlist_only" ] },
        "allowlist": { "type": "array", "items": { "$ref": "#/$defs/network_allow_entry" }, "uniqueItems": true },
        "denylist": { "type": "array", "items": { "$ref": "#/$defs/network_deny_entry" }, "uniqueItems": true },
        "redirect_policy": { "type": "string", "enum": [ "deny", "same_host_only" ] },
        "timeout_seconds": { "type": "integer", "minimum": 0, "maximum": 60 },
        "max_response_bytes": { "type": "integer", "minimum": 0, "maximum": 5242880 }
      },
      "allOf": [
        {
          "if": { "properties": { "mode": { "const": "allowlist_only" } }, "required": [ "mode" ] },
          "then": { "properties": { "allowlist": { "minItems": 1 }, "timeout_seconds": { "minimum": 1 }, "max_response_bytes": { "minimum": 1 } } }
        },
        {
          "if": { "properties": { "mode": { "const": "deny_all" } }, "required": [ "mode" ] },
          "then": { "properties": { "allowlist": { "maxItems": 0 }, "timeout_seconds": { "const": 0 }, "max_response_bytes": { "const": 0 } } }
        }
      ]
    },
    "sandbox_policy": {
      "type": "object",
      "additionalProperties": false,
      "required": [ "allowed", "max_ram_mb", "max_wall_clock_seconds", "network_access" ],
      "properties": {
        "allowed": { "type": "boolean" },
        "max_ram_mb": { "type": "integer", "minimum": 0, "maximum": 256 },
        "max_wall_clock_seconds": { "type": "integer", "minimum": 0, "maximum": 60 },
        "network_access": { "type": "string", "enum": [ "denied" ] }
      }
    },
    "memory_policy": {
      "type": "object",
      "additionalProperties": false,
      "required": [ "read", "write", "max_query_results", "write_requires_dedupe" ],
      "properties": {
        "read": { "type": "boolean" },
        "write": { "type": "boolean" },
        "max_query_results": { "type": "integer", "minimum": 0 },
        "write_requires_dedupe": { "type": "boolean" }
      }
    },
    "audit_policy": {
      "type": "object",
      "additionalProperties": false,
      "required": [ "log_task_id", "log_manifest_id", "log_tool_calls", "log_policy_denials" ],
      "properties": {
        "log_task_id": { "type": "boolean", "const": true },
        "log_manifest_id": { "type": "boolean", "const": true },
        "log_tool_calls": { "type": "boolean" },
        "log_policy_denials": { "type": "boolean", "const": true }
      }
    },
    "role_manifest": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "schema_version", "manifest_type", "manifest_id", "manifest_version",
        "approved_by_panel_version", "description", "role", "budget_policy",
        "allowed_capabilities", "allowed_tools", "forbidden_tools",
        "network_policy", "sandbox_policy", "memory_policy", "audit_policy"
      ],
      "properties": {
        "schema_version": { "type": "string", "const": "axiom.manifest.v1" },
        "manifest_type": { "type": "string", "const": "role" },
        "manifest_id": { "$ref": "#/$defs/manifest_id" },
        "manifest_version": { "type": "string", "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+$" },
        "approved_by_panel_version": { "type": "string", "minLength": 1 },
        "description": { "type": "string" },
        "role": {
          "type": "object",
          "additionalProperties": false,
          "required": [ "role_name", "role_tier", "allowed_task_classes", "may_create_child_tasks", "may_commit_task_tree" ],
          "properties": {
            "role_name": { "type": "string" },
            "role_tier": { "type": "string", "enum": [ "goal_planner", "task_planner", "tool_executor", "result_verifier", "system" ] },
            "allowed_task_classes": { "type": "array", "items": { "type": "string", "enum": [ "goal_planning", "task_planning", "tool_execution", "result_verification", "memory_operation", "system_maintenance" ] }, "uniqueItems": true },
            "may_create_child_tasks": { "type": "boolean" },
            "may_commit_task_tree": { "type": "boolean" }
          }
        },
        "budget_policy": { "$ref": "#/$defs/budget_policy" },
        "allowed_capabilities": {
          "allOf": [
            { "$ref": "#/$defs/allowed_capabilities" },
            { "properties": { "operator_control": { "properties": { "allowed_commands": { "maxItems": 0 } } } } }
          ]
        },
        "allowed_tools": { "type": "array", "items": { "$ref": "#/$defs/tool_id" }, "uniqueItems": true },
        "forbidden_tools": { "type": "array", "items": { "$ref": "#/$defs/tool_id" }, "uniqueItems": true },
        "network_policy": { "$ref": "#/$defs/network_policy" },
        "sandbox_policy": { "$ref": "#/$defs/sandbox_policy" },
        "memory_policy": { "$ref": "#/$defs/memory_policy" },
        "audit_policy": { "$ref": "#/$defs/audit_policy" }
      }
    },
    "operator_control_manifest": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "schema_version", "manifest_type", "manifest_id", "manifest_version",
        "approved_by_panel_version", "description", "operator_command", "authorization_policy",
        "budget_policy", "allowed_capabilities", "allowed_tools", "forbidden_tools",
        "network_policy", "sandbox_policy", "memory_policy", "audit_policy"
      ],
      "properties": {
        "schema_version": { "type": "string", "const": "axiom.manifest.v1" },
        "manifest_type": { "type": "string", "const": "operator_control" },
        "manifest_id": { "$ref": "#/$defs/manifest_id" },
        "manifest_version": { "type": "string", "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+$" },
        "approved_by_panel_version": { "type": "string", "minLength": 1 },
        "description": { "type": "string" },
        "operator_command": {
          "type": "object",
          "additionalProperties": false,
          "required": [ "command_name", "telegram_aliases", "creates_task", "created_task_class", "allowed_when_autonomous_disabled", "allowed_when_safe_pass_disabled", "effect_class" ],
          "properties": {
            "command_name": { "type": "string", "enum": [ "status", "cancel_current_chain", "pause_after_current", "resume", "shutdown_after_current", "run_classifier_validation", "enable_autonomous", "reconcile_provider_usage" ] },
            "telegram_aliases": { "type": "array", "items": { "type": "string", "pattern": "^/" }, "uniqueItems": true },
            "creates_task": { "type": "boolean" },
            "created_task_class": { "type": "string", "const": "operator_control" },
            "allowed_when_autonomous_disabled": { "type": "boolean" },
            "allowed_when_safe_pass_disabled": { "type": "boolean" },
            "effect_class": { "type": "string", "enum": [ "read_only", "state_change", "shutdown", "calibration", "reconciliation" ] }
          }
        },
        "authorization_policy": {
          "type": "object",
          "additionalProperties": false,
          "required": [ "telegram_operator_whitelist_required", "capability_token_required", "requires_active_session" ],
          "properties": {
            "telegram_operator_whitelist_required": { "type": "boolean", "const": true },
            "capability_token_required": { "type": "boolean" },
            "requires_active_session": { "type": "boolean" }
          }
        },
        "budget_policy": { "$ref": "#/$defs/budget_policy" },
        "allowed_capabilities": {
          "allOf": [
            { "$ref": "#/$defs/allowed_capabilities" },
            { "properties": { "operator_control": { "properties": { "allowed_commands": { "minItems": 1, "maxItems": 1 } } } } }
          ]
        },
        "allowed_tools": { "type": "array", "items": { "$ref": "#/$defs/tool_id" }, "uniqueItems": true },
        "forbidden_tools": { "type": "array", "items": { "$ref": "#/$defs/tool_id" }, "uniqueItems": true },
        "network_policy": { "$ref": "#/$defs/network_policy" },
        "sandbox_policy": { "$ref": "#/$defs/sandbox_policy" },
        "memory_policy": { "$ref": "#/$defs/memory_policy" },
        "audit_policy": { "$ref": "#/$defs/audit_policy" }
      }
    }
  }
}
```

# Appendix C — `axiom/policy/security_artifacts/tool_capability_map.json`

```json
{
  "schema_version": "axiom.tool_capability_map.v1",
  "artifact_type": "tool_capability_map",
  "artifact_id": "security.tool_capability_map.v1",
  "artifact_version": "1.0.0",
  "approved_by_panel_version": "v1.11.4",
  "tools": {
    "model_gateway.call": {
      "source": "allowed_capabilities.model.allow_model_calls",
      "additional_checks": [
        "provider_group_allowed",
        "budget_policy_not_exceeded"
      ]
    },
    "memory_gateway.query": {
      "source": "memory_policy.read",
      "additional_checks": [
        "memory_policy.max_query_results"
      ]
    },
    "memory_gateway.write": {
      "source": "memory_policy.write",
      "additional_checks": [
        "memory_policy.write_requires_dedupe"
      ]
    },
    "network_gateway.fetch": {
      "source": "network_policy",
      "additional_checks": [
        "mode_allowlist_only",
        "request_matches_allowlist",
        "request_does_not_match_denylist",
        "redirect_policy",
        "timeout_seconds",
        "max_response_bytes"
      ]
    },
    "sandbox_gateway.execute": {
      "source": "sandbox_policy.allowed",
      "additional_checks": [
        "sandbox_policy.max_ram_mb",
        "sandbox_policy.max_wall_clock_seconds",
        "sandbox_policy.network_access_denied"
      ]
    },
    "filesystem.read": {
      "source": "allowed_capabilities.filesystem.read",
      "additional_checks": [
        "path_under_allowed_roots"
      ]
    },
    "filesystem.write": {
      "source": "allowed_capabilities.filesystem.write",
      "additional_checks": [
        "path_under_allowed_roots"
      ]
    },
    "session_controller.status": {
      "source": "allowed_capabilities.operator_control.allowed_commands",
      "required_command": "status",
      "requires_manifest_type": "operator_control"
    },
    "session_controller.cancel_current_chain": {
      "source": "allowed_capabilities.operator_control.allowed_commands",
      "required_command": "cancel_current_chain",
      "requires_manifest_type": "operator_control"
    },
    "session_controller.pause_after_current": {
      "source": "allowed_capabilities.operator_control.allowed_commands",
      "required_command": "pause_after_current",
      "requires_manifest_type": "operator_control"
    },
    "session_controller.resume": {
      "source": "allowed_capabilities.operator_control.allowed_commands",
      "required_command": "resume",
      "requires_manifest_type": "operator_control"
    },
    "session_controller.shutdown_after_current": {
      "source": "allowed_capabilities.operator_control.allowed_commands",
      "required_command": "shutdown_after_current",
      "requires_manifest_type": "operator_control"
    },
    "session_controller.run_classifier_validation": {
      "source": "allowed_capabilities.operator_control.allowed_commands",
      "required_command": "run_classifier_validation",
      "requires_manifest_type": "operator_control"
    },
    "session_controller.enable_autonomous": {
      "source": "allowed_capabilities.operator_control.allowed_commands",
      "required_command": "enable_autonomous",
      "requires_manifest_type": "operator_control"
    },
    "session_controller.reconcile_provider_usage": {
      "source": "allowed_capabilities.operator_control.allowed_commands",
      "required_command": "reconcile_provider_usage",
      "requires_manifest_type": "operator_control"
    }
  }
}
```

# Appendix D — `axiom/policy/schemas/tool_capability_map_schema.json`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "axiom.tool_capability_map.schema.v1",
  "title": "AXIOM Tool Capability Map Schema v1",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schema_version",
    "artifact_type",
    "artifact_id",
    "artifact_version",
    "approved_by_panel_version",
    "tools"
  ],
  "properties": {
    "schema_version": {
      "type": "string",
      "const": "axiom.tool_capability_map.v1"
    },
    "artifact_type": {
      "type": "string",
      "const": "tool_capability_map"
    },
    "artifact_id": {
      "type": "string",
      "const": "security.tool_capability_map.v1"
    },
    "artifact_version": {
      "type": "string",
      "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+$"
    },
    "approved_by_panel_version": {
      "type": "string",
      "minLength": 1
    },
    "tools": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "model_gateway.call",
        "memory_gateway.query",
        "memory_gateway.write",
        "network_gateway.fetch",
        "sandbox_gateway.execute",
        "filesystem.read",
        "filesystem.write",
        "session_controller.status",
        "session_controller.cancel_current_chain",
        "session_controller.pause_after_current",
        "session_controller.resume",
        "session_controller.shutdown_after_current",
        "session_controller.run_classifier_validation",
        "session_controller.enable_autonomous",
        "session_controller.reconcile_provider_usage"
      ],
      "properties": {
        "model_gateway.call": {
          "$ref": "#/$defs/standard_tool_entry"
        },
        "memory_gateway.query": {
          "$ref": "#/$defs/standard_tool_entry"
        },
        "memory_gateway.write": {
          "$ref": "#/$defs/standard_tool_entry"
        },
        "network_gateway.fetch": {
          "$ref": "#/$defs/standard_tool_entry"
        },
        "sandbox_gateway.execute": {
          "$ref": "#/$defs/standard_tool_entry"
        },
        "filesystem.read": {
          "$ref": "#/$defs/standard_tool_entry"
        },
        "filesystem.write": {
          "$ref": "#/$defs/standard_tool_entry"
        },
        "session_controller.status": {
          "$ref": "#/$defs/operator_control_tool_entry"
        },
        "session_controller.cancel_current_chain": {
          "$ref": "#/$defs/operator_control_tool_entry"
        },
        "session_controller.pause_after_current": {
          "$ref": "#/$defs/operator_control_tool_entry"
        },
        "session_controller.resume": {
          "$ref": "#/$defs/operator_control_tool_entry"
        },
        "session_controller.shutdown_after_current": {
          "$ref": "#/$defs/operator_control_tool_entry"
        },
        "session_controller.run_classifier_validation": {
          "$ref": "#/$defs/operator_control_tool_entry"
        },
        "session_controller.enable_autonomous": {
          "$ref": "#/$defs/operator_control_tool_entry"
        },
        "session_controller.reconcile_provider_usage": {
          "$ref": "#/$defs/operator_control_tool_entry"
        }
      }
    }
  },
  "$defs": {
    "source_path": {
      "type": "string",
      "enum": [
        "allowed_capabilities.model.allow_model_calls",
        "allowed_capabilities.filesystem.read",
        "allowed_capabilities.filesystem.write",
        "allowed_capabilities.operator_control.allowed_commands",
        "memory_policy.read",
        "memory_policy.write",
        "network_policy",
        "sandbox_policy.allowed"
      ]
    },
    "additional_check": {
      "type": "string",
      "enum": [
        "provider_group_allowed",
        "budget_policy_not_exceeded",
        "memory_policy.max_query_results",
        "memory_policy.write_requires_dedupe",
        "mode_allowlist_only",
        "request_matches_allowlist",
        "request_does_not_match_denylist",
        "redirect_policy",
        "timeout_seconds",
        "max_response_bytes",
        "sandbox_policy.max_ram_mb",
        "sandbox_policy.max_wall_clock_seconds",
        "sandbox_policy.network_access_denied",
        "path_under_allowed_roots"
      ]
    },
    "standard_tool_entry": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "source",
        "additional_checks"
      ],
      "properties": {
        "source": {
          "$ref": "#/$defs/source_path"
        },
        "additional_checks": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/additional_check"
          },
          "uniqueItems": true
        }
      },
      "not": {
        "anyOf": [
          {
            "required": [
              "required_command"
            ]
          },
          {
            "required": [
              "requires_manifest_type"
            ]
          }
        ]
      }
    },
    "operator_control_tool_entry": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "source",
        "required_command",
        "requires_manifest_type"
      ],
      "properties": {
        "source": {
          "type": "string",
          "const": "allowed_capabilities.operator_control.allowed_commands"
        },
        "required_command": {
          "type": "string",
          "enum": [
            "status",
            "cancel_current_chain",
            "pause_after_current",
            "resume",
            "shutdown_after_current",
            "run_classifier_validation",
            "enable_autonomous",
            "reconcile_provider_usage"
          ]
        },
        "requires_manifest_type": {
          "type": "string",
          "const": "operator_control"
        },
        "additional_checks": {
          "type": "array",
          "maxItems": 0
        }
      }
    }
  }
}

```

Semantic command/tool suffix equality is still enforced by `ManifestBinder.validate_tool_capability_map_semantics()`.


# Document History

- **v1.11** — 2026-05-03: Prior implementation plan with seven gaps identified
- **v1.12** — 2026-05-04: Complete revision incorporating v1.11.1–v1.11.4 canonical schemas, Arbiter Gap 3 ruling, registration CLIs, ModelGateway think=false enforcement, PlanInjectionScanner return contract, TOOL_CAPABILITY_MAP runtime loading, seven-step authorization, ManifestBinder cross-field validation, PolicyEngine fail-closed, and unified 100-test acceptance suite
- **v1.13** — 2026-05-03: Targeted revision: Defect 1 (manifest_id regex), Defect 2 (PlanInjectionScanner risk_class dispatch), Defect 3 (enum completeness), Defect 4 (acceptance test updates). Architecture spine unchanged. No new sections.

---

End of AXIOM_Implementation_v1.13
