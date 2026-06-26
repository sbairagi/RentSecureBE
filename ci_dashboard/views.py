"""
CI Dashboard Views.

Provides pages for:
- /ci/ (dashboard)
- /ci/run/ (run workflow)
- /ci/history/ (execution history)
- /ci/workflows/ (available workflows)
- /ci/logs/<run_id>/ (logs with SSE streaming)
- /ci/job/<job_run_id>/ (job detail)
- /ci/search/ (search workflow runs)
- /ci/rerun/<run_id>/ (rerun failed workflow)
- /ci/download/<run_id>/ (download logs)
- /ci/export/<run_id>/ (export as PDF)
"""

import json
import logging
import threading
import time
from datetime import timedelta
from pathlib import Path

from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from ci_dashboard.executor import ExecutionEngine
from ci_dashboard.models import (
    JobRun,
    LogEntry,
    StepRun,
    WorkflowDefinition,
    WorkflowRun,
)
from ci_dashboard.workflow_parser import WorkflowParser

logger = logging.getLogger(__name__)


def _get_parser() -> WorkflowParser:
    return WorkflowParser()


def _get_workflows() -> dict[str, Path]:
    return _get_parser().discover_workflows()


def _build_context(extra: dict | None = None) -> dict:
    """Build common template context."""
    workflows = _get_parser().parse_all()
    recent_runs = WorkflowRun.objects.all()[:20]
    context = {
        "recent_runs": recent_runs,
        "workflows": workflows,
        "total_runs": WorkflowRun.objects.count(),
        "passed_runs": WorkflowRun.objects.filter(
            status=WorkflowRun.STATUS_PASSED
        ).count(),
        "failed_runs": WorkflowRun.objects.filter(
            status=WorkflowRun.STATUS_FAILED
        ).count(),
        "running_runs": WorkflowRun.objects.filter(
            status=WorkflowRun.STATUS_RUNNING
        ).count(),
        "avg_duration": _get_avg_duration(),
        "success_rate": _get_success_rate(),
    }
    if extra:
        context.update(extra)
    return context


def _get_avg_duration() -> timedelta | None:
    """Calculate average duration of completed runs."""
    runs = WorkflowRun.objects.filter(
        status__in=[WorkflowRun.STATUS_PASSED, WorkflowRun.STATUS_FAILED],
        duration__isnull=False,
    )
    if not runs.exists():
        return None
    total = sum((r.duration for r in runs), timedelta())
    return total / runs.count()


def _get_success_rate() -> float:
    """Calculate success rate percentage."""
    total = WorkflowRun.objects.filter(
        status__in=[WorkflowRun.STATUS_PASSED, WorkflowRun.STATUS_FAILED]
    ).count()
    if total == 0:
        return 0.0
    passed = WorkflowRun.objects.filter(status=WorkflowRun.STATUS_PASSED).count()
    return round((passed / total) * 100, 1)


def dashboard(request):
    """Main dashboard page showing recent workflow runs with metrics."""
    workflows = _get_parser().parse_all()
    recent_runs = WorkflowRun.objects.all()

    # Search and filter
    search_query = request.GET.get("q", "").strip()
    status_filter = request.GET.get("status", "").strip()
    workflow_filter = request.GET.get("workflow", "").strip()

    if search_query:
        recent_runs = recent_runs.filter(
            workflow_name__icontains=search_query
        ) | recent_runs.filter(commit_sha__icontains=search_query)

    if status_filter:
        recent_runs = recent_runs.filter(status=status_filter)

    if workflow_filter:
        recent_runs = recent_runs.filter(workflow_file=workflow_filter)

    recent_runs = recent_runs.order_by("-created_at")[:20]

    context = _build_context(
        {
            "page_title": "CI Dashboard",
            "recent_runs": recent_runs,
            "search_query": search_query,
            "status_filter": status_filter,
            "workflow_filter": workflow_filter,
            "workflow_files": list(workflows.keys()),
        }
    )
    return render(request, "ci_dashboard/dashboard.html", context)


def workflow_list(request):
    """List all available workflows parsed from .github/workflows/."""
    parser = _get_parser()
    workflows = parser.parse_all()

    search_query = request.GET.get("q", "").strip()
    if search_query:
        filtered = {}
        for name, wf in workflows.items():
            if (
                search_query.lower() in wf.name.lower()
                or search_query.lower() in name.lower()
            ):
                filtered[name] = wf
        workflows = filtered

    context = _build_context(
        {
            "page_title": "Workflows",
            "workflows": workflows,
            "search_query": search_query,
        }
    )
    return render(request, "ci_dashboard/workflows.html", context)


def history(request):
    """Show execution history with filters."""
    runs = WorkflowRun.objects.all()

    search_query = request.GET.get("q", "").strip()
    status_filter = request.GET.get("status", "").strip()
    workflow_filter = request.GET.get("workflow", "").strip()

    if search_query:
        runs = runs.filter(workflow_name__icontains=search_query) | runs.filter(
            commit_sha__icontains=search_query
        )

    if status_filter:
        runs = runs.filter(status=status_filter)

    if workflow_filter:
        runs = runs.filter(workflow_file=workflow_filter)

    runs = runs.order_by("-created_at")[:100]

    context = _build_context(
        {
            "page_title": "Execution History",
            "runs": runs,
            "search_query": search_query,
            "status_filter": status_filter,
            "workflow_filter": workflow_filter,
            "workflow_files": [w.file_path for w in WorkflowDefinition.objects.all()],
        }
    )
    return render(request, "ci_dashboard/history.html", context)


def run_workflow(request):
    """Trigger a workflow run."""
    if request.method == "POST":
        workflow_file = request.POST.get("workflow_file", "")
        if not workflow_file:
            from django.http import HttpResponseBadRequest

            return HttpResponseBadRequest("workflow_file required")

        parser = _get_parser()
        workflow_path = parser.WORKFLOWS_DIR / workflow_file
        if not workflow_path.exists():
            from django.http import HttpResponseNotFound

            return HttpResponseNotFound("Workflow file not found")

        workflow = parser.parse_file(workflow_path)

        # Create WorkflowRun
        workflow_run = WorkflowRun.objects.create(
            workflow_file=workflow_file,
            workflow_name=workflow.name,
            triggered_by="manual (dashboard)",
            trigger_event="workflow_dispatch",
            status=WorkflowRun.STATUS_QUEUED,
        )

        # Execute in background thread
        engine = ExecutionEngine(workflow_run, workflow)

        def _run() -> None:
            engine.execute()

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()

        from django.shortcuts import redirect

        return redirect("ci_dashboard:logs", run_id=workflow_run.id)

    # GET: show run page or auto-run if workflow specified
    parser = _get_parser()
    workflows = parser.discover_workflows()

    # Check for ?workflow= query param to auto-trigger
    auto_workflow = request.GET.get("workflow", "").strip()
    if auto_workflow and (parser.WORKFLOWS_DIR / auto_workflow).exists():
        workflow_path = parser.WORKFLOWS_DIR / auto_workflow
        workflow = parser.parse_file(workflow_path)
        workflow_run = WorkflowRun.objects.create(
            workflow_file=auto_workflow,
            workflow_name=workflow.name,
            triggered_by="manual (dashboard)",
            trigger_event="workflow_dispatch",
            status=WorkflowRun.STATUS_QUEUED,
        )
        engine = ExecutionEngine(workflow_run, workflow)
        thread = threading.Thread(target=engine.execute, daemon=True)
        thread.start()
        from django.shortcuts import redirect

        return redirect("ci_dashboard:logs", run_id=workflow_run.id)

    context = _build_context(
        {
            "page_title": "Run Workflow",
            "workflow_files": [p.name for p in workflows],
        }
    )
    return render(request, "ci_dashboard/run.html", context)


def rerun_workflow(request, run_id: str):
    """Rerun a failed workflow."""
    if request.method == "POST":
        original_run = get_object_or_404(WorkflowRun, id=run_id)
        parser = _get_parser()
        workflow_path = parser.WORKFLOWS_DIR / original_run.workflow_file
        if not workflow_path.exists():
            from django.http import HttpResponseNotFound

            return HttpResponseNotFound("Workflow file not found")

        workflow = parser.parse_file(workflow_path)

        workflow_run = WorkflowRun.objects.create(
            workflow_file=original_run.workflow_file,
            workflow_name=original_run.workflow_name,
            triggered_by="rerun",
            trigger_event="workflow_dispatch",
            branch=original_run.branch,
            commit_sha=original_run.commit_sha,
            status=WorkflowRun.STATUS_QUEUED,
        )

        engine = ExecutionEngine(workflow_run, workflow)

        def _run() -> None:
            engine.execute()

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()

        from django.shortcuts import redirect

        return redirect("ci_dashboard:logs", run_id=workflow_run.id)

    from django.shortcuts import redirect

    return redirect("ci_dashboard:history")


def job_detail(request, job_run_id: str):
    """Show details for a specific job run, including nested reusable workflow jobs."""
    job_run = get_object_or_404(JobRun, id=job_run_id)

    nested_jobs = JobRun.objects.filter(
        workflow_run=job_run.workflow_run,
        job_id__startswith=f"{job_run.job_id}.",
    ).order_by("created_at")

    context = _build_context(
        {
            "page_title": f"Job: {job_run.name}",
            "job_run": job_run,
            "steps": job_run.steps.all(),
            "logs": job_run.log_entries.all()[:500],
            "nested_jobs": nested_jobs,
        }
    )
    return render(request, "ci_dashboard/job_detail.html", context)


def logs(request, run_id: str):
    """Show logs for a workflow run with full job hierarchy."""
    workflow_run = get_object_or_404(WorkflowRun, id=run_id)
    job_runs = workflow_run.jobs.select_related().all()
    log_entries = workflow_run.log_entries.all()[:2000]

    # Build hierarchical job structure from workflow definition
    workflow_structure = []
    parser = _get_parser()
    workflow_def = parser.get_workflow(workflow_run.workflow_file)

    if workflow_def:
        # Create a map of actual job runs by job_id
        job_run_map = {jr.job_id: jr for jr in job_runs}

        for job_id in workflow_def.get_stage_order():
            job_def = workflow_def.jobs.get(job_id)
            if not job_def:
                continue

            # Get or create placeholder for parent job
            parent_job_run = job_run_map.get(job_id)
            parent_status = (
                parent_job_run.status if parent_job_run else JobRun.STATUS_QUEUED
            )
            parent_name = job_def.name

            # Extract stage name
            stage_name = (
                parent_name.split("│")[0].strip() if "│" in parent_name else parent_name
            )

            children = []
            # If this is a reusable workflow, parse it to get inner jobs
            if job_def.is_reusable and job_def.raw.get("uses"):
                uses_path = job_def.raw["uses"]
                ref_path = (Path.cwd() / uses_path).resolve()
                if ref_path.exists():
                    try:
                        ref_workflow = parser.parse_file(ref_path)
                        for ref_job_id in ref_workflow.get_stage_order():
                            ref_job_def = ref_workflow.jobs.get(ref_job_id)
                            if not ref_job_def:
                                continue
                            child_job_id = f"{job_id}.{ref_job_id}"
                            child_job_run = job_run_map.get(child_job_id)
                            child_status = (
                                child_job_run.status
                                if child_job_run
                                else JobRun.STATUS_QUEUED
                            )
                            children.append(
                                {
                                    "job_id": child_job_id,
                                    "name": ref_job_def.name,
                                    "status": child_status,
                                    "job_run": child_job_run,
                                }
                            )
                    except Exception as exc:
                        logger.debug(
                            "Failed to parse reusable workflow for child jobs: %s",
                            exc,
                        )

            workflow_structure.append(
                {
                    "job_id": job_id,
                    "name": parent_name,
                    "stage": stage_name,
                    "status": parent_status,
                    "job_run": parent_job_run,
                    "children": children,
                }
            )

    context = _build_context(
        {
            "page_title": f"Logs: {workflow_run.workflow_name}",
            "workflow_run": workflow_run,
            "jobs": job_runs,
            "log_entries": log_entries,
            "workflow_structure": workflow_structure,
        }
    )
    return render(request, "ci_dashboard/logs.html", context)


def cancel_workflow(request, run_id: str):
    """Cancel a running workflow."""
    if request.method == "POST":
        workflow_run = get_object_or_404(WorkflowRun, id=run_id)
        if workflow_run.status in (
            WorkflowRun.STATUS_QUEUED,
            WorkflowRun.STATUS_RUNNING,
        ):
            workflow_run.status = WorkflowRun.STATUS_CANCELLED
            workflow_run.conclusion = "cancelled"
            workflow_run.finished_at = timezone.now()
            if workflow_run.started_at:
                workflow_run.duration = (
                    workflow_run.finished_at - workflow_run.started_at
                )
            workflow_run.save()

            # Cancel all running jobs
            for job in workflow_run.jobs.filter(status=JobRun.STATUS_RUNNING):
                job.status = JobRun.STATUS_CANCELLED
                job.finished_at = timezone.now()
                if job.started_at:
                    job.duration = job.finished_at - job.started_at
                job.save()
                for step in job.steps.filter(status=StepRun.STATUS_RUNNING):
                    step.status = StepRun.STATUS_CANCELLED
                    step.finished_at = timezone.now()
                    if step.started_at:
                        step.duration = step.finished_at - step.started_at
                    step.save()

            LogEntry.objects.create(
                workflow_run=workflow_run,
                content="::warning:: Workflow cancelled by user",
                stream=LogEntry.STREAM_SYSTEM,
            )

    from django.shortcuts import redirect

    return redirect("ci_dashboard:logs", run_id=run_id)


def sse_logs(request, run_id: str):
    """Server-Sent Events endpoint for live log streaming."""
    workflow_run = get_object_or_404(WorkflowRun, id=run_id)

    def event_stream():
        last_id = request.GET.get("last_id", "0")
        try:
            last_id_int = int(last_id)
        except ValueError:
            last_id_int = 0

        def _format_log_entry(entry: LogEntry) -> str:
            data = {
                "id": entry.id,
                "content": entry.content,
                "stream": entry.stream,
                "timestamp": entry.timestamp.isoformat(),
            }
            return f"event: log\ndata: {json.dumps(data)}\n\n"

        while True:
            workflow_run.refresh_from_db()
            if workflow_run.status not in (
                WorkflowRun.STATUS_QUEUED,
                WorkflowRun.STATUS_RUNNING,
            ):
                remaining = LogEntry.objects.filter(
                    workflow_run=workflow_run,
                    pk__gt=last_id_int,
                ).order_by("timestamp")
                for entry in remaining:
                    yield f"id: {entry.id}\n"
                    yield _format_log_entry(entry)
                    last_id_int = entry.id
                yield "event: end\ndata: {}\n\n"
                break

            new_logs = LogEntry.objects.filter(
                workflow_run=workflow_run,
                pk__gt=last_id_int,
            ).order_by("timestamp")

            for entry in new_logs:
                yield f"id: {entry.id}\n"
                yield _format_log_entry(entry)
                last_id_int = entry.id

            time.sleep(0.5)

    response = StreamingHttpResponse(
        event_stream(),
        content_type="text/event-stream",
    )
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response


def workflow_graph(request, run_id: str):
    """Render workflow dependency graph visualization (GitHub Actions style)."""
    from collections import OrderedDict

    workflow_run = get_object_or_404(WorkflowRun, id=run_id)
    jobs = workflow_run.jobs.all()

    # Group jobs by stage based on name prefix
    stages = OrderedDict()
    for job in jobs:
        # Extract stage from job name
        # e.g. "Stage 1-2 | Setup & Code Quality" -> "Stage 1-2"
        stage_name = job.name.split("│")[0].strip() if "│" in job.name else job.name
        if stage_name not in stages:
            stages[stage_name] = []
        stages[stage_name].append(job)

    context = _build_context(
        {
            "page_title": f"Graph: {workflow_run.workflow_name}",
            "workflow_run": workflow_run,
            "stages": stages,
            "jobs": jobs,
        }
    )
    return render(request, "ci_dashboard/graph.html", context)


def workflow_graph_json(request, run_id: str):
    """Return job dependency graph as JSON for API consumers."""
    workflow_run = get_object_or_404(WorkflowRun, id=run_id)
    jobs = workflow_run.jobs.all()

    nodes = []
    edges = []

    for job in jobs:
        nodes.append(
            {
                "id": str(job.id),
                "job_id": job.job_id,
                "name": job.name,
                "status": job.status,
                "needs": job.needs,
            }
        )
        for dep in job.needs:
            edges.append({"from": dep, "to": job.job_id})

    from django.http import JsonResponse

    return JsonResponse(
        {"nodes": nodes, "edges": edges, "workflow": workflow_run.workflow_name}
    )


def download_logs(request, run_id: str):
    """Download logs as text file."""
    workflow_run = get_object_or_404(WorkflowRun, id=run_id)
    log_entries = workflow_run.log_entries.all().order_by("timestamp")

    content_lines = [
        f"Workflow: {workflow_run.workflow_name}",
        f"Run ID: {workflow_run.id}",
        f"Status: {workflow_run.get_status_display()}",
        f"Branch: {workflow_run.branch}",
        f"Commit: {workflow_run.commit_sha}",
        f"Started: {workflow_run.started_at}",
        f"Finished: {workflow_run.finished_at}",
        "=" * 80,
        "",
    ]

    for entry in log_entries:
        timestamp = entry.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        content_lines.append(f"[{timestamp}] [{entry.stream.upper()}] {entry.content}")

    content = "\n".join(content_lines)

    from django.http import HttpResponse

    response = HttpResponse(content, content_type="text/plain")
    response["Content-Disposition"] = (
        f"attachment; filename=ci-logs-{workflow_run.id.hex[:8]}.txt"
    )
    return response


def export_pdf(request, run_id: str):
    """Export workflow run as PDF (browser print-to-PDF)."""
    workflow_run = get_object_or_404(WorkflowRun, id=run_id)
    jobs = workflow_run.jobs.all()
    log_entries = workflow_run.log_entries.all()[:1000]

    context = _build_context(
        {
            "page_title": f"PDF Export: {workflow_run.workflow_name}",
            "workflow_run": workflow_run,
            "jobs": jobs,
            "log_entries": log_entries,
            "is_pdf": True,
        }
    )
    return render(request, "ci_dashboard/pdf_export.html", context)
