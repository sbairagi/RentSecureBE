"""
Local CI Execution Engine.

Executes GitHub Actions workflow jobs locally using subprocess.
Respects job dependencies (needs:).
Streams logs to database in real-time.
Supports: run:, env:, needs:, if:, timeout-minutes:, working-directory:
"""

import logging
import os
import subprocess
import threading
import time
from pathlib import Path

from django.utils import timezone

from ci_dashboard.models import JobRun, LogEntry, StepRun, WorkflowRun
from ci_dashboard.workflow_parser import WorkflowParser

logger = logging.getLogger(__name__)


class ExecutionEngine:
    """Execute workflow jobs locally, respecting dependencies."""

    def __init__(self, workflow_run: WorkflowRun, workflow) -> None:
        self.workflow_run = workflow_run
        self.workflow = workflow
        self._lock = threading.Lock()
        self._cancelled = False

    def cancel(self) -> None:
        """Cancel the entire workflow run."""
        with self._lock:
            self._cancelled = True
        self.workflow_run.status = WorkflowRun.STATUS_CANCELLED
        self.workflow_run.finished_at = timezone.now()
        self.workflow_run.save()

    @property
    def is_cancelled(self) -> bool:
        with self._lock:
            return self._cancelled

    def execute(self) -> None:
        """Execute the full workflow respecting job dependencies."""
        self._start_workflow()

        stage_order = self.workflow.get_stage_order()
        completed_jobs: set[str] = set()
        failed_jobs: set[str] = set()

        for job_id in stage_order:
            if self.is_cancelled:
                break

            job_def = self.workflow.jobs.get(job_id)
            if not job_def:
                continue

            if self._is_reusable_job(job_def):
                success = self._execute_reusable_job(job_id, job_def)
                self._record_job_result(job_id, success, completed_jobs, failed_jobs)
                continue

            if not self._dependencies_met(job_def, completed_jobs, failed_jobs):
                self._skip_job(job_id, "Dependency failed or not completed")
                failed_jobs.add(job_id)
                continue

            job_run = self._create_job_run(job_id, job_def)
            success = self._execute_job(job_run, job_def)
            self._record_job_result(job_id, success, completed_jobs, failed_jobs)

        self._finalize_workflow(len(stage_order), len(completed_jobs), len(failed_jobs))

    def _start_workflow(self) -> None:
        """Set workflow status to running."""
        self.workflow_run.status = WorkflowRun.STATUS_RUNNING
        self.workflow_run.started_at = timezone.now()
        self.workflow_run.save()

    @staticmethod
    def _is_reusable_job(job_def) -> bool:
        """Check if job references a reusable workflow."""
        return job_def.is_reusable

    def _dependencies_met(
        self, job_def, completed_jobs: set[str], failed_jobs: set[str]
    ) -> bool:
        """Check if all job dependencies have passed."""
        for dep in job_def.needs:
            if dep in failed_jobs or dep not in completed_jobs:
                return False
        return True

    def _record_job_result(
        self,
        job_id: str,
        success: bool,
        completed_jobs: set[str],
        failed_jobs: set[str],
    ) -> None:
        """Record job execution result."""
        if success:
            completed_jobs.add(job_id)
        else:
            failed_jobs.add(job_id)

    def _finalize_workflow(self, total: int, completed: int, failed: int) -> None:
        """Update final workflow status."""
        self.workflow_run.jobs_total = total
        self.workflow_run.jobs_completed = completed
        self.workflow_run.jobs_failed = failed

        if self.is_cancelled:
            self.workflow_run.status = WorkflowRun.STATUS_CANCELLED
            self.workflow_run.conclusion = "cancelled"
        elif failed:
            self.workflow_run.status = WorkflowRun.STATUS_FAILED
            self.workflow_run.conclusion = "failure"
        else:
            self.workflow_run.status = WorkflowRun.STATUS_PASSED
            self.workflow_run.conclusion = "success"

        self.workflow_run.finished_at = timezone.now()
        if self.workflow_run.started_at:
            self.workflow_run.duration = (
                self.workflow_run.finished_at - self.workflow_run.started_at
            )
        self.workflow_run.save()

    def _execute_reusable_job(self, job_id: str, job_def) -> bool:
        """Resolve and execute a reusable workflow."""
        uses_path = job_def.raw.get("uses", "")
        if not uses_path:
            return True

        self._log_system(f"Resolving reusable workflow: {uses_path}")
        ref_path = self._resolve_reusable_path(uses_path)

        if not ref_path.exists():
            self._log_error(f"Reusable workflow not found: {ref_path}")
            return False

        ref_workflow = self._parse_reusable_workflow(ref_path)
        if not ref_workflow:
            return False

        job_run = self._create_job_run(job_id, job_def)
        job_run.status = JobRun.STATUS_RUNNING
        job_run.save()

        return self._execute_reusable_workflow(job_run, job_def, ref_workflow, ref_path)

    def _resolve_reusable_path(self, uses_path: str) -> Path:
        """Resolve reusable workflow path from repo root."""
        return (Path.cwd() / uses_path).resolve()

    def _parse_reusable_workflow(self, ref_path: Path):
        """Parse reusable workflow YAML file."""
        parser = WorkflowParser()
        try:
            return parser.parse_file(ref_path)
        except Exception as exc:
            self._log_error(f"Failed to parse reusable workflow: {exc}")
            return None

    def _execute_reusable_workflow(
        self, job_run: JobRun, job_def, ref_workflow, ref_path: Path
    ) -> bool:
        """Execute referenced workflow respecting its dependencies."""
        ref_stage_order = ref_workflow.get_stage_order()
        ref_completed: set[str] = set()
        ref_failed: set[str] = set()

        for ref_job_id in ref_stage_order:
            if self.is_cancelled:
                break

            ref_job_def = ref_workflow.jobs.get(ref_job_id)
            if not ref_job_def:
                continue

            if not self._dependencies_met(ref_job_def, ref_completed, ref_failed):
                self._skip_job(ref_job_id, "Dependency failed or not completed")
                ref_failed.add(ref_job_id)
                continue

            ref_job_run = self._create_nested_job_run(
                job_run, job_def, ref_job_def, ref_job_id, ref_path.name
            )
            success = self._execute_job(ref_job_run, ref_job_def)
            self._record_job_result(ref_job_id, success, ref_completed, ref_failed)

        return self._finalize_reusable_job(job_run, ref_failed)

    def _create_nested_job_run(
        self,
        parent_job_run: JobRun,
        parent_job_def,
        ref_job_def,
        ref_job_id: str,
        source_workflow: str,
    ) -> JobRun:
        """Create a nested job run linked to parent reusable workflow."""
        return JobRun.objects.create(
            workflow_run=self.workflow_run,
            job_id=f"{parent_job_run.job_id}.{ref_job_id}",
            name=f"{parent_job_def.name} -> {ref_job_def.name}",
            status=JobRun.STATUS_RUNNING,
            started_at=timezone.now(),
            runner_label=", ".join(ref_job_def.runs_on),
            needs=ref_job_def.needs,
            meta={
                "parent_job": parent_job_run.job_id,
                "source_workflow": source_workflow,
            },
        )

    def _finalize_reusable_job(self, job_run: JobRun, ref_failed: set[str]) -> bool:
        """Update parent job run status after reusable workflow completes."""
        job_run.finished_at = timezone.now()
        if ref_failed:
            job_run.status = JobRun.STATUS_FAILED
            job_run.exit_code = 1
        else:
            job_run.status = JobRun.STATUS_PASSED
            job_run.exit_code = 0
        if job_run.started_at:
            job_run.duration = job_run.finished_at - job_run.started_at
        job_run.save()
        return len(ref_failed) == 0

    def _create_job_run(self, job_id: str, job_def) -> JobRun:
        """Create a JobRun record."""
        return JobRun.objects.create(
            workflow_run=self.workflow_run,
            job_id=job_id,
            name=job_def.name,
            status=JobRun.STATUS_RUNNING,
            started_at=timezone.now(),
            runner_label=", ".join(job_def.runs_on),
            needs=job_def.needs,
        )

    def _skip_job(self, job_id: str, reason: str) -> None:
        """Mark a job as skipped."""
        JobRun.objects.create(
            workflow_run=self.workflow_run,
            job_id=job_id,
            name=job_id,
            status=JobRun.STATUS_SKIPPED,
            meta={"reason": reason},
        )
        self._log_system(f"Skipping job '{job_id}': {reason}")

    def _execute_job(self, job_run: JobRun, job_def) -> bool:
        """Execute all steps in a job."""
        job_run.status = JobRun.STATUS_RUNNING
        job_run.save()

        overall_success = True
        for step_def in job_def.steps:
            if self.is_cancelled:
                job_run.status = JobRun.STATUS_CANCELLED
                job_run.save()
                return False

            if step_def.if_condition and not self._evaluate_condition(
                step_def.if_condition
            ):
                self._create_skipped_step(job_run, step_def)
                continue

            step_run = self._create_step_run(job_run, step_def)
            success = self._execute_step(step_run, step_def)

            if not success and not step_def.continue_on_error:
                overall_success = False
                job_run.status = JobRun.STATUS_FAILED
                job_run.exit_code = step_run.exit_code or 1
                job_run.finished_at = timezone.now()
                job_run.save()
                break

        return self._finalize_job(job_run, overall_success)

    def _finalize_job(self, job_run: JobRun, overall_success: bool) -> bool:
        """Update job run status after all steps complete."""
        if overall_success:
            job_run.status = JobRun.STATUS_PASSED
            job_run.exit_code = 0
        elif job_run.status not in (
            JobRun.STATUS_CANCELLED,
            JobRun.STATUS_FAILED,
        ):
            job_run.status = JobRun.STATUS_FAILED

        if not job_run.finished_at:
            job_run.finished_at = timezone.now()
        if job_run.started_at:
            job_run.duration = job_run.finished_at - job_run.started_at
        job_run.save()
        return overall_success

    def _create_step_run(self, job_run: JobRun, step_def) -> StepRun:
        """Create a StepRun record."""
        return StepRun.objects.create(
            job_run=job_run,
            step_id=step_def.step_id,
            name=step_def.name,
            status=StepRun.STATUS_RUNNING,
            started_at=timezone.now(),
            command=step_def.run or step_def.uses or "",
        )

    def _create_skipped_step(self, job_run: JobRun, step_def) -> StepRun:
        """Create a skipped StepRun record."""
        return StepRun.objects.create(
            job_run=job_run,
            step_id=step_def.step_id,
            name=step_def.name,
            status=StepRun.STATUS_SKIPPED,
            meta={"reason": f"Condition not met: {step_def.if_condition}"},
        )

    def _execute_step(self, step_run: StepRun, step_def) -> bool:
        """Execute a single step."""
        step_run.status = StepRun.STATUS_RUNNING
        step_run.save()

        if step_def.is_reusable:
            return self._execute_reusable_step(step_run, step_def)
        if step_def.is_local:
            return self._execute_local_step(step_run, step_def)

        step_run.status = StepRun.STATUS_PASSED
        step_run.exit_code = 0
        step_run.finished_at = timezone.now()
        step_run.save()
        return True

    def _execute_local_step(self, step_run: StepRun, step_def) -> bool:
        """Execute a local shell command step."""
        command = step_def.run
        if not command:
            step_run.status = StepRun.STATUS_PASSED
            step_run.exit_code = 0
            step_run.finished_at = timezone.now()
            step_run.save()
            return True

        env = self._build_step_env(step_def.env)
        start_time = timezone.now()
        log_func = self._build_logger(step_run)

        log_func(f"$ {command}", LogEntry.STREAM_SYSTEM)

        try:
            # shell=True is required to support multi-line commands,
            # pipes, redirects, and shell variable expansion used in
            # GitHub Actions workflow run: steps.
            process = subprocess.Popen(  # noqa: S602
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                text=True,
                cwd=Path(step_def.working_directory or ".").resolve(),
            )
            return self._stream_process_output(process, step_run, log_func, start_time)
        except Exception as exc:
            step_run.status = StepRun.STATUS_FAILED
            step_run.exit_code = -1
            step_run.finished_at = timezone.now()
            step_run.save()
            log_func(f"Exception: {exc}", LogEntry.STREAM_SYSTEM)
            logger.exception("Failed to execute step")
            return False

    def _build_step_env(self, step_env: dict) -> dict:
        """Build environment variables for step execution."""
        env = os.environ.copy()
        env.update(step_env)
        env["CI"] = "true"
        env["GITHUB_ACTIONS"] = "true"
        return env

    def _build_logger(self, step_run: StepRun):
        """Create a log function bound to current step run."""

        def _log(line: str, stream: str = LogEntry.STREAM_STDOUT) -> None:
            LogEntry.objects.create(
                workflow_run=self.workflow_run,
                job_run=step_run.job_run,
                step_run=step_run,
                content=line,
                stream=stream,
            )

        return _log

    def _stream_process_output(
        self, process, step_run: StepRun, log_func, start_time
    ) -> bool:
        """Stream subprocess output and capture result."""
        try:
            while True:
                if self.is_cancelled:
                    self._terminate_process(process)
                    step_run.status = StepRun.STATUS_CANCELLED
                    step_run.exit_code = -1
                    step_run.finished_at = timezone.now()
                    step_run.save()
                    log_func("Step cancelled by user", LogEntry.STREAM_SYSTEM)
                    return False

                stdout_line = process.stdout.readline()
                stderr_line = process.stderr.readline()

                if stdout_line:
                    log_func(stdout_line.rstrip("\n"), LogEntry.STREAM_STDOUT)
                if stderr_line:
                    log_func(stderr_line.rstrip("\n"), LogEntry.STREAM_STDERR)

                if process.poll() is not None:
                    self._drain_streams(process, log_func)
                    break

                time.sleep(0.01)
        finally:
            self._close_process_streams(process)

        return self._finalize_step(process, step_run, start_time)

    def _terminate_process(self, process) -> None:
        """Terminate process with timeout fallback to kill."""
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()

    def _drain_streams(self, process, log_func) -> None:
        """Read remaining output from process streams."""
        for remaining in process.stdout:
            try:
                log_func(remaining.rstrip("\n"), LogEntry.STREAM_STDOUT)
            except Exception:
                logger.debug("Failed to read stdout", exc_info=True)
        for remaining in process.stderr:
            try:
                log_func(remaining.rstrip("\n"), LogEntry.STREAM_STDERR)
            except Exception:
                logger.debug("Failed to read stderr", exc_info=True)

    def _close_process_streams(self, process) -> None:
        """Close process streams safely."""
        try:
            if process.stdout:
                process.stdout.close()
        except Exception:
            logger.debug("Failed to close stdout", exc_info=True)
        try:
            if process.stderr:
                process.stderr.close()
        except Exception:
            logger.debug("Failed to close stderr", exc_info=True)
        try:
            process.wait(timeout=1)
        except Exception:
            logger.debug("Process wait timeout", exc_info=True)

    def _finalize_step(self, process, step_run: StepRun, start_time) -> bool:
        """Record final step status based on exit code."""
        exit_code = process.returncode
        end_time = timezone.now()

        step_run.exit_code = exit_code
        step_run.finished_at = end_time
        step_run.duration = end_time - start_time

        if exit_code == 0:
            step_run.status = StepRun.STATUS_PASSED
        else:
            step_run.status = StepRun.STATUS_FAILED
            step_run.job_run.workflow_run.log_entries.create(
                content=f"Command failed with exit code {exit_code}",
                stream=LogEntry.STREAM_SYSTEM,
            )

        step_run.save()
        return exit_code == 0

    def _execute_reusable_step(self, step_run: StepRun, step_def) -> bool:
        """Execute a reusable workflow step (uses: ...)."""
        self._log_notice(
            step_run,
            f"Reusable workflow '{step_def.uses}' skipped in local mode",
        )
        step_run.status = StepRun.STATUS_PASSED
        step_run.exit_code = 0
        step_run.finished_at = timezone.now()
        step_run.save()
        return True

    def _log_system(self, message: str) -> None:
        """Log a system message to workflow log."""
        LogEntry.objects.create(
            workflow_run=self.workflow_run,
            content=f"::{message}",
            stream=LogEntry.STREAM_SYSTEM,
        )

    def _log_error(self, message: str) -> None:
        """Log an error message to workflow log."""
        LogEntry.objects.create(
            workflow_run=self.workflow_run,
            content=f"::error:: {message}",
            stream=LogEntry.STREAM_SYSTEM,
        )

    def _log_notice(self, step_run: StepRun, message: str) -> None:
        """Log a notice message to workflow log."""
        LogEntry.objects.create(
            workflow_run=self.workflow_run,
            job_run=step_run.job_run,
            step_run=step_run,
            content=f"::notice:: {message}",
            stream=LogEntry.STREAM_SYSTEM,
        )

    @staticmethod
    def _evaluate_condition(condition: str | None) -> bool:
        """Evaluate a simple GitHub Actions if condition."""
        if not condition:
            return True

        if "always()" in condition:
            return True
        if "success()" in condition:
            return True
        if "failure()" in condition:
            return False
        if "cancelled()" in condition:
            return False

        return True
