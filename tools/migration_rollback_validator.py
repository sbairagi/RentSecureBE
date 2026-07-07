#!/usr/bin/env python3
"""Migration Rollback Validator.

Discovers project apps automatically via Django app registry, applies all
migrations once, then for every app with >=2 migrations:
- rolls back the latest migration using the Django migration graph
- re-applies forward to the latest migration
Fails immediately on IrreversibleError or any runtime error.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import django

REPO_ROOT = Path(__file__).resolve().parent.parent
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rentsecure_be.settings")
os.chdir(REPO_ROOT)

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

django.setup()

from django.apps import apps as django_apps  # noqa: E402
from django.core.management import call_command  # noqa: E402
from django.db.migrations.exceptions import IrreversibleError  # noqa: E402
from django.db.migrations.loader import MigrationLoader  # noqa: E402


def _project_apps() -> list[str]:
    base_dir = REPO_ROOT.resolve()
    discovered: list[str] = []
    for app_cfg in sorted(django_apps.get_app_configs(), key=lambda a: a.label):
        app_path = Path(app_cfg.path).resolve()
        is_project = app_path.is_relative_to(base_dir)
        mig_dir = app_path / "migrations"
        has_migrations = False
        if mig_dir.exists():
            has_migrations = any(p.name != "__init__.py" for p in mig_dir.glob("*.py"))
        if is_project and mig_dir.exists() and has_migrations:
            discovered.append(app_cfg.label)
    return discovered


def _graph_info(
    app_label: str, loader: MigrationLoader
) -> tuple[tuple[str, str], tuple[str, str]]:
    """Return ((app_label, latest_name), (app_label, previous_name)) from graph."""
    graph = loader.graph
    app_nodes = sorted(node for node in graph.nodes if node[0] == app_label)
    if len(app_nodes) < 2:
        raise ValueError(f"App {app_label} has fewer than 2 migrations in graph")
    return app_nodes[-1], app_nodes[-2]


def _rm_db() -> None:
    db_path = REPO_ROOT / "db.sqlite3"
    if db_path.exists():
        db_path.unlink()


def _migrate_all_once() -> None:
    _rm_db()
    print("[init] Applying all migrations on fresh database ...")
    call_command("migrate", "--run-syncdb", verbosity=1)
    print("[init] All migrations applied.\n")


def _current_targets(app_label: str) -> set[str]:
    """Return the set of applied migration names for an app."""
    from django.db.migrations.recorder import MigrationRecorder

    return {
        row[0]
        for row in MigrationRecorder.Migration.objects.filter(app=app_label)
        .order_by("name")
        .values_list("name", flat=True)
    }


def _print_error(msg: str) -> None:
    print(f"❌ {msg}")


def _validate_latest_applied(
    app: str, latest_name: str, before_rollback: set[str]
) -> bool:
    if latest_name not in before_rollback:
        _print_error(
            f"VALIDATION FAILED in {app}: latest migration "
            f"{latest_name} not applied before rollback"
        )
        return False
    return True


def _validate_previous_in_graph(
    previous_node: tuple[str, str], loader: MigrationLoader
) -> bool:
    if previous_node not in loader.graph.nodes:
        previous_name = previous_node[1]
        _print_error(
            f"VALIDATION FAILED: previous migration "
            f"{previous_name} not found in graph"
        )
        return False
    return True


def _rollback(app: str, previous_name: str) -> bool:
    print(f"[{app}] Rolling back to {previous_name} ...")
    try:
        call_command("migrate", app, previous_name, verbosity=1)
    except IrreversibleError:
        _print_error(
            f"IRREVERSIBLE MIGRATION DETECTED in {app}: "
            f"cannot rollback to {previous_name}"
        )
        return False
    except Exception as exc:
        _print_error(f"ROLLBACK FAILED in {app}: {type(exc).__name__}: {exc}")
        return False
    return True


def _validate_latest_not_rolled_back(
    app: str, latest_name: str, after_rollback: set[str]
) -> bool:
    if latest_name in after_rollback:
        _print_error(
            f"ROLLBACK VALIDATION FAILED in {app}: latest migration "
            f"{latest_name} still applied after rollback"
        )
        return False
    return True


def _reapply(app: str) -> bool:
    print(f"[{app}] Re-applying migrations forward ...")
    try:
        call_command("migrate", app, verbosity=1)
    except IrreversibleError:
        _print_error(
            f"IRREVERSIBLE MIGRATION DETECTED in {app}: "
            f"cannot re-apply after rollback"
        )
        return False
    except Exception as exc:
        _print_error(f"RE-APPLY FAILED in {app}: {type(exc).__name__}: {exc}")
        return False
    return True


def _validate_latest_reapplied(
    app: str, latest_name: str, after_reapply: set[str]
) -> bool:
    if latest_name not in after_reapply:
        _print_error(
            f"RE-APPLY VALIDATION FAILED in {app}: latest migration "
            f"{latest_name} not applied after re-apply"
        )
        return False
    return True


def _print_summary(
    project_apps: list[str], tested: int, skipped: int, failed: int
) -> int:
    print("\n" + "=" * 60)
    print(
        f"Summary: apps={len(project_apps)} "
        f"tested={tested} skipped={skipped} failed={failed}"
    )
    if failed:
        print("❌ Migration rollback validation FAILED")
        return 1
    if tested == 0:
        print("⚠️  No apps with >=2 migrations were found to test")
        return 0
    print("✅ All migration rollback tests passed")
    return 0


def main() -> int:
    print("=" * 80)
    print("  MIGRATION ROLLBACK VALIDATION — RentSecure Backend")
    print("=" * 80)
    print("Optimization: one fresh database initialization, apply once, then")
    print("rollback/re-apply per app to minimize runtime.\n")

    project_apps = _project_apps()
    print(f"Discovered project apps with migrations: {project_apps}\n")

    loader = MigrationLoader(connection=None)

    _migrate_all_once()

    tested = 0
    failed = 0
    skipped = 0

    for app in project_apps:
        try:
            latest_node, previous_node = _graph_info(app, loader)
        except ValueError as exc:
            print(f"SKIP: {app} — {exc}")
            skipped += 1
            continue

        tested += 1
        latest_name = latest_node[1]
        previous_name = previous_node[1]

        print("=" * 60)
        print(f"App: {app}")
        print(f"Latest migration:   {latest_name}")
        print(f"Previous migration: {previous_name}")
        print("=" * 60)

        # Pre-rollback validation
        before_rollback = _current_targets(app)
        if not _validate_latest_applied(app, latest_name, before_rollback):
            failed += 1
            continue
        if not _validate_previous_in_graph(previous_node, loader):
            failed += 1
            continue

        # Rollback one migration
        if not _rollback(app, previous_name):
            failed += 1
            continue

        # Post-rollback validation
        after_rollback = _current_targets(app)
        if not _validate_latest_not_rolled_back(app, latest_name, after_rollback):
            failed += 1
            continue

        # Re-apply forward to latest
        if not _reapply(app):
            failed += 1
            continue

        # Post-re-apply validation
        after_reapply = _current_targets(app)
        if not _validate_latest_reapplied(app, latest_name, after_reapply):
            failed += 1
            continue

        print(f"✅ {app} rollback test passed")

    return _print_summary(project_apps, tested, skipped, failed)


if __name__ == "__main__":
    sys.exit(main())
