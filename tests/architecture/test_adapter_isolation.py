"""Architecture regression: properties module must not import payment modules.

The properties domain context must depend only on shared abstractions.
Payment gateway injection is handled by the application bootstrap
(e.g., rentsecure_be/__init__.py or payments/apps.py) via the
PaymentOrchestrator gateway setter. Concrete payment adapters and
payment services must not be imported directly from properties.
"""

import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PROPERTIES_DIR = REPO_ROOT / "properties"
PROPERTIES_DIR_REL = Path("properties")
FORBIDDEN_PREFIXES = (
    "payments",
    "payments.adapters",
    "payments.gateway",
    "payments.providers",
    "payments.sdk",
    "payments.services",
)
EXCLUDED_DIRS = {
    ".venv",
    "venv",
    "build",
    "dist",
    "__pycache__",
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
            if str(rel).startswith("properties") or rel.is_relative_to(
                PROPERTIES_DIR_REL
            ):
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
            imports.add(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
    return imports


class TestAdapterIsolation:
    @pytest.mark.parametrize("filepath", _python_files())
    def test_properties_does_not_import_payment_modules(self, filepath: Path) -> None:
        if filepath.name in EXCLUDED_FILES:
            return
        imports = _imports_from(filepath)
        violations = {
            imp
            for imp in imports
            if any(
                imp == prefix or imp.startswith(prefix + ".")
                for prefix in FORBIDDEN_PREFIXES
            )
        }
        assert (
            not violations
        ), f"{filepath.relative_to(REPO_ROOT)} imports forbidden payment module: {violations}"
