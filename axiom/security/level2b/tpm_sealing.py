"""Mock-only TPM 2.0 sealing interface for Level 2B tests."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
from typing import Protocol


class MockTpmError(ValueError):
    """Raised when mock TPM operations must fail closed."""


class TpmInterface(Protocol):
    def create_key(self, *, label: str) -> "MockTpmKey":
        ...

    def sign(self, key: "MockTpmKey", payload: bytes) -> "MockSignatureBlock":
        ...


@dataclass(frozen=True)
class MockTpmKey:
    key_id: str
    label: str
    public_key_sha256: str
    non_extractable: bool = True


@dataclass(frozen=True)
class MockSignatureBlock:
    key_id: str
    payload_sha256: str
    signature_sha256: str
    mock_tpm: bool = True


class MockTpm:
    def __init__(self, *, seed: bytes = b"axiom-level2b-mock-tpm") -> None:
        self._seed = seed

    def create_key(self, *, label: str) -> MockTpmKey:
        if not label:
            raise MockTpmError("ERR_TPM_LABEL_REQUIRED")
        key_material = hmac.new(self._seed, label.encode("utf-8"), hashlib.sha256).digest()
        key_id = "mock-tpm-" + hashlib.sha256(key_material).hexdigest()[:16]
        public_hash = "sha256:" + hashlib.sha256(b"public:" + key_material).hexdigest()
        return MockTpmKey(key_id=key_id, label=label, public_key_sha256=public_hash)

    def sign(self, key: MockTpmKey, payload: bytes) -> MockSignatureBlock:
        if not key.non_extractable:
            raise MockTpmError("ERR_TPM_KEY_EXTRACTABLE")
        payload_hash = "sha256:" + hashlib.sha256(payload).hexdigest()
        signature_hash = "sha256:" + hmac.new(
            self._seed,
            f"{key.key_id}:{payload_hash}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return MockSignatureBlock(
            key_id=key.key_id,
            payload_sha256=payload_hash,
            signature_sha256=signature_hash,
        )

    def verify(self, key: MockTpmKey, payload: bytes, signature: MockSignatureBlock) -> bool:
        expected = self.sign(key, payload)
        return expected == signature
