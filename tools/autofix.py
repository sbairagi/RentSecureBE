#!/usr/bin/env python3
"""Auto-fix code quality issues for RentSecure Backend.

Applies safe, automated fixes for:
- Ruff lint issues
- Black formatting
- isort import ordering
- Unused imports / variables (autoflake)
- Missing Django migrations (safety-checked)
"""

from __future__ import annotations

import os
import secrets
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent


def _ci_secret_key(suffix: str = "") -> str:
    return f"autofix-{suffix}{secrets.token_urlsafe(16)}"


SOURCE_DIRS = [
    "rentsecure_be",
    "ai_assistant",
    "core",
    "dashboard",
    "documents",
    "finance",
    "notification",
    "properties",
    "referral_and_earn",
    "smartbot",
    "scripts",
    "tests",
    "ci_dashboard",
    "management",
    "tools",
]
EXCLUDE_DIRS = {
    ".nox",
    ".venv",
    "venv",
    "site-packages",
    "build",
    "dist",
    "node_modules",
    "htmlcov",
    ".pytest_cache",
    "migrations",
    "__pycache__",
    ".git",
    ".kilo",
    ".hypothesis",
    "reports",
    "frontend",
}


def get_tracked_python_files() -> list[str]:
    """Return Python files from git tracked sources, excluding virtualenv/build dirs."""
    try:
        result = subprocess.run(  # noqa: S603
            ["git", "ls-files"],  # noqa: S607
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )  # noqa: S607
        tracked = [
            f
            for f in result.stdout.splitlines()
            if f.endswith(".py")
            and not any(
                f"/{exclude}/" in f or f.startswith(f"{exclude}/")
                for exclude in EXCLUDE_DIRS
            )
        ]
        if tracked:
            return tracked
    except subprocess.CalledProcessError:
        pass
    return []


def _source_args() -> list[str]:
    tracked = get_tracked_python_files()
    if tracked:
        return tracked
    return [d for d in SOURCE_DIRS if (REPO_ROOT / d).exists()]


def run(cmd: str | Sequence[str], **kwargs: Any) -> bool:
    """Run a hardcoded CI tool command and return True on success."""
    if isinstance(cmd, str):
        cmd = cmd.split()
    result = subprocess.run(cmd, cwd=REPO_ROOT, **kwargs)  # noqa: S603
    return result.returncode == 0


def step_ruff_format() -> bool:
    print("[autofix] ruff format ...")
    args = _source_args()
    return run([sys.executable, "-m", "ruff", "format", *args])


def step_black() -> bool:
    print("[autofix] black ...")
    args = _source_args()
    return run([sys.executable, "-m", "black", *args])


def step_isort() -> bool:
    print("[autofix] isort ...")
    args = _source_args()
    return run([sys.executable, "-m", "isort", *args])


def step_ruff_check() -> bool:
    print("[autofix] ruff check --fix ...")
    args = _source_args()
    return run([sys.executable, "-m", "ruff", "check", *args, "--fix"])


def step_autoflake() -> bool:
    print("[autofix] autoflake (unused imports / variables) ...")
    cmd = [
        sys.executable,
        "-m",
        "autoflake",
        "--in-place",
        "--remove-all-unused-imports",
        "--remove-unused-variables",
        "--ignore-init-module-imports",
        *_source_args(),
    ]
    return run(cmd)


def step_migrations() -> bool:
    """Generate missing migrations if safe to do so."""
    print("[autofix] checking for missing migrations ...")
    env = {
        "USE_SQLITE": "True",
        "SECRET_KEY": _ci_secret_key("migration-guard-"),
        "DEBUG": "False",
        "DJANGO_ENV": "test",
    }
    # Dry-run to detect missing migrations
    check = subprocess.run(  # noqa: S603
        [sys.executable, "manage.py", "makemigrations", "--check", "--dry-run"],
        cwd=REPO_ROOT,
        env={**dict(os.environ), **env},
    )  # noqa: S603
    if check.returncode != 0:
        print("[autofix] missing migrations detected — generating them ...")
        gen = subprocess.run(  # noqa: S603
            [sys.executable, "manage.py", "makemigrations"],
            cwd=REPO_ROOT,
            env={**dict(os.environ), **env},
        )  # noqa: S603
        return gen.returncode == 0
    print("[autofix] no new migrations required.")
    return True


def autofix() -> bool:
    """Run all auto-fix steps. Returns True if all passed."""
    results = [
        step_autoflake(),
        step_ruff_check(),
        step_ruff_format(),
        step_black(),
        step_isort(),
        step_migrations(),
    ]
    return all(results)


def main() -> int:
    print("=" * 80)
    print("  AUTOFIX — RentSecure Backend")
    print("=" * 80)
    ok = autofix()
    print()
    if ok:
        print("  ✅ Autofix complete — no blocking errors.")
        return 0
    print("  ❌ Autofix encountered issues. Review output above.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
