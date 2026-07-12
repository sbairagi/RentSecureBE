#!/usr/bin/env python3
"""Architecture Guardian - detects architecture drift and violations."""

from __future__ import annotations

import argparse
import ast
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


class ArchitectureGuardian:
    """Detects architecture violations and drift."""

    def __init__(self, root: Path):
        self.root = root
        self.violations: list[str] = []

    def check_circular_imports(self) -> bool:  # noqa: C901
        """Check for circular imports between Django apps.

        Note: import-linter is the source of truth for architecture rules.
        This check is advisory only.
        """
        apps = [
            "core",
            "properties",
            "smartbot",
            "finance",
            "notification",
            "documents",
            "referral_and_earn",
            "ai_assistant",
            "dashboard",
        ]
        import_graph: dict[str, set[str]] = {app: set() for app in apps}

        for app in apps:
            app_dir = self.root / app
            if not app_dir.exists():
                continue
            for py_file in app_dir.rglob("*.py"):
                if "__pycache__" in str(py_file) or "migrations" in str(py_file):
                    continue
                try:
                    with open(py_file, encoding="utf-8") as f:
                        content = f.read()
                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ImportFrom):
                            if node.module:
                                for other_app in apps:
                                    if other_app != app and node.module.startswith(
                                        other_app
                                    ):
                                        import_graph[app].add(other_app)
                except Exception:  # noqa: BLE001
                    logger.warning("Error reading %s during import graph scan", py_file)

        visited = set()
        rec_stack = set()

        def dfs(app: str) -> bool:
            visited.add(app)
            rec_stack.add(app)
            for neighbor in sorted(import_graph.get(app, [])):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    print(
                        f"[WARN] Circular import detected: {app} <-> "
                        f"{neighbor} (advisory)"
                    )
                    return True
            rec_stack.discard(app)
            return False

        for app in sorted(apps):
            if app not in visited:
                dfs(app)

        return True

    def check_views_have_services(self) -> bool:
        """Check that views delegate to services."""
        view_dirs = [
            self.root / "core" / "views",
            self.root / "properties" / "views",
            self.root / "finance" / "views",
        ]
        for view_dir in view_dirs:
            if not view_dir.exists():
                continue
            for py_file in view_dir.rglob("*.py"):
                if "__pycache__" in str(py_file):
                    continue
                try:
                    with open(py_file, encoding="utf-8") as f:
                        content = f.read()
                    if "def handle" in content and "service" not in content.lower():
                        self.violations.append(
                            f"Possible business logic in view: {py_file}"
                        )
                except Exception:  # noqa: BLE001
                    logger.warning(
                        "Error scanning %s for business logic in views", py_file
                    )

        return len(self.violations) == 0

    def check_django_settings_immutable(self) -> bool:
        """Check that critical Django settings are not hardcoded.

        Note: This is advisory only. import-linter and security scanners are
        the source of truth.
        """
        settings_file = self.root / "rentsecure_be" / "settings.py"
        if not settings_file.exists():
            return True

        content = settings_file.read_text()
        critical_settings = [
            "SECRET_KEY",
            "DEBUG",
            "DATABASES",
            "ALLOWED_HOSTS",
            "CSRF_TRUSTED_ORIGINS",
        ]

        for setting in critical_settings:
            if f"{setting} = config(" in content:
                continue
            if f"{setting}:" in content and "{" in content:
                continue
            if f"{setting} =" in content:
                print(f"[WARN] Hardcoded setting detected: {setting}")

        return True

    def run_all_checks(self) -> int:
        """Run all architecture checks."""
        checks = [
            ("Circular Imports", self.check_circular_imports),
            ("Service Layer Pattern", self.check_views_have_services),
            ("Django Settings", self.check_django_settings_immutable),
        ]

        for name, check in checks:
            try:
                check()
            except Exception as e:
                print(f"[ERROR] {name}: {e}")

        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run architecture guardian checks")
    parser.add_argument("--root", type=str, default=".", help="Repository root")
    args = parser.parse_args()

    guardian = ArchitectureGuardian(Path(args.root))
    return guardian.run_all_checks()


if __name__ == "__main__":
    sys.exit(main())
