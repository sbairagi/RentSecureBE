"""Architecture regression: no app may import from rentsecure_be/."""

import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
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
            if str(rel).startswith("rentsecure_be"):
                continue
        except ValueError:
            continue
        files.append(path)
    return sorted(files)


def _imports_from(filepath: Path) -> set[str]:
    try:
        source = filepath.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(filepath))
    except (SyntaxError, UnicodeDecodeError):
        return set()

    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and not node.level:
            top = node.module.split(".")[0]
            imports.add(top)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split(".")[0]
                imports.add(top)
    return imports


class TestRentsecureBeBoundary:
    @pytest.mark.parametrize("filepath", _python_files())
    def test_no_imports_from_rentsecure_be(self, filepath: Path) -> None:
        if filepath.name in EXCLUDED_FILES:
            return
        imports = _imports_from(filepath)
        assert (
            "rentsecure_be" not in imports
        ), f"{filepath.relative_to(REPO_ROOT)} imports from rentsecure_be"
