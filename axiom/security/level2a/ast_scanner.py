"""AST risk scanner for Level 2A verifier inputs."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path


class AstScanViolation(ValueError):
    """Raised when verifier source scanning finds a blocked construct."""


@dataclass(frozen=True)
class AstScanFinding:
    path: str
    line: int
    code: str
    detail: str


class _RiskVisitor(ast.NodeVisitor):
    def __init__(self, path: str) -> None:
        self.path = path
        self.findings: list[AstScanFinding] = []

    def _add(self, node: ast.AST, code: str, detail: str) -> None:
        self.findings.append(AstScanFinding(self.path, getattr(node, "lineno", 0), code, detail))

    def visit_Import(self, node: ast.Import) -> None:
        risky_modules = {"subprocess", "socket", "importlib"}
        for alias in node.names:
            root_name = alias.name.split(".", 1)[0]
            if root_name in risky_modules:
                self._add(node, f"ERR_AST_{root_name.upper()}_IMPORT", f"blocked import: {alias.name}")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        root_name = (node.module or "").split(".", 1)[0]
        if root_name in {"subprocess", "socket", "importlib"}:
            self._add(node, f"ERR_AST_{root_name.upper()}_IMPORT", f"blocked import: {node.module}")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        name = _call_name(node.func)
        if name in {"eval", "exec", "__import__", "importlib.import_module", "os.system"}:
            self._add(node, "ERR_AST_BLOCKED_CALL", f"blocked call: {name}")
        if name in {"open", "Path.write_text", "Path.write_bytes"} and _call_may_write(node):
            self._add(node, "ERR_AST_FILE_WRITE", f"blocked file write call: {name}")
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        name = _attribute_name(node)
        if name == "sys.meta_path":
            self._add(node, "ERR_AST_IMPORT_HOOK", "blocked import hook manipulation: sys.meta_path")
        if name == "os.environ":
            self._add(node, "ERR_AST_ENV_MUTATION", "blocked environment mutation: os.environ")
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            name = _attribute_name(target)
            if name in {"sys.meta_path", "os.environ"}:
                self._add(node, "ERR_AST_MUTATION", f"blocked assignment target: {name}")
        self.generic_visit(node)


def _attribute_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _attribute_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return None


def _call_name(node: ast.AST) -> str | None:
    return _attribute_name(node)


def _call_may_write(node: ast.Call) -> bool:
    if not node.args:
        return True
    if _call_name(node.func) in {"Path.write_text", "Path.write_bytes"}:
        return True
    if len(node.args) < 2:
        return False
    mode = node.args[1]
    return isinstance(mode, ast.Constant) and isinstance(mode.value, str) and any(flag in mode.value for flag in "wax+")


def scan_python_source(source: str, *, path: str = "<memory>") -> list[AstScanFinding]:
    tree = ast.parse(source, filename=path)
    visitor = _RiskVisitor(path)
    visitor.visit(tree)
    return visitor.findings


def scan_python_file(path: str | Path) -> list[AstScanFinding]:
    source_path = Path(path)
    return scan_python_source(source_path.read_text(encoding="utf-8"), path=str(source_path))


def scan_python_paths(paths: list[str | Path]) -> list[AstScanFinding]:
    findings: list[AstScanFinding] = []
    for path in paths:
        source_path = Path(path)
        if source_path.suffix == ".py":
            findings.extend(scan_python_file(source_path))
    return findings


def require_ast_scan_clean(paths: list[str | Path]) -> bool:
    findings = scan_python_paths(paths)
    if findings:
        first = findings[0]
        raise AstScanViolation(f"AUDIT_FAILED:{first.code}:{first.path}:{first.line}:{first.detail}")
    return True
