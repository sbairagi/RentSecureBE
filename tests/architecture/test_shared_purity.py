"""Architecture regression: shared package purity."""

import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SHARED_DIR = REPO_ROOT / "shared"
FORBIDDEN_IMPORTS = {
    "core",
    "properties",
    "payments",
    "notification",
    "finance",
    "documents",
    "referral_and_earn",
    "smartbot",
    "rentsecure_be",
}
EXCLUDED_FILES = {"__init__.py"}


def _python_files(directory: Path) -> list[Path]:
    files = []
    for path in directory.rglob("*.py"):
        if any(
            part
            in {
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
            for part in path.parts
        ) or path.name.startswith("test_"):
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


class TestSharedPurity:
    @pytest.mark.parametrize("filepath", _python_files(SHARED_DIR))
    def test_shared_does_not_import_django_or_apps(self, filepath: Path) -> None:
        if filepath.name in EXCLUDED_FILES:
            return
        imports = _imports_from(filepath)
        violations = imports & FORBIDDEN_IMPORTS
        assert (
            not violations
        ), f"{filepath.relative_to(REPO_ROOT)} imports forbidden apps: {violations}"
