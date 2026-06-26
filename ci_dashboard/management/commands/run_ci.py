"""
Django management command to run CI workflows from command line.

Usage:
    python manage.py run_ci --workflow ci.yml
    python manage.py run_ci --workflow lint.yml
    python manage.py run_ci --list
"""

import argparse
import sys

from django.core.management.base import BaseCommand

from ci_dashboard.executor import ExecutionEngine
from ci_dashboard.models import WorkflowRun
from ci_dashboard.workflow_parser import WorkflowParser


class Command(BaseCommand):
    help = "Run GitHub Actions workflows locally via the CI Dashboard engine"

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--workflow",
            type=str,
            help="Workflow filename (e.g., ci.yml)",
        )
        parser.add_argument(
            "--list",
            action="store_true",
            help="List available workflows",
        )

    def handle(self, *args: object, **options: object) -> None:
        parser = WorkflowParser()

        if options["list"]:
            workflows = parser.discover_workflows()
            self.stdout.write("Available workflows:")
            for wf in workflows:
                self.stdout.write(f"  - {wf.name}")
            return

        workflow_file = options.get("workflow")
        if not workflow_file:
            self.stderr.write("Error: --workflow is required (or use --list)")
            sys.exit(1)

        workflow_path = parser.WORKFLOWS_DIR / workflow_file
        if not workflow_path.exists():
            self.stderr.write(
                f"Error: Workflow '{workflow_file}' not found in .github/workflows/"
            )
            sys.exit(1)

        workflow = parser.parse_file(workflow_path)

        workflow_run = WorkflowRun.objects.create(
            workflow_file=workflow_file,
            workflow_name=workflow.name,
            triggered_by="cli",
            trigger_event="manual",
            status=WorkflowRun.STATUS_QUEUED,
        )

        self.stdout.write(f"Starting workflow: {workflow.name}")
        self.stdout.write(f"Run ID: {workflow_run.id}")

        engine = ExecutionEngine(workflow_run, workflow)
        engine.execute()

        workflow_run.refresh_from_db()
        self.stdout.write(
            f"Workflow finished: {workflow_run.get_status_display()} "
            f"in {workflow_run.duration or 'N/A'}"
        )

        if workflow_run.status == WorkflowRun.STATUS_FAILED:
            sys.exit(1)
