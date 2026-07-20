"""Architecture regression: documents module is a projection (read-only).

The documents module generates PDFs from domain data. It must not write
to domain context tables (properties, core, finance, notification).
Allowed operations: read queries, template rendering, PDF generation.
"""

import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCUMENTS_DIR = REPO_ROOT / "documents"
DOCUMENTS_DIR_REL = Path("documents")
PROPERTIES_MODELS_DIR = REPO_ROOT / "properties" / "models"
PROPERTIES_MODELS_DIR_REL = Path("properties") / "models"
FORBIDDEN_CALL_PATTERNS = {
    "save",
    "create",
    "delete",
    "update",
    "bulk_create",
    "bulk_update",
    "get_or_create",
    "update_or_create",
}
EXCLUDED_DIRS = {
    ".venv",
    "venv",
    "build",
    "dist",
    "__pycache__",
    "migrations",
    ".pytest_cache",
    ".github",
    ".kilo",
    ".nox",
    "tests",
    "management",
}
EXCLUDED_FILES = {"__init__.py"}


def _python_files() -> list[Path]:
    files = []
    for path in REPO_ROOT.rglob("*.py"):
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        if path.name in EXCLUDED_FILES or path.name.startswith("test_"):
            continue
        try:
            rel = path.relative_to(REPO_ROOT)
            if str(rel).startswith("documents") or rel.is_relative_to(
                DOCUMENTS_DIR_REL
            ):
                files.append(path)
        except ValueError:
            continue
    return sorted(files)


def _property_model_files() -> list[Path]:
    files = []
    for path in PROPERTIES_MODELS_DIR.rglob("*.py"):
        if path.name in EXCLUDED_FILES:
            continue
        files.append(path)
    return sorted(files)


def _forbidden_calls(filepath: Path) -> set[str]:
    try:
        source = filepath.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(filepath))
    except (SyntaxError, UnicodeDecodeError):
        return set()

    forbidden = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute) and func.attr in FORBIDDEN_CALL_PATTERNS:
                forbidden.add(func.attr)
    return forbidden


class TestDocumentsProjectionBoundary:
    @pytest.mark.parametrize("filepath", _python_files())
    def test_documents_does_not_write_to_domain_tables(self, filepath: Path) -> None:
        if filepath.name in EXCLUDED_FILES:
            return
        forbidden = _forbidden_calls(filepath)
        assert (
            not forbidden
        ), f"{filepath.relative_to(REPO_ROOT)} contains forbidden write call: {forbidden}"


class TestPropertyModelsProjectionBoundary:
    @pytest.mark.parametrize("filepath", _property_model_files())
    def test_property_models_do_not_contain_write_calls(self, filepath: Path) -> None:
        if filepath.name in EXCLUDED_FILES:
            return
        forbidden = _forbidden_calls(filepath)
        assert (
            not forbidden
        ), f"{filepath.relative_to(REPO_ROOT)} contains forbidden write call: {forbidden}"
