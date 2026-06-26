"""
CI Dashboard Tests.

Comprehensive test coverage for:
- Workflow parsing
- Model creation and relationships
- Execution engine
- Views and URL routing
- Dependency graph generation
- SSE streaming
"""

import json
from pathlib import Path

import pytest
from django.test import TestCase
from django.urls import reverse

from ci_dashboard.executor import ExecutionEngine
from ci_dashboard.models import (
    JobRun,
    LogEntry,
    StepRun,
    WorkflowDefinition,
    WorkflowRun,
)
from ci_dashboard.workflow_parser import Job, Step, Workflow, WorkflowParser

WORKFLOWS_DIR = Path(".github/workflows")


class TestWorkflowParser(TestCase):
    """Test workflow YAML parsing."""

    def setUp(self) -> None:
        self.parser = WorkflowParser()

    def test_discover_workflows(self) -> None:
        workflows = self.parser.discover_workflows()
        assert len(workflows) > 0
        assert any(w.name == "ci.yml" for w in workflows)

    def test_parse_ci_workflow(self) -> None:
        ci_path = WORKFLOWS_DIR / "ci.yml"
        if not ci_path.exists():
            pytest.skip("ci.yml not found")
        workflow = self.parser.parse_file(ci_path)
        assert workflow.name == "CI Pipeline"
        assert len(workflow.jobs) > 0
        assert "lint" in workflow.jobs

    def test_parse_lint_workflow(self) -> None:
        lint_path = WORKFLOWS_DIR / "lint.yml"
        if not lint_path.exists():
            pytest.skip("lint.yml not found")
        workflow = self.parser.parse_file(lint_path)
        assert "pre-commit" in workflow.jobs
        assert "black" in workflow.jobs
        assert "ruff" in workflow.jobs
        assert "pylint" in workflow.jobs
        assert "mypy" in workflow.jobs
        assert "vulture" in workflow.jobs

    def test_parse_security_workflow(self) -> None:
        security_path = WORKFLOWS_DIR / "security.yml"
        if not security_path.exists():
            pytest.skip("security.yml not found")
        workflow = self.parser.parse_file(security_path)
        assert "bandit" in workflow.jobs
        assert "semgrep" in workflow.jobs
        assert "trivy" in workflow.jobs
        assert "codeql" in workflow.jobs

    def test_job_dependencies(self) -> None:
        ci_path = WORKFLOWS_DIR / "ci.yml"
        if not ci_path.exists():
            pytest.skip("ci.yml not found")
        workflow = self.parser.parse_file(ci_path)
        lint_job = workflow.jobs.get("lint")
        assert lint_job is not None
        assert lint_job.needs == []

        test_job = workflow.jobs.get("test")
        if test_job:
            assert "lint" in test_job.needs

    def test_stage_order(self) -> None:
        ci_path = WORKFLOWS_DIR / "ci.yml"
        if not ci_path.exists():
            pytest.skip("ci.yml not found")
        workflow = self.parser.parse_file(ci_path)
        order = workflow.get_stage_order()
        assert "lint" in order
        lint_idx = order.index("lint")
        test_idx = order.index("test")
        assert lint_idx < test_idx

    def test_reusable_workflow_detection(self) -> None:
        ci_path = WORKFLOWS_DIR / "ci.yml"
        if not ci_path.exists():
            pytest.skip("ci.yml not found")
        workflow = self.parser.parse_file(ci_path)
        lint_job = workflow.jobs.get("lint")
        assert lint_job is not None
        # ci.yml uses reusable workflows
        assert len(lint_job.steps) == 0  # uses: doesn't have local steps


class TestWorkflowModels(TestCase):
    """Test database models."""

    def test_create_workflow_run(self) -> None:
        run = WorkflowRun.objects.create(
            workflow_file="ci.yml",
            workflow_name="CI Pipeline",
            status=WorkflowRun.STATUS_QUEUED,
        )
        assert run.id is not None
        assert str(run) == f"CI Pipeline [{run.id.hex[:8]}] - queued"

    def test_create_job_run(self) -> None:
        wf_run = WorkflowRun.objects.create(
            workflow_file="ci.yml",
            workflow_name="CI Pipeline",
        )
        job_run = JobRun.objects.create(
            workflow_run=wf_run,
            job_id="lint",
            name="Lint",
            status=JobRun.STATUS_RUNNING,
        )
        assert job_run.id is not None
        assert str(job_run) == "Lint [running]"

    def test_create_step_run(self) -> None:
        wf_run = WorkflowRun.objects.create(
            workflow_file="ci.yml",
            workflow_name="CI Pipeline",
        )
        job_run = JobRun.objects.create(
            workflow_run=wf_run,
            job_id="lint",
            name="Lint",
        )
        step_run = StepRun.objects.create(
            job_run=job_run,
            step_id="pre-commit",
            name="Pre-commit",
            status=StepRun.STATUS_PASSED,
            exit_code=0,
        )
        assert step_run.id is not None

    def test_create_log_entry(self) -> None:
        wf_run = WorkflowRun.objects.create(
            workflow_file="ci.yml",
            workflow_name="CI Pipeline",
        )
        log = LogEntry.objects.create(
            workflow_run=wf_run,
            content="Test log line",
            stream=LogEntry.STREAM_STDOUT,
        )
        assert log.id is not None
        assert log.content == "Test log line"

    def test_workflow_run_success_rate(self) -> None:
        wf_run = WorkflowRun.objects.create(
            workflow_file="ci.yml",
            workflow_name="CI Pipeline",
            jobs_total=10,
            jobs_completed=8,
            jobs_failed=2,
        )
        assert wf_run.success_rate == 80.0

    def test_workflow_run_is_active(self) -> None:
        wf_running = WorkflowRun.objects.create(
            workflow_file="ci.yml",
            workflow_name="CI Pipeline",
            status=WorkflowRun.STATUS_RUNNING,
        )
        assert wf_running.is_active is True

        wf_passed = WorkflowRun.objects.create(
            workflow_file="ci.yml",
            workflow_name="CI Pipeline",
            status=WorkflowRun.STATUS_PASSED,
        )
        assert wf_passed.is_active is False


class TestWorkflowDefinition(TestCase):
    """Test cached workflow definitions."""

    def test_create_definition(self) -> None:
        wf_def = WorkflowDefinition.objects.create(
            file_path=".github/workflows/ci.yml",
            workflow_name="CI Pipeline",
            raw_yaml="name: CI Pipeline\n'on':\n  push:\n    branches: [main]",
            jobs={"lint": {"runs-on": "ubuntu-latest"}},
            on_trigger={"push": {"branches": ["main"]}},
        )
        assert wf_def.job_ids == ["lint"]

    def test_topological_sort(self) -> None:
        wf_def = WorkflowDefinition.objects.create(
            file_path=".github/workflows/ci.yml",
            workflow_name="CI Pipeline",
            jobs={
                "lint": {"needs": []},
                "test": {"needs": ["lint"]},
                "security": {"needs": ["test"]},
            },
        )
        order = wf_def.stage_order
        assert order.index("lint") < order.index("test")
        assert order.index("test") < order.index("security")


class TestViews(TestCase):
    """Test views."""

    def test_dashboard_view(self) -> None:
        response = self.client.get(reverse("ci_dashboard:dashboard"))
        assert response.status_code == 200
        assert "CI Dashboard" in response.content.decode()

    def test_workflow_list_view(self) -> None:
        response = self.client.get(reverse("ci_dashboard:workflows"))
        assert response.status_code == 200

    def test_history_view(self) -> None:
        response = self.client.get(reverse("ci_dashboard:history"))
        assert response.status_code == 200

    def test_run_view_get(self) -> None:
        response = self.client.get(reverse("ci_dashboard:run"))
        assert response.status_code == 200

    def test_sse_logs_view(self) -> None:
        wf_run = WorkflowRun.objects.create(
            workflow_file="ci.yml",
            workflow_name="CI Pipeline",
            status=WorkflowRun.STATUS_RUNNING,
        )
        response = self.client.get(
            reverse("ci_dashboard:sse_logs", kwargs={"run_id": wf_run.id})
        )
        assert response.status_code == 200
        assert response["content-type"] == "text/event-stream"

    def test_download_logs_view(self) -> None:
        wf_run = WorkflowRun.objects.create(
            workflow_file="ci.yml",
            workflow_name="CI Pipeline",
        )
        LogEntry.objects.create(
            workflow_run=wf_run,
            content="Test log",
            stream=LogEntry.STREAM_STDOUT,
        )
        response = self.client.get(
            reverse("ci_dashboard:download_logs", kwargs={"run_id": wf_run.id})
        )
        assert response.status_code == 200
        assert response["content-type"] == "text/plain"

    def test_cancel_workflow(self) -> None:
        wf_run = WorkflowRun.objects.create(
            workflow_file="ci.yml",
            workflow_name="CI Pipeline",
            status=WorkflowRun.STATUS_RUNNING,
        )
        response = self.client.post(
            reverse("ci_dashboard:cancel", kwargs={"run_id": wf_run.id})
        )
        assert response.status_code == 302
        wf_run.refresh_from_db()
        assert wf_run.status == WorkflowRun.STATUS_CANCELLED


class TestExecutionEngine(TestCase):
    """Test execution engine."""

    def test_execute_simple_workflow(self) -> None:
        """Test executing a simple workflow with a single local step."""
        # Create a minimal workflow
        workflow = Workflow(
            name="Test Workflow",
            file_path="test.yml",
            on_trigger={"workflow_dispatch": {}},
            jobs={
                "test-job": Job(
                    job_id="test-job",
                    name="Test Job",
                    runs_on=["ubuntu-latest"],
                    needs=[],
                    steps=[
                        Step(
                            step_id="echo-step",
                            name="Echo Hello",
                            run="echo 'Hello World'",
                        )
                    ],
                )
            },
        )

        wf_run = WorkflowRun.objects.create(
            workflow_file="test.yml",
            workflow_name="Test Workflow",
            status=WorkflowRun.STATUS_QUEUED,
        )

        engine = ExecutionEngine(wf_run, workflow)
        engine.execute()

        wf_run.refresh_from_db()
        assert wf_run.status == WorkflowRun.STATUS_PASSED
        assert wf_run.jobs_completed == 1

    def test_execute_failing_workflow(self) -> None:
        """Test that a failing step marks the workflow as failed."""
        workflow = Workflow(
            name="Test Workflow",
            file_path="test.yml",
            on_trigger={"workflow_dispatch": {}},
            jobs={
                "fail-job": Job(
                    job_id="fail-job",
                    name="Fail Job",
                    runs_on=["ubuntu-latest"],
                    needs=[],
                    steps=[
                        Step(
                            step_id="fail-step",
                            name="Fail Step",
                            run="exit 1",
                        )
                    ],
                )
            },
        )

        wf_run = WorkflowRun.objects.create(
            workflow_file="test.yml",
            workflow_name="Test Workflow",
            status=WorkflowRun.STATUS_QUEUED,
        )

        engine = ExecutionEngine(wf_run, workflow)
        engine.execute()

        wf_run.refresh_from_db()
        assert wf_run.status == WorkflowRun.STATUS_FAILED
        assert wf_run.jobs_failed == 1

    def test_dependency_enforcement(self) -> None:
        """Test that jobs wait for dependencies."""
        workflow = Workflow(
            name="Test Workflow",
            file_path="test.yml",
            on_trigger={"workflow_dispatch": {}},
            jobs={
                "first": Job(
                    job_id="first",
                    name="First",
                    runs_on=["ubuntu-latest"],
                    needs=[],
                    steps=[Step(step_id="s1", name="Step 1", run="echo first")],
                ),
                "second": Job(
                    job_id="second",
                    name="Second",
                    runs_on=["ubuntu-latest"],
                    needs=["first"],
                    steps=[Step(step_id="s2", name="Step 2", run="echo second")],
                ),
            },
        )

        wf_run = WorkflowRun.objects.create(
            workflow_file="test.yml",
            workflow_name="Test Workflow",
            status=WorkflowRun.STATUS_QUEUED,
        )

        engine = ExecutionEngine(wf_run, workflow)
        engine.execute()

        wf_run.refresh_from_db()
        assert wf_run.jobs_completed == 2
        assert wf_run.status == WorkflowRun.STATUS_PASSED


class TestWorkflowGraph(TestCase):
    """Test dependency graph generation."""

    def test_graph_json(self) -> None:
        wf_run = WorkflowRun.objects.create(
            workflow_file="ci.yml",
            workflow_name="CI Pipeline",
        )
        JobRun.objects.create(
            workflow_run=wf_run,
            job_id="lint",
            name="Lint",
            needs=[],
        )
        JobRun.objects.create(
            workflow_run=wf_run,
            job_id="test",
            name="Test",
            needs=["lint"],
        )

        response = self.client.get(
            reverse("ci_dashboard:graph_json", kwargs={"run_id": wf_run.id})
        )
        assert response.status_code == 200
        assert response["content-type"] == "application/json"
        data = json.loads(response.content)
        assert "nodes" in data
        assert "edges" in data
        assert len(data["nodes"]) == 2


class TestManagementCommand(TestCase):
    """Test management command."""

    def test_list_workflows(self) -> None:
        from io import StringIO

        from django.core.management import call_command

        out = StringIO()
        call_command("run_ci", "--list", stdout=out)
        output = out.getvalue()
        assert "Available workflows" in output or len(output) > 0
