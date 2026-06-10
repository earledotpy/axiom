from axiom.security.level2a.nonce_registry import (
    DEFAULT_NONCE_REGISTRY_PATH,
    NONCE_REGISTRY_ENV_VAR,
    NonceRegistry,
    resolve_nonce_registry_path,
)


def test_nonce_registry_registers_and_rejects_duplicates(tmp_path):
    registry = NonceRegistry(tmp_path / "nonce.db")

    assert registry.register_nonce("nonce-1") is True
    assert registry.nonce_exists("nonce-1") is True
    assert registry.register_nonce("nonce-1") is False


def test_nonce_registry_uses_environment_override(monkeypatch, tmp_path):
    db_path = tmp_path / "env-nonce.db"
    monkeypatch.setenv(NONCE_REGISTRY_ENV_VAR, str(db_path))

    registry = NonceRegistry()
    assert registry.path == db_path
    assert registry.register_nonce("env-nonce") is True
    assert db_path.exists()


def test_nonce_registry_does_not_touch_default_path_when_override_is_used(monkeypatch, tmp_path):
    before_exists = DEFAULT_NONCE_REGISTRY_PATH.exists()
    before_mtime = DEFAULT_NONCE_REGISTRY_PATH.stat().st_mtime_ns if before_exists else None
    db_path = tmp_path / "isolated-nonce.db"
    monkeypatch.setenv(NONCE_REGISTRY_ENV_VAR, str(db_path))

    registry = NonceRegistry()
    assert registry.register_nonce("isolated") is True

    after_exists = DEFAULT_NONCE_REGISTRY_PATH.exists()
    after_mtime = DEFAULT_NONCE_REGISTRY_PATH.stat().st_mtime_ns if after_exists else None
    assert (after_exists, after_mtime) == (before_exists, before_mtime)


def test_resolve_nonce_registry_default_is_inside_level2a_directory(monkeypatch):
    monkeypatch.delenv(NONCE_REGISTRY_ENV_VAR, raising=False)

    assert resolve_nonce_registry_path() == DEFAULT_NONCE_REGISTRY_PATH
    assert DEFAULT_NONCE_REGISTRY_PATH.name == "nonce_registry.db"
