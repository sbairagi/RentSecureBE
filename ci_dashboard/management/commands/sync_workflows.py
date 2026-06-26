"""
Django management command to sync workflow definitions from .github/workflows/.

Usage:
    python manage.py sync_workflows
"""

from django.core.management.base import BaseCommand

from ci_dashboard.workflow_parser import WorkflowParser


class Command(BaseCommand):
    help = "Sync GitHub Actions workflow definitions to database"

    def handle(self, *args: object, **options: object) -> None:
        parser = WorkflowParser()
        definitions = parser.sync_to_db()
        self.stdout.write(f"Synced {len(definitions)} workflows:")
        for filename, wf_def in definitions.items():
            self.stdout.write(f"  - {wf_def.workflow_name} ({filename})")
