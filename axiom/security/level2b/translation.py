"""Console descriptor translation helpers for future container execution."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DescriptorKind(str, Enum):
    CONSOLE_HANDLE = "console_handle"
    FILE_DESCRIPTOR = "file_descriptor"


class DescriptorStream(str, Enum):
    STDIN = "stdin"
    STDOUT = "stdout"
    STDERR = "stderr"


class TranslationError(ValueError):
    """Raised when descriptor translation would lose stdio semantics."""


@dataclass(frozen=True)
class WindowsDescriptor:
    stream: DescriptorStream
    kind: DescriptorKind
    value: str


@dataclass(frozen=True)
class PosixDescriptor:
    stream: DescriptorStream
    socket_path: str
    pipe_path: str


def translate_descriptor(descriptor: WindowsDescriptor, *, namespace: str = "axiom") -> PosixDescriptor:
    if not descriptor.value:
        raise TranslationError("ERR_EMPTY_DESCRIPTOR")
    safe_value = "".join(ch if ch.isalnum() else "_" for ch in descriptor.value).strip("_").lower()
    if not safe_value:
        raise TranslationError("ERR_INVALID_DESCRIPTOR")
    base = f"/run/{namespace}/{descriptor.stream.value}_{safe_value}"
    return PosixDescriptor(
        stream=descriptor.stream,
        socket_path=f"{base}.sock",
        pipe_path=f"{base}.pipe",
    )


def translate_stdio(descriptors: list[WindowsDescriptor], *, namespace: str = "axiom") -> dict[DescriptorStream, PosixDescriptor]:
    streams = {descriptor.stream for descriptor in descriptors}
    missing = {DescriptorStream.STDIN, DescriptorStream.STDOUT, DescriptorStream.STDERR} - streams
    if missing:
        names = ",".join(sorted(stream.value for stream in missing))
        raise TranslationError(f"ERR_STDIO_STREAM_MISSING:{names}")
    return {descriptor.stream: translate_descriptor(descriptor, namespace=namespace) for descriptor in descriptors}
