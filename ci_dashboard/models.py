"""
Database models for CI Dashboard.

Stores workflow runs, job runs, step runs, and log entries.
Mirrors GitHub Actions execution model with full audit trail.
"""

import uuid

from django.db import models
from django.db.models import JSONField
from django.urls import reverse


class WorkflowRun(models.Model):
    """Represents a single execution of a GitHub Actions workflow."""

    STATUS_QUEUED = "queued"
    STATUS_RUNNING = "running"
    STATUS_PASSED = "passed"
    STATUS_FAILED = "failed"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (STATUS_QUEUED, "Queued"),
        (STATUS_RUNNING, "Running"),
        (STATUS_PASSED, "Passed"),
        (STATUS_FAILED, "Failed"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow_file = models.CharField(max_length=255, db_index=True)
    workflow_name = models.CharField(max_length=255, blank=True)
    triggered_by = models.CharField(max_length=255, default="manual")
    trigger_event = models.CharField(max_length=50, default="workflow_dispatch")
    branch = models.CharField(max_length=255, blank=True, db_index=True)
    commit_sha = models.CharField(max_length=255, blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_QUEUED, db_index=True
    )
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    duration = models.DurationField(null=True, blank=True)
    conclusion = models.CharField(max_length=50, blank=True)
    jobs_total = models.IntegerField(default=0)
    jobs_completed = models.IntegerField(default=0)
    jobs_failed = models.IntegerField(default=0)
    meta = JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["workflow_file", "created_at"]),
            models.Index(fields=["branch", "created_at"]),
        ]

    def __str__(self) -> str:
        short_id = self.id.hex[:8]
        return (
            f"{self.workflow_name or self.workflow_file} [{short_id}] - "
            f"{self.status}"
        )

    def get_absolute_url(self) -> str:
        return reverse("ci_dashboard:logs", kwargs={"run_id": self.id})

    @property
    def short_id(self) -> str:
        return self.id.hex[:8]

    @property
    def success_rate(self) -> float:
        if self.jobs_total == 0:
            return 0.0
        return (self.jobs_completed / self.jobs_total) * 100

    @property
    def is_active(self) -> bool:
        return self.status in (self.STATUS_QUEUED, self.STATUS_RUNNING)


class JobRun(models.Model):
    """Represents a single job execution within a workflow run."""

    STATUS_QUEUED = "queued"
    STATUS_RUNNING = "running"
    STATUS_PASSED = "passed"
    STATUS_FAILED = "failed"
    STATUS_CANCELLED = "cancelled"
    STATUS_SKIPPED = "skipped"

    STATUS_CHOICES = [
        (STATUS_QUEUED, "Queued"),
        (STATUS_RUNNING, "Running"),
        (STATUS_PASSED, "Passed"),
        (STATUS_FAILED, "Failed"),
        (STATUS_CANCELLED, "Cancelled"),
        (STATUS_SKIPPED, "Skipped"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow_run = models.ForeignKey(
        WorkflowRun, related_name="jobs", on_delete=models.CASCADE
    )
    job_id = models.CharField(max_length=255, db_index=True)
    name = models.CharField(max_length=255, blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_QUEUED, db_index=True
    )
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    duration = models.DurationField(null=True, blank=True)
    exit_code = models.IntegerField(null=True, blank=True)
    runner_label = models.CharField(max_length=255, blank=True)
    needs = JSONField(default=list, blank=True)
    meta = JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["workflow_run", "status"]),
            models.Index(fields=["job_id", "workflow_run"]),
        ]

    def __str__(self) -> str:
        return f"{self.name or self.job_id} [{self.status}]"


class StepRun(models.Model):
    """Represents a single step execution within a job."""

    STATUS_QUEUED = "queued"
    STATUS_RUNNING = "running"
    STATUS_PASSED = "passed"
    STATUS_FAILED = "failed"
    STATUS_CANCELLED = "cancelled"
    STATUS_SKIPPED = "skipped"

    STATUS_CHOICES = [
        (STATUS_QUEUED, "Queued"),
        (STATUS_RUNNING, "Running"),
        (STATUS_PASSED, "Passed"),
        (STATUS_FAILED, "Failed"),
        (STATUS_CANCELLED, "Cancelled"),
        (STATUS_SKIPPED, "Skipped"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job_run = models.ForeignKey(JobRun, related_name="steps", on_delete=models.CASCADE)
    step_id = models.CharField(max_length=255, db_index=True)
    name = models.CharField(max_length=255, blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_QUEUED, db_index=True
    )
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    duration = models.DurationField(null=True, blank=True)
    exit_code = models.IntegerField(null=True, blank=True)
    command = models.TextField(blank=True)
    meta = JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["job_run", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.name or self.step_id} [{self.status}]"


class LogEntry(models.Model):
    """Individual log line from a job or step execution."""

    STREAM_STDOUT = "stdout"
    STREAM_STDERR = "stderr"
    STREAM_SYSTEM = "system"

    STREAM_CHOICES = [
        (STREAM_STDOUT, "Stdout"),
        (STREAM_STDERR, "Stderr"),
        (STREAM_SYSTEM, "System"),
    ]

    id = models.BigAutoField(primary_key=True)
    workflow_run = models.ForeignKey(
        WorkflowRun, related_name="log_entries", on_delete=models.CASCADE, null=True
    )
    job_run = models.ForeignKey(
        JobRun, related_name="log_entries", on_delete=models.CASCADE, null=True
    )
    step_run = models.ForeignKey(
        StepRun, related_name="log_entries", on_delete=models.CASCADE, null=True
    )
    content = models.TextField()
    stream = models.CharField(
        max_length=20, choices=STREAM_CHOICES, default=STREAM_STDOUT
    )
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    run_number = models.IntegerField(default=1)

    class Meta:
        ordering = ["timestamp"]
        indexes = [
            models.Index(fields=["workflow_run", "timestamp"]),
            models.Index(fields=["job_run", "timestamp"]),
            models.Index(fields=["step_run", "timestamp"]),
        ]

    def __str__(self) -> str:
        return f"[{self.stream}] {self.content[:80]}"


class WorkflowDefinition(models.Model):
    """Cached parsed workflow definition from GitHub Actions YAML."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file_path = models.CharField(max_length=255, unique=True, db_index=True)
    workflow_name = models.CharField(max_length=255)
    raw_yaml = models.TextField()
    parsed_json = JSONField(default=dict)
    jobs = JSONField(default=dict)
    on_trigger = JSONField(default=dict)
    last_synced_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["workflow_name"]

    def __str__(self) -> str:
        return self.workflow_name

    @property
    def job_ids(self) -> list[str]:
        return list(self.jobs.keys())

    @property
    def stage_order(self) -> list[str]:
        """Return jobs in dependency order."""
        return self._topological_sort(self.jobs)

    def _topological_sort(self, jobs: dict) -> list[str]:
        visited = set()
        result = []

        def visit(job_id: str) -> None:
            if job_id in visited:
                return
            visited.add(job_id)
            job_def = jobs.get(job_id, {})
            needs = job_def.get("needs", [])
            if isinstance(needs, str):
                needs = [needs]
            for dep in needs:
                if dep in jobs:
                    visit(dep)
            result.append(job_id)

        for job_id in jobs:
            visit(job_id)

        return result
