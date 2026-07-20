"""Architecture regression: no view file exceeds 300 lines."""

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
MAX_VIEW_LINES = 300


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


class TestGodViews:
    @pytest.mark.parametrize("filepath", _view_files())
    def test_view_file_under_line_limit(self, filepath: Path) -> None:
        lines = filepath.read_text(encoding="utf-8").splitlines()
        assert len(lines) <= MAX_VIEW_LINES, (
            f"{filepath.relative_to(REPO_ROOT)} exceeds {MAX_VIEW_LINES} lines "
            f"({len(lines)} lines)"
        )
