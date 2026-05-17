I have reviewed the full approved proposal stack (v1.9 baseline → v1.10 → v1.10.1 → v1.10.2). The architecture spine is intact: sequential runtime, SQLite task queue, stateless PolicyEngine, manifest-scoped execution, Telegram control plane, local classifier for sanitizer lane only, cloud models for cognitive work.

Below is the concrete implementation plan, the first three executable tasks, and the gaps that must be clarified before implementation proceeds.

---

AXIOM MVP Implementation Plan

Binding Constraints Applied
- Hardware: HP laptop, Celeron N4500, 8 GB RAM (2.0–2.3 GB headroom), SATA SSD, Windows 11, no GPU
- Runtime: Python 3.12, strict sequential execution, 4-thread cap
- Local model: qwen3:4b Q4 quantized, memory-mapped via Ollama, thinking disabled
- Database: SQLite with WAL mode, `PRAGMA synchronous=FULL`, busy timeout 5000 ms
- Security: Fail-closed on all verification failures; safe-pass disabled until calibration passes
- Budget: Free/near-zero API spend; no new hardware; no paid services

---

First Three Implementation Tasks (In Sequence)

Task 1: Foundation — Project Skeleton, SQLite Schema, and Persistence Layer

Objective: Create the directory structure, database schema, connection layer with WAL mode, and repository stubs. Every subsequent task depends on this.

Step 1.1 — Create directory structure

```
C:\axiom\
├── axiom\
│   ├── __init__.py
│   ├── app\
│   │   ├── __init__.py
│   │   ├── telegram_gateway.py
│   │   ├── operator_control_inserter.py
│   │   ├── session_controller.py
│   │   └── command_parser.py
│   ├── core\
│   │   ├── __init__.py
│   │   ├── scheduler.py
│   │   ├── state_machine.py
│   │   ├── policy_engine.py
│   │   ├── permissions.py
│   │   ├── context_builder.py
│   │   ├── manifest_binder.py
│   │   ├── task_committer.py
│   │   ├── role_executor.py
│   │   └── resource_limits.py
│   ├── agents\
│   │   ├── __init__.py
│   │   ├── goal_planner.py
│   │   ├── task_planner.py
│   │   ├── tool_executor.py
│   │   └── result_verifier.py
│   ├── gateways\
│   │   ├── __init__.py
│   │   ├── model_gateway.py
│   │   ├── memory_gateway.py
│   │   ├── network_gateway.py
│   │   └── sandbox_gateway.py
│   ├── security\
│   │   ├── __init__.py
│   │   ├── sanitizer.py
│   │   ├── plan_injection_scanner.py
│   │   ├── classifier_validation.py
│   │   ├── audit.py
│   │   ├── model_fingerprint_guard.py
│   │   └── test_sets\
│   │       └── injection_classifier_v1.jsonl   (placeholder only)
│   ├── persistence\
│   │   ├── __init__.py
│   │   ├── db.py
│   │   ├── schema.sql
│   │   └── repositories.py
│   └── policy\
│       ├── role_manifests\
│       └── operator_control_manifests\
├── tools\
│   └── register_manifests.py
├── tests\
│   ├── e2e\
│   └── __init__.py
├── config\
│   └── axiom.yaml
├── logs\
└── requirements.txt
```

Step 1.2 — Create `requirements.txt`

```
python-telegram-bot>=20.0
aiohttp
requests
pyyaml
pywin32          # Windows Job Objects for sandbox
ollama           # Ollama Python client
sqlite-vec       # Vector search extension
```

Step 1.3 — Create `axiom/persistence/schema.sql`

Execute this SQL to create the database. (Note: This schema is inferred from the approved design. See Gap #1 below.)

```sql
-- Sessions and safe-pass state
CREATE TABLE IF NOT EXISTS sessions (
    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    autonomous_operation_enabled BOOLEAN DEFAULT 0,
    scheduler_status TEXT DEFAULT 'initializing',
    shutdown_requested BOOLEAN DEFAULT 0,
    safe_pass_enabled BOOLEAN DEFAULT 0,
    safe_pass_disabled_reason TEXT,
    safe_pass_disabled_at DATETIME,
    safe_pass_alert_sent BOOLEAN DEFAULT 0,
    current_chain_id TEXT,
    operator_id TEXT
);

-- Task queue
CREATE TABLE IF NOT EXISTS tasks (
    task_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER REFERENCES sessions(session_id),
    parent_task_id INTEGER REFERENCES tasks(task_id),
    chain_id TEXT,
    task_class TEXT NOT NULL,           -- goal_planning, operator_control, tool_execution, etc.
    task_type TEXT,
    status TEXT DEFAULT 'pending',      -- pending, running, completed, failed, quarantined, needs_human_input, blocked_resource_limit
    priority INTEGER DEFAULT 5,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    started_at DATETIME,
    completed_at DATETIME,
    goal_text TEXT,
    result_text TEXT,
    error_info TEXT,
    manifest_id TEXT,
    commit_batch_id TEXT,
    cancel_requested BOOLEAN DEFAULT 0
);

-- Manifest-scoped permissions per task
CREATE TABLE IF NOT EXISTS task_permissions (
    permission_id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL REFERENCES tasks(task_id),
    manifest_id TEXT NOT NULL,
    granted_capabilities TEXT NOT NULL, -- JSON array
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Security events (immutable audit)
CREATE TABLE IF NOT EXISTS security_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER REFERENCES sessions(session_id),
    task_id INTEGER REFERENCES tasks(task_id),
    event_type TEXT NOT NULL,
    reason TEXT,
    severity TEXT NOT NULL,             -- info, warning, critical
    details TEXT,                       -- JSON
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Session lifecycle events
CREATE TABLE IF NOT EXISTS session_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER REFERENCES sessions(session_id),
    event_type TEXT NOT NULL,
    details TEXT,                       -- JSON
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Scheduler heartbeat (SupervisorMonitor reads this)
CREATE TABLE IF NOT EXISTS scheduler_heartbeat (
    heartbeat_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER REFERENCES sessions(session_id),
    last_freshness_at DATETIME NOT NULL,
    last_tick_started_at DATETIME,
    last_tick_completed_at DATETIME,
    last_blocking_operation_started_at DATETIME,
    last_blocking_operation_completed_at DATETIME,
    last_blocking_operation_type TEXT,
    active_task_id INTEGER REFERENCES tasks(task_id),
    active_chain_id TEXT,
    scheduler_state TEXT,
    last_action TEXT,
    tick_count INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Model profile fingerprints (tied to calibration)
CREATE TABLE IF NOT EXISTS model_profile_fingerprints (
    profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_name TEXT NOT NULL,
    ollama_model_tag TEXT NOT NULL,
    ollama_model_digest TEXT,
    quantization TEXT,
    thinking_mode TEXT,
    ollama_show_json_hash TEXT,
    model_file_mtime REAL,
    model_file_size INTEGER,
    calibration_id TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_current BOOLEAN DEFAULT 0
);

-- Manifest integrity fingerprints
CREATE TABLE IF NOT EXISTS manifest_fingerprints (
    manifest_id INTEGER PRIMARY KEY AUTOINCREMENT,
    relative_path TEXT NOT NULL UNIQUE,
    sha256 TEXT NOT NULL,
    manifest_type TEXT NOT NULL CHECK(manifest_type IN ('role', 'operator_control')),
    version TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    approved_by_panel_version TEXT
);

-- Provider usage tracking
CREATE TABLE IF NOT EXISTS provider_usage (
    usage_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER REFERENCES sessions(session_id),
    provider TEXT NOT NULL,
    model TEXT,
    status TEXT DEFAULT 'started',      -- started, completed, abandoned_session_crash
    estimated_input_tokens INTEGER,
    estimated_output_tokens INTEGER,
    actual_input_tokens INTEGER,
    actual_output_tokens INTEGER,
    actuals_unavailable BOOLEAN DEFAULT 0,
    charged_input_estimate INTEGER,
    charged_output_estimate INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Manual reconciliation records
CREATE TABLE IF NOT EXISTS provider_usage_reconciliations (
    reconciliation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider TEXT NOT NULL,
    date_range_start DATE,
    date_range_end DATE,
    operator_reported_input_tokens INTEGER,
    operator_reported_output_tokens INTEGER,
    local_estimated_tokens INTEGER,
    adjustment_tokens INTEGER,
    discrepancy_percent REAL,
    confirmed_large_adjustment BOOLEAN DEFAULT 0,
    operator_confirmation_timestamp DATETIME,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Plan artifacts (scanner + checkpoint results)
CREATE TABLE IF NOT EXISTS plan_artifacts (
    artifact_id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL REFERENCES tasks(task_id),
    parent_task_id INTEGER REFERENCES tasks(task_id),
    artifact_type TEXT,
    artifact_status TEXT DEFAULT 'draft',   -- draft, checkpoint_passed, checkpoint_failed, quarantined
    commit_status TEXT DEFAULT 'not_started',
    risk_class TEXT,                        -- high_risk, ordinary
    scanner_result TEXT,
    checkpoint_verdict TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Operator control commands
CREATE TABLE IF NOT EXISTS operator_commands (
    command_id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL REFERENCES tasks(task_id),
    command_type TEXT NOT NULL,
    payload TEXT,                           -- JSON
    status TEXT DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Semantic memory
CREATE TABLE IF NOT EXISTS memory_items (
    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER REFERENCES sessions(session_id),
    content TEXT NOT NULL,
    embedding BLOB,                         -- sqlite-vec compatible
    metadata TEXT,                          -- JSON
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Resource usage per task
CREATE TABLE IF NOT EXISTS resource_usage (
    usage_id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL REFERENCES tasks(task_id),
    resource_type TEXT NOT NULL,            -- sandbox_ram, sandbox_time, context_bundle_kb, tokens
    amount REAL,
    limit_value REAL,
    status TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Budget accounting windows
CREATE TABLE IF NOT EXISTS provider_budget_window (
    window_id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider TEXT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    budget_tokens INTEGER,
    used_tokens INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

Step 1.4 — Create `axiom/persistence/db.py`

```python
import sqlite3
import os
from contextlib import contextmanager
from pathlib import Path

DB_PATH = os.environ.get("AXIOM_DB_PATH", r"C:\axiom\axiom.db")
SCHEMA_PATH = Path(__file__).with_name("schema.sql")

def _apply_pragmas(conn: sqlite3.Connection):
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=FULL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    conn.execute("PRAGMA foreign_keys=ON;")

@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    _apply_pragmas(conn)
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            conn.executescript(f.read())
        conn.commit()
        # Verify WAL
        mode = conn.execute("PRAGMA journal_mode;").fetchone()[0]
        if mode.lower() != "wal":
            raise RuntimeError(f"WAL mode not enabled; got {mode}")
```

Step 1.5 — Create `axiom/persistence/repositories.py`

Stub the following classes with basic CRUD:
- `SessionRepository` — create, get_current, update_safe_pass_state, update_scheduler_status
- `TaskRepository` — insert, get_next_pending, update_status, get_by_id, get_running_task
- `SecurityEventRepository` — log_event, get_by_session
- `HeartbeatRepository` — write_heartbeat, get_last_freshness
- `ManifestFingerprintRepository` — insert, get_all, get_by_path
- `ModelProfileRepository` — insert, get_current, set_current

Step 1.6 — Create `config/axiom.yaml`

```yaml
database:
  path: "C:\\axiom\\axiom.db"

ollama:
  host: "http://localhost:11434"
  model: "qwen3:4b"
  fingerprint_timeout_seconds: 5

telegram:
  token_path: "C:\\axiom\\.telegram_token"
  operator_whitelist_path: "C:\\axiom\\.operators"
  keepalive_interval_minutes: 15

sandbox:
  max_ram_mb: 256
  max_wall_clock_seconds: 60
  termination_overhead_seconds: 10
  working_dir: "C:\\axiom\\sandbox_temp"

context:
  max_bundle_kb: 500

scheduler:
  stale_threshold_seconds: 120

provider_cascade:
  - name: cerebras
    model: "qwen-3-235b-a22b-instruct-2507"
  - name: groq
    model: null
  - name: openrouter
    model: null
  - name: sambanova
    model: null
```

Step 1.7 — Initialize database and verify

```powershell
cd C:\axiom
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python -c "from axiom.persistence.db import init_db; init_db()"
sqlite3 axiom.db "PRAGMA journal_mode;"
# Expected output: wal
```

Step 1.8 — Write and run `tests/test_sqlite_wal_mode.py`

```python
import sqlite3
from axiom.persistence.db import get_connection, init_db, DB_PATH

def test_wal_mode():
    init_db()
    with get_connection() as conn:
        mode = conn.execute("PRAGMA journal_mode;").fetchone()[0]
        sync = conn.execute("PRAGMA synchronous;").fetchone()[0]
        busy = conn.execute("PRAGMA busy_timeout;").fetchone()[0]
        assert mode.lower() == "wal"
        assert sync == 2  # FULL
        assert busy >= 5000
```

Acceptance criteria for Task 1:
- Directory structure matches specification
- `init_db()` creates all tables without error
- `PRAGMA journal_mode` returns `wal`
- `test_sqlite_wal_mode.py` passes
- Repository stubs import successfully

---

Task 2: Manifest System — Registration CLI and Integrity Verification

Objective: Implement the manifest registration CLI (outside the autonomous runtime), create initial policy artifacts, and implement boot-time manifest integrity verification with fail-closed behavior.

Step 2.1 — Define manifest JSON schema

Each manifest file is a JSON object with this structure (inferred from approved design — see Gap #2):

```json
{
  "manifest_id": "goal_planner_v1",
  "manifest_type": "role",
  "version": "1.0",
  "role_name": "goal_planner",
  "approved_by_panel_version": "v1.10.2",
  "budget_policy": {
    "max_estimated_input_tokens": 8000,
    "max_estimated_output_tokens": 4000
  },
  "allowed_capabilities": ["decompose_goal", "create_plan_artifact"],
  "allowed_tools": ["model_gateway.call", "memory_gateway.query"],
  "forbidden_tools": ["sandbox_gateway.execute", "network_gateway.fetch"],
  "network_policy": {
    "allowlist": [],
    "denylist": ["*"]
  },
  "sandbox_policy": {
    "allowed": false,
    "max_ram_mb": 0,
    "max_duration_seconds": 0
  },
  "memory_policy": {
    "read_only": true,
    "write_allowed": false,
    "max_vectors": 100
  }
}
```

Step 2.2 — Create initial role manifests

Create these files in `axiom/policy/role_manifests/`:
- `goal_planner.json`
- `task_planner.json`
- `tool_executor_network_fetch.json`
- `tool_executor_sandbox_execute.json`
- `tool_executor_file_limited.json`
- `result_verifier.json`

Step 2.3 — Create initial operator control manifests

Create these files in `axiom/policy/operator_control_manifests/`:
- `status.json`
- `cancel_current_chain.json`
- `pause_after_current.json`
- `resume.json`
- `shutdown_after_current.json`
- `run_classifier_validation.json`
- `enable_autonomous.json`
- `reconcile_provider_usage.json`

Each operator control manifest uses `"manifest_type": "operator_control"` and `"command_name": "<name>"`.

Step 2.4 — Implement `tools/register_manifests.py`

```python
#!/usr/bin/env python3
"""
Standalone CLI tool for manifest fingerprint registration.
NOT imported by the main AXIOM runtime.
"""
import hashlib
import json
import os
import sys
from pathlib import Path

# Add parent to path for persistence access
sys.path.insert(0, str(Path(__file__).parent.parent))

from axiom.persistence.db import get_connection, init_db, _apply_pragmas
import sqlite3

POLICY_DIR = Path(r"C:\axiom\axiom\policy")
DB_PATH = os.environ.get("AXIOM_DB_PATH", r"C:\axiom\axiom.db")

def compute_sha256(file_path: Path) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def register_manifests():
    init_db()
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    _apply_pragmas(conn)
    cursor = conn.cursor()

    # Clear and re-register
    cursor.execute("DELETE FROM manifest_fingerprints")

    for subdir, mtype in [("role_manifests", "role"), ("operator_control_manifests", "operator_control")]:
        manifest_dir = POLICY_DIR / subdir
        if not manifest_dir.exists():
            continue
        for manifest_file in sorted(manifest_dir.glob("*.json")):
            rel_path = str(manifest_file.relative_to(POLICY_DIR.parent))
            sha = compute_sha256(manifest_file)
            with open(manifest_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            cursor.execute(
                """INSERT INTO manifest_fingerprints
                   (relative_path, sha256, manifest_type, version, approved_by_panel_version)
                   VALUES (?, ?, ?, ?, ?)""",
                (rel_path, sha, mtype, data.get("version", "1.0"), data.get("approved_by_panel_version", "unknown"))
            )

    conn.commit()
    conn.close()
    print(f"Registered {cursor.rowcount} manifest fingerprints.")

if __name__ == "__main__":
    register_manifests()
```

Step 2.5 — Implement `security/audit.py::ManifestIntegrityVerifier`

```python
import hashlib
import json
from pathlib import Path
from typing import List, Tuple
from axiom.persistence.repositories import ManifestFingerprintRepository

class ManifestIntegrityVerifier:
    POLICY_DIR = Path(r"C:\axiom\axiom\policy")

    def __init__(self, repo: ManifestFingerprintRepository):
        self.repo = repo

    def verify_all(self) -> Tuple[bool, List[dict]]:
        """
        Returns (all_valid, list_of_mismatches).
        """
        mismatches = []
        registered = {m["relative_path"]: m for m in self.repo.get_all()}

        for subdir in ["role_manifests", "operator_control_manifests"]:
            for manifest_file in sorted((self.POLICY_DIR / subdir).glob("*.json")):
                rel_path = str(manifest_file.relative_to(self.POLICY_DIR.parent))
                current_sha = self._sha256(manifest_file)

                if rel_path not in registered:
                    mismatches.append({"path": rel_path, "reason": "missing_registration"})
                    continue

                expected_sha = registered[rel_path]["sha256"]
                if current_sha != expected_sha:
                    mismatches.append({
                        "path": rel_path,
                        "reason": "hash_mismatch",
                        "expected": expected_sha,
                        "actual": current_sha
                    })

        return len(mismatches) == 0, mismatches

    @staticmethod
    def _sha256(file_path: Path) -> str:
        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
```

Step 2.6 — Implement boot verification in `app/session_controller.py`

Stub `SessionController` with `bootstrap()` method:

```python
class SessionController:
    def __init__(self, manifest_verifier, security_repo, session_repo, telegram_gateway):
        self.manifest_verifier = manifest_verifier
        self.security_repo = security_repo
        self.session_repo = session_repo
        self.telegram = telegram_gateway

    def bootstrap(self) -> dict:
        """
        Returns session dict. On manifest mismatch, returns session with
        autonomous_operation_enabled=False.
        """
        session = self.session_repo.create()
        valid, mismatches = self.manifest_verifier.verify_all()

        if not valid:
            self.session_repo.update(session["session_id"], {
                "autonomous_operation_enabled": False,
                "scheduler_status": "safe_disabled"
            })
            self.security_repo.log_event(
                session_id=session["session_id"],
                event_type="manifest_integrity_mismatch",
                severity="critical",
                details={"mismatches": mismatches}
            )
            if self.telegram:
                self.telegram.send_alert(
                    f"MANIFEST MISMATCH: {len(mismatches)} manifest(s) failed integrity check. "
                    "Autonomous operation disabled. Only /status and /shutdown_after_current available."
                )
            return self.session_repo.get_by_id(session["session_id"])

        self.session_repo.update(session["session_id"], {
            "autonomous_operation_enabled": True,
            "scheduler_status": "ready"
        })
        return self.session_repo.get_by_id(session["session_id"])
```

Step 2.7 — Register manifests and test

```powershell
cd C:\axiom
.\venv\Scripts\activate
python tools\register_manifests.py
# Expected: Registered N manifest fingerprints.
```

Step 2.8 — Write tests

- `tests/test_manifest_integrity_verification.py` — corrupt a manifest file, verify boot fails closed
- `tests/test_manifest_registration_cli_boundary.py` — assert main runtime cannot import `register_manifests` module

Acceptance criteria for Task 2:
- `register_manifests.py` computes SHA256 for all JSON files and writes to `manifest_fingerprints`
- `ManifestIntegrityVerifier.verify_all()` returns mismatch when a file is modified
- Boot sets `autonomous_operation_enabled=False` on mismatch
- Security event `manifest_integrity_mismatch` is written
- Telegram alert is sent on mismatch
- Registration CLI is not importable by main runtime code

---

Task 3: Model Fingerprint Guard and Safe-Pass State Machine

Objective: Implement the ModelFingerprintGuard with 5-second timeout, fail-closed semantics, Ollama profile querying, thinking-mode inference, and safe-pass session state management.

Step 3.1 — Implement `security/model_fingerprint_guard.py`

```python
import json
import os
import time
from pathlib import Path
from typing import Optional, Dict
import requests

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
TIMEOUT = 5  # seconds

class ModelFingerprintGuard:
    def __init__(self, profile_repo, security_repo, session_repo, telegram_gateway):
        self.profile_repo = profile_repo
        self.security_repo = security_repo
        self.session_repo = session_repo
        self.telegram = telegram_gateway

    def verify_current_profile(self, session_id: int) -> bool:
        """
        Pre-decision fingerprint check. Returns True only if current Ollama profile
        matches the stored calibrated fingerprint exactly.
        Any failure (timeout, connection, malformed, mismatch) returns False
        and disables safe-pass.
        """
        try:
            current = self._query_ollama_profile()
        except Exception as e:
            self._handle_failure(session_id, reason=self._classify_error(e))
            return False

        stored = self.profile_repo.get_current()
        if not stored:
            self._handle_failure(session_id, reason="no_stored_profile")
            return False

        match = self._compare_profiles(current, stored)
        if not match:
            self._handle_failure(session_id, reason="fingerprint_mismatch", current=current, stored=stored)
            return False

        return True

    def _query_ollama_profile(self) -> Dict:
        """Query Ollama /api/show with strict timeout."""
        model = os.environ.get("AXIOM_OLLAMA_MODEL", "qwen3:4b")
        resp = requests.post(
            f"{OLLAMA_HOST}/api/show",
            json={"name": model},
            timeout=TIMEOUT
        )
        resp.raise_for_status()
        data = resp.json()

        # Extract fields
        profile = {
            "model_name": model,
            "ollama_model_tag": data.get("modelfile", "")[:200],
            "ollama_model_digest": data.get("digest", ""),
            "quantization": self._extract_quantization(data),
            "thinking_mode": self._infer_thinking_mode(data),  # See Gap #3
            "ollama_show_json_hash": self._hash_json(data),
            "model_file_mtime": None,
            "model_file_size": None,
        }
        return profile

    def _infer_thinking_mode(self, data: dict) -> str:
        """
        Infer whether thinking is disabled for qwen3:4b.
        Inspect template, system, parameters fields.
        """
        template = str(data.get("template", ""))
        system = str(data.get("system", ""))
        params = str(data.get("parameters", ""))

        # Gap: exact pattern for qwen3:4b thinking-disabled is not specified.
        # Placeholder heuristic:
        if "/no_think" in template or "/no_think" in system:
            return "disabled"
        if "thinking" in params and "false" in params.lower():
            return "disabled"
        return "unknown"

    def _compare_profiles(self, current: dict, stored: dict) -> bool:
        fields = [
            "model_name", "ollama_model_digest", "quantization",
            "thinking_mode", "ollama_show_json_hash"
        ]
        for f in fields:
            if current.get(f) != stored.get(f):
                return False
        return True

    def _handle_failure(self, session_id: int, reason: str, current=None, stored=None):
        self.session_repo.update_safe_pass_state(session_id, enabled=False, reason=reason)
        self.security_repo.log_event(
            session_id=session_id,
            event_type="model_fingerprint_verification_failed",
            reason=reason,
            severity="critical",
            details={"current": current, "stored": stored}
        )
        if self.telegram:
            self.telegram.send_security_alert(
                f"SECURITY ALERT: AXIOM could not verify local model fingerprint.\n"
                f"Reason: {reason}.\n"
                f"Classifier safe-pass has been disabled.\n"
                f"Use /status for current session state."
            )

    def _classify_error(self, exc: Exception) -> str:
        if isinstance(exc, requests.Timeout):
            return "timeout"
        if isinstance(exc, requests.ConnectionError):
            return "connection_error"
        return "malformed_response"

    @staticmethod
    def _extract_quantization(data: dict) -> str:
        # Infer from model info if available
        return "Q4_K_M"  # Placeholder; see Gap

    @staticmethod
    def _hash_json(data: dict) -> str:
        import hashlib
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:32]
```

Step 3.2 — Add safe-pass state methods to `SessionRepository`

```python
def update_safe_pass_state(self, session_id: int, enabled: bool, reason: str = None):
    with get_connection() as conn:
        conn.execute(
            """UPDATE sessions SET
               safe_pass_enabled = ?,
               safe_pass_disabled_reason = ?,
               safe_pass_disabled_at = CURRENT_TIMESTAMP,
               safe_pass_alert_sent = CASE WHEN ? = 0 THEN 1 ELSE safe_pass_alert_sent END
               WHERE session_id = ?""",
            (enabled, reason, enabled, session_id)
        )
        conn.commit()
```

Step 3.3 — Integrate fingerprint guard into `security/plan_injection_scanner.py`

Stub the scanner with the safe-pass short-circuit rule:

```python
class PlanInjectionScanner:
    def __init__(self, fingerprint_guard, session_repo):
        self.fingerprint_guard = fingerprint_guard
        self.session_repo = session_repo

    def scan(self, artifact: dict, session_id: int) -> dict:
        """
        Returns dict with:
        - decision: passed | quarantined | needs_human_input | checkpoint_blocked
        - risk_class: high_risk | ordinary
        - reason: str
        """
        session = self.session_repo.get_by_id(session_id)

        # Deterministic rules first (always run)
        rule_result = self._apply_deterministic_rules(artifact)
        if rule_result["decision"] in ("quarantined", "needs_human_input"):
            return rule_result

        # Safe-pass short-circuit: if disabled, skip classifier
        if not session.get("safe_pass_enabled"):
            return {
                "decision": "quarantined" if rule_result["risk_class"] == "high_risk" else "checkpoint_blocked",
                "risk_class": rule_result["risk_class"],
                "reason": "safe_pass_disabled"
            }

        # Pre-decision fingerprint check
        if not self.fingerprint_guard.verify_current_profile(session_id):
            # verify_current_profile already disabled safe-pass and logged events
            return {
                "decision": "quarantined" if rule_result["risk_class"] == "high_risk" else "checkpoint_blocked",
                "risk_class": rule_result["risk_class"],
                "reason": "fingerprint_verification_failed"
            }

        # Classifier safe-pass (only if calibration passed and fingerprint matched)
        classifier_result = self._apply_classifier(artifact)
        return classifier_result

    def _apply_deterministic_rules(self, artifact: dict) -> dict:
        # TODO: schema validation, privileged task class checks, etc.
        return {"decision": "passed", "risk_class": "ordinary", "reason": "deterministic_ok"}
```

Step 3.4 — Write tests

- `tests/test_model_fingerprint_mid_session.py` — verify mismatch disables safe-pass
- `tests/test_model_fingerprint_guard_fail_closed.py` — mock Ollama timeout/connection error, assert safe-pass disabled
- `tests/test_fingerprint_telegram_alert.py` — assert Telegram alert fired on mismatch

Step 3.5 — Run tests

```powershell
cd C:\axiom
.\venv\Scripts\activate
pytest tests/test_model_fingerprint_guard_fail_closed.py -v
pytest tests/test_fingerprint_telegram_alert.py -v
```

Acceptance criteria for Task 3:
- `ModelFingerprintGuard.verify_current_profile()` returns `False` on Ollama timeout (>5s)
- `False` on connection refused, malformed response, schema change
- On any failure: `safe_pass_enabled` set to `False`, security event written, Telegram alert sent
- `PlanInjectionScanner` short-circuits classifier rules when `safe_pass_enabled=False`
- High-risk artifacts become `quarantined`; ordinary become `checkpoint_blocked` → `needs_human_input`
- Alert deduplication: only one Telegram alert per disablement event per session

---

Gaps in the Approved Design Requiring Panel Clarification

The following gaps prevent me from writing complete, unambiguous specifications. The operator can begin Tasks 1–3 above, but should pause at the flagged points until the panel resolves these.

Gap 1: Database Schema Is Not Fully Specified
The approved design references 15 tables and many columns across v1.9–v1.10.2, but never provides a canonical `CREATE TABLE` specification. The schema in Task 1.3 is my inference derived from the proposals. Before the operator commits data to this schema, the panel should confirm:

- Are all tables and columns correct?
- Are the foreign key relationships and `ON DELETE` behaviors correct?
- Is the `tasks.status` enum complete (`pending, running, completed, failed, quarantined, needs_human_input, blocked_resource_limit`)?
- Should `memory_items.embedding` use `BLOB` or `FLOAT[]` for sqlite-vec compatibility?

Impact: High. Wrong schema requires migration or rebuild.

Gap 2: Manifest JSON Schema Is Not Specified
The proposals state that manifests are "security artifacts" and describe concepts like `budget_policy`, `allowed_capabilities`, and `forbidden_tools`, but never define the exact JSON schema. Task 2.1 presents an inferred schema. The panel must confirm:

- What is the exact field set for role manifests vs operator control manifests?
- Are `budget_policy.max_estimated_input_tokens` and `max_estimated_output_tokens` the correct field names?
- How are nested capabilities represented (e.g., `tool_executor.sandbox.execute` vs flat list)?
- What is the canonical format for `network_policy.allowlist/denylist`?

Impact: High. Manifests are the permission boundary; ambiguity creates security holes or false blocks.

Gap 3: Ollama `thinking_mode` Inference Pattern Is Undefined
v1.10.1 explicitly notes: "Ollama does not expose a native stable field named `thinking_mode`" and instructs Kimi to infer it from `/api/show` fields (`template`, `system`, `parameters`). However, the panel never specifies what pattern indicates "thinking disabled" for qwen3:4b. 

The operator cannot implement `ModelFingerprintGuard._infer_thinking_mode()` correctly without knowing:
- What string/pattern in the `template` field means thinking is disabled?
- What `parameters` value (if any) controls thinking mode?
- What should happen if the inference returns `"unknown"` — treat as mismatch or allow with warning?

Impact: Critical. Incorrect inference causes false fingerprint mismatches and disables safe-pass unnecessarily, or worse, allows a thinking-enabled model to pass as disabled.

Gap 4: Calibration Test Set Is a Panel Dependency (Acknowledged but Blocking)
v1.10.1 §6 and v1.10 §3 explicitly state that MVP completion gates on the panel producing `security/test_sets/injection_classifier_v1.jsonl`. The workflow is:

Gemini authors → DeepSeek reviews → Claude checks → Qwen checks → Kimi packages → Operator writes → Calibration runs.

The operator can proceed with Tasks 1–3 and all non-classifier tests, but cannot complete:
- `test_classifier_calibration_thresholds.py`
- `test_classifier_embedded_instruction_no_rule_hit.py`
- `e2e/test_full_goal_flow_minimum.py` (if it exercises the classifier path)
- Full safe-pass enablement

Impact: Blocks final MVP acceptance. The panel must produce and approve the test set before the operator can write it to disk and run calibration.

Gap 5: Sandbox Windows Job Object Implementation Is Not Specified
The proposals reference "Windows Job Object + restricted token (pywin32)" for sandbox RAM containment and network isolation, but provide no Windows API specifics. The legacy reference notes this was researched but never implemented. The operator needs:

- Exact `pywin32` calls to create a Job Object with 256 MB memory limit
- How to assign the child process to the Job Object
- How to create a restricted token with no network privileges
- How to verify network isolation (the proposal says "verified by test")
- Whether `subprocess.run(timeout=60)` is sufficient or if a custom wrapper is needed for the 60s wall-clock cap

Impact: High. Sandbox/network separation is Core Value 6. Without specifics, the operator must research and design the Windows isolation layer, which risks architectural drift.

Gap 6: Cloud Provider API Configuration and Cascade Logic
The proposals reference Cerebras, Groq, OpenRouter, and SambaNova with a priority cascade, but do not specify:

- Exact API endpoint URLs and authentication headers for each provider
- How the operator should store API keys (environment variables, config file, separate file?)
- Per-provider timeout values and retry logic
- Response parsing for token usage reporting
- How the cascade advances when a provider returns rate-limit or quota-exhausted errors

Impact: Medium-High. The ModelGateway cannot be implemented without these specifics. The operator can stub the gateway, but cannot execute cloud-calling tasks.

Gap 7: Telegram Operator ID Whitelist Mechanism
The seven-step operator-control authorization chain (v1.10 §12) references "Telegram operator ID whitelist" as Step 1, but the design does not specify:

- How operator IDs are stored (file, database table, config?)
- The exact format of a Telegram operator ID (numeric user ID, username, chat ID?)
- How the whitelist is loaded and whether it is hot-reloadable
- Whether multiple operators are supported or strictly one

Impact: Medium. Blocks `app/telegram_gateway.py` and `test_operator_control_authorization_chain.py` completion.

---

Recommended Sequencing After Task 3

Phase	Tasks	Dependencies	
Phase 1: Foundation (Tasks 1–3)	DB, manifests, fingerprint guard	None	
Phase 2: Core Runtime	Scheduler, StateMachine, PolicyEngine, TaskCommitter, ManifestBinder	Gap #2 resolved	
Phase 3: Security Layer	Sanitizer, PlanInjectionScanner (deterministic rules), Ingress validation	Gap #4 resolved for classifier path	
Phase 4: Gateways	ModelGateway, MemoryGateway, NetworkGateway, SandboxGateway	Gap #5, #6 resolved	
Phase 5: Agents	GoalPlanner, TaskPlanner, ToolExecutor, ResultVerifier	All prior phases	
Phase 6: Control Plane	TelegramGateway, CommandParser, OperatorControlInserter, SessionController	Gap #7 resolved	
Phase 7: Acceptance	Run full canonical test suite + e2e test	All gaps resolved	

---

I await panel clarification on the seven gaps above. The operator may begin Task 1 immediately, as the directory structure, WAL-mode database, and repository stubs are foundational and reversible. Tasks 2 and 3 should proceed only after the panel confirms the inferred schema (Gap #1) and manifest JSON structure (Gap #2). Task 3 cannot be fully validated until Gap #3 (thinking-mode inference pattern) is resolved.