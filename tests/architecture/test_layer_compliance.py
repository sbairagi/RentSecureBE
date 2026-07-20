"""Architecture regression: views do not import models from other apps."""

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


def _view_files() -> list[Path]:
    files = []
    for path in REPO_ROOT.rglob("*.py"):
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        if path.name.startswith("test_"):
            continue
        try:
            rel = path.relative_to(REPO_ROOT)
            if "views" in rel.parts or path.name.endswith("_views.py"):
                files.append(path)
        except ValueError:
            continue
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


class TestLayerCompliance:
    @pytest.mark.parametrize("filepath", _view_files())
    def test_view_does_not_import_models_from_other_apps(self, filepath: Path) -> None:
        if filepath.name in EXCLUDED_FILES:
            return
        try:
            rel = filepath.relative_to(REPO_ROOT)
            view_app = rel.parts[0]
        except ValueError:
            return

        imports = _imports_from(filepath)
        for imp in imports:
            if imp != view_app and imp not in {"django", "rest_framework"}:
                pytest.fail(
                    f"{filepath.relative_to(REPO_ROOT)} imports from app '{imp}'"
                )
