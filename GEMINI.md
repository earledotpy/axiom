# Axiom: Agentic Governance & Policy Framework

Axiom is a high-integrity Python framework for orchestrating agentic workflows with embedded security, deterministic policy enforcement, and structured governance. It utilizes a SQLite foundation with vector search capabilities to manage state, memory, and authorization.

## Project Overview

- **Architecture:** Modular system with specialized directories for core logic (`axiom/core`), persistence (`axiom/persistence`), security (`axiom/security`), and bootstrap validation (`axiom/app`).
- **Policy & Security:** Uses a stateless `PolicyEngine` to authorize tool usage against signed manifests. Enforcement is data-driven, relying on `manifest_type` (e.g., `role`, `operator_control`) and specific capability mappings.
- **State Management:** A central `StateMachine` governs task transitions (e.g., `pending` -> `running` -> `completed`).
- **Persistence:** SQLite-backed with `WAL` mode enabled for concurrency and `sqlite-vec` for vector embeddings (memory).
- **Governance:** Managed through the `governance/` directory, which tracks ratification history, active bindings, and handoffs.

## Building and Running

### Prerequisites
- Python 3.10+
- [Ollama](https://ollama.com/) (configured in `config/axiom.yaml`)

### Setup & Initialization
1.  **Install Dependencies:**
    ```bash
    python -m pip install -r requirements.txt
    ```
2.  **Initialize Database:**
    ```bash
    python -c "from axiom.persistence.db import init_db; init_db()"
    ```
3.  **Register Policy Manifests:**
    Run this tool whenever schema or manifest files in `axiom/policy/` are modified:
    ```bash
    python tools/register_manifests.py
    ```

### Execution & Testing
- **Run Tests:**
  ```bash
  pytest
  ```
- **Focused Testing:**
  ```bash
  pytest tests/test_policy_engine.py
  ```

## Development Conventions

- **Indentation:** 4-space indentation.
- **Typing:** Use type hints (`from __future__ import annotations`) for all new code.
- **Naming:** `snake_case` for functions and modules; `PascalCase` for classes.
- **Imports:** Prefer explicit absolute imports (e.g., `from axiom.core.policy_engine import ...`).
- **Modularity:** Keep modules focused on a single domain. Logic involving policies should live in `axiom/core/policy_engine.py`, while database-specific logic stays in `axiom/persistence/`.
- **Error Handling:** Use descriptive, domain-specific exceptions (e.g., `InvalidTransitionError`, `PolicyDeniedError`).

## Testing Guidelines

- **Framework:** `pytest`.
- **Structure:** Mirror the `axiom/` directory structure in `tests/`.
- **Naming:** Files should be prefixed with `test_` (e.g., `tests/test_boot_verifier.py`).
- **Invariants:** Prioritize testing safety invariants and edge cases in policy enforcement (both allowed and denied paths).

## Configuration

Default runtime settings are stored in `config/axiom.yaml`. You can override the database path using the `AXIOM_DB_PATH` environment variable.
