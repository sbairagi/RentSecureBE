"""Architecture regression: Notification.objects.create must stay in notification app."""

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
        if path.name.startswith("test_"):
            continue
        try:
            rel = path.relative_to(REPO_ROOT)
            if str(rel).startswith("notification"):
                continue
        except ValueError:
            continue
        files.append(path)
    return sorted(files)


def _file_contains_notification_create(filepath: Path) -> bool:
    try:
        source = filepath.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return False
    return "Notification.objects.create" in source


class TestImportRules:
    @pytest.mark.parametrize("filepath", _python_files())
    def test_no_notification_create_outside_notification(self, filepath: Path) -> None:
        if filepath.name in EXCLUDED_FILES:
            return
        if _file_contains_notification_create(filepath):
            pytest.fail(
                f"{filepath.relative_to(REPO_ROOT)} creates notifications outside "
                "the notification app."
            )
