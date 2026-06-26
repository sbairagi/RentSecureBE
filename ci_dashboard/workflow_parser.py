"""
GitHub Actions Workflow Parser.

Reads YAML files from .github/workflows/ and extracts:
- jobs, steps, commands, dependencies (needs)
- stage names, trigger conditions
- Reusable workflow detection

This is the single source of truth for the local CI dashboard.
"""

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from ci_dashboard.models import WorkflowDefinition


@dataclass
class Step:
    """Represents a single step in a GitHub Actions job."""

    step_id: str
    name: str
    uses: str | None = None
    run: str | None = None
    with_: dict = field(default_factory=dict)
    env: dict = field(default_factory=dict)
    if_condition: str | None = None
    continue_on_error: bool = False
    timeout_minutes: int | None = None
    working_directory: str | None = None
    raw: dict = field(default_factory=dict)

    @property
    def is_reusable(self) -> bool:
        return self.uses is not None

    @property
    def is_local(self) -> bool:
        return self.run is not None


@dataclass
class Job:
    """Represents a single job in a GitHub Actions workflow."""

    job_id: str
    name: str
    runs_on: str | list[str]
    needs: list[str] = field(default_factory=list)
    steps: list[Step] = field(default_factory=list)
    if_condition: str | None = None
    timeout_minutes: int | None = None
    strategy: dict | None = None
    env: dict = field(default_factory=dict)
    defaults: dict = field(default_factory=dict)
    outputs: dict = field(default_factory=dict)
    raw: dict = field(default_factory=dict)

    @property
    def is_reusable(self) -> bool:
        return "uses" in self.raw


@dataclass
class Workflow:
    """Represents a complete GitHub Actions workflow."""

    name: str
    file_path: str
    on_trigger: dict
    jobs: dict[str, Job]
    env: dict = field(default_factory=dict)
    defaults: dict = field(default_factory=dict)
    permissions: dict = field(default_factory=dict)
    concurrency: dict | None = None
    raw: dict = field(default_factory=dict)

    @property
    def job_ids(self) -> list[str]:
        return list(self.jobs.keys())

    def get_stage_order(self) -> list[str]:
        """Return job IDs in topological order based on needs."""
        visited = set()
        result = []

        def visit(job_id: str) -> None:
            if job_id in visited:
                return
            visited.add(job_id)
            job = self.jobs.get(job_id)
            if job:
                for dep in job.needs:
                    if dep in self.jobs:
                        visit(dep)
            result.append(job_id)

        for job_id in self.jobs:
            visit(job_id)

        return result

    def get_job(self, job_id: str) -> Job | None:
        """Get a job by ID."""
        return self.jobs.get(job_id)

    def has_trigger(self, trigger_name: str) -> bool:
        """Check if workflow has a specific trigger."""
        return trigger_name in self.on_trigger


class WorkflowParser:
    """Parse GitHub Actions workflow YAML files."""

    WORKFLOWS_DIR = Path(".github/workflows")

    def __init__(self, workflows_dir: Path | None = None):
        self.workflows_dir = workflows_dir or self.WORKFLOWS_DIR

    def discover_workflows(self) -> list[Path]:
        """Find all YAML workflow files."""
        if not self.workflows_dir.exists():
            return []
        return sorted(self.workflows_dir.glob("*.yml"))

    def parse_file(self, file_path: Path) -> Workflow:
        """Parse a single workflow YAML file."""
        with open(file_path) as f:
            raw = yaml.safe_load(f) or {}

        workflow_name = raw.get("name", file_path.stem)
        on_trigger = raw.get("on", {})
        if not isinstance(on_trigger, dict):
            on_trigger = {}
        jobs_raw = raw.get("jobs", {})

        jobs = {}
        for job_id, job_def in jobs_raw.items():
            if not isinstance(job_def, dict):
                continue
            jobs[job_id] = self._parse_job(job_id, job_def)

        return Workflow(
            name=workflow_name,
            file_path=str(file_path),
            on_trigger=on_trigger,
            jobs=jobs,
            env=raw.get("env", {}),
            defaults=raw.get("defaults", {}),
            permissions=raw.get("permissions", {}),
            concurrency=raw.get("concurrency"),
            raw=raw,
        )

    def parse_all(self) -> dict[str, Workflow]:
        """Parse all workflow files and return by filename."""
        workflows = {}
        for path in self.discover_workflows():
            try:
                workflow = self.parse_file(path)
                workflows[path.name] = workflow
            except Exception as exc:
                print(f"Warning: Failed to parse {path}: {exc}")
        return workflows

    def _parse_job(self, job_id: str, job_def: dict) -> Job:
        """Parse a single job definition."""
        runs_on = job_def.get("runs-on", "ubuntu-latest")
        if isinstance(runs_on, str):
            runs_on = [runs_on]

        needs = job_def.get("needs", [])
        if isinstance(needs, str):
            needs = [needs]

        steps = []
        for step_def in job_def.get("steps", []):
            steps.append(self._parse_step(step_def))

        return Job(
            job_id=job_id,
            name=job_def.get("name", job_id),
            runs_on=runs_on,
            needs=needs,
            steps=steps,
            if_condition=job_def.get("if"),
            timeout_minutes=job_def.get("timeout-minutes"),
            strategy=job_def.get("strategy"),
            env=job_def.get("env", {}),
            defaults=job_def.get("defaults", {}),
            outputs=job_def.get("outputs", {}),
            raw=job_def,
        )

    def _parse_step(self, step_def: dict) -> Step:
        """Parse a single step definition."""
        step_id = step_def.get("id", step_def.get("name", f"step_{id(step_def)}"))
        name = step_def.get("name", step_id)

        return Step(
            step_id=str(step_id),
            name=name,
            uses=step_def.get("uses"),
            run=step_def.get("run"),
            with_=step_def.get("with", {}),
            env=step_def.get("env", {}),
            if_condition=step_def.get("if"),
            continue_on_error=step_def.get("continue-on-error", False),
            timeout_minutes=step_def.get("timeout-minutes"),
            working_directory=step_def.get("working-directory"),
            raw=step_def,
        )

    def sync_to_db(self) -> dict[str, WorkflowDefinition]:
        """Parse all workflows and sync to database."""
        workflows = self.parse_all()
        definitions = {}

        for filename, workflow in workflows.items():
            wf_def, _ = WorkflowDefinition.objects.update_or_create(
                file_path=workflow.file_path,
                defaults={
                    "workflow_name": workflow.name,
                    "raw_yaml": yaml.dump(workflow.raw, default_flow_style=False),
                    "parsed_json": workflow.raw,
                    "jobs": {jid: job.raw for jid, job in workflow.jobs.items()},
                    "on_trigger": workflow.on_trigger,
                },
            )
            definitions[filename] = wf_def

        return definitions

    @staticmethod
    def get_workflow(file_path: str) -> Workflow | None:
        """Get a parsed workflow by file path."""
        path = Path(file_path)
        if not path.exists():
            return None
        parser = WorkflowParser()
        try:
            return parser.parse_file(path)
        except Exception:
            return None
