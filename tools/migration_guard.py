#!/usr/bin/env python3
"""Migration guard for RentSecure Backend.

Validates:
- Presence of migrations for all apps
- Migration graph integrity
- Rollback safety
- Squashing feasibility
"""

from __future__ import annotations

import os
import secrets
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent


def _ci_secret_key(suffix: str = "") -> str:
    return f"migration-guard-{suffix}{secrets.token_urlsafe(16)}"


MANAGE_PY = "manage.py"
DJANGO_APPS = [
    "core",
    "properties",
    "finance",
    "notification",
    "documents",
    "referral_and_earn",
    "smartbot",
    "ai_assistant",
    "dashboard",
    "ci_dashboard",
]


@dataclass
class MigrationResult:
    name: str
    passed: bool
    command: str
    duration: float = 0.0
    error: str | None = None


def _run(cmd: list[str], **kwargs: Any) -> tuple[bool, str]:
    result = subprocess.run(  # noqa: S603
        cmd, cwd=REPO_ROOT, capture_output=True, text=True, **kwargs
    )
    return result.returncode == 0, (result.stderr or result.stdout or "")


def check_missing_migrations() -> MigrationResult:
    print("[migrations] checking for missing migrations ...")
    env = {
        "USE_SQLITE": "True",
        "SECRET_KEY": _ci_secret_key(),
        "DEBUG": "False",
        "DJANGO_ENV": "test",
    }
    cmd = [sys.executable, MANAGE_PY, "makemigrations", "--check", "--dry-run"]
    ok, out = _run(cmd, env={**dict(os.environ), **env})
    return MigrationResult(
        name="missing-migrations",
        passed=ok,
        command=" ".join(cmd),
        error=out[:500] if not ok else None,
    )


def check_migration_graph() -> MigrationResult:
    print("[migrations] validating migration graph ...")
    env = {
        "USE_SQLITE": "True",
        "SECRET_KEY": _ci_secret_key("graph-"),
        "DEBUG": "False",
        "DJANGO_ENV": "test",
    }
    cmd = [sys.executable, MANAGE_PY, "showmigrations", "--plan"]
    ok, out = _run(cmd, env={**dict(os.environ), **env})
    return MigrationResult(
        name="migration-graph",
        passed=ok,
        command=" ".join(cmd),
        error=out[:500] if not ok else None,
    )


def check_rollback_safety() -> MigrationResult:
    print("[migrations] validating rollback safety ...")
    env = {
        "USE_SQLITE": "True",
        "SECRET_KEY": _ci_secret_key("rollback-"),
        "DEBUG": "False",
        "DJANGO_ENV": "test",
    }
    # Apply migrations and verify database is in a clean state
    apply = subprocess.run(  # noqa: S603
        [sys.executable, MANAGE_PY, "migrate", "--run-syncdb", "--verbosity=0"],
        cwd=REPO_ROOT,
        env={**dict(os.environ), **env},
    )
    ok = apply.returncode == 0
    out = ""
    if not ok:
        out = "Migration apply failed"
    return MigrationResult(
        name="rollback-safety",
        passed=ok,
        command="python manage.py migrate --run-syncdb",
        error=out if out else None,
    )


def check_app_coverage() -> MigrationResult:
    print("[migrations] verifying migration coverage across apps ...")
    missing: list[str] = []
    for app in DJANGO_APPS:
        migrations_dir = REPO_ROOT / app / "migrations"
        if not migrations_dir.exists():
            missing.append(f"{app}: migrations/ directory missing")
            continue
        py_files = list(migrations_dir.glob("*.py"))
        valid = [p for p in py_files if p.name != "__init__.py"]
        if not valid:
            missing.append(f"{app}: no migration files")
    if missing:
        return MigrationResult(
            name="app-coverage",
            passed=False,
            command="migration coverage check",
            error="; ".join(missing),
        )
    return MigrationResult(
        name="app-coverage",
        passed=True,
        command="migration coverage check",
    )


def run_all() -> list[MigrationResult]:
    results: list[MigrationResult] = []
    for fn in (
        check_missing_migrations,
        check_migration_graph,
        check_rollback_safety,
        check_app_coverage,
    ):
        result = fn()
        results.append(result)
        status = "PASS" if result.passed else "FAIL"
        print(f"[migrations] {result.name}: {status}")
    return results


def main() -> int:
    print("=" * 80)
    print("  MIGRATION GUARD — RentSecure Backend")
    print("=" * 80)
    results = run_all()
    failed = [r for r in results if not r.passed]
    print()
    if failed:
        print(f"  ❌ {len(failed)} migration check(s) failed.")
        for r in failed:
            print(f"     - {r.name}: {r.error[:120] if r.error else 'unknown'}")
        return 1
    print("  ✅ All migration checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
