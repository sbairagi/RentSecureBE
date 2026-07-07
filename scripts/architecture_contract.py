#!/usr/bin/env python3
"""
Architecture Contract Validator v2.0
...
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

# pylint: disable=too-many-lines


def _validate_safe_path(path: Path, base: Path) -> Path:
    resolved = path.resolve()
    base_resolved = base.resolve()
    try:
        resolved.relative_to(base_resolved)
    except ValueError:
        raise ValueError(f"Path escapes allowed directory: {path}") from None
    return resolved


CI_YAML = ".github/workflows/ci.yml"
ARCHITECTURE_GUARD_YAML = ".github/workflows/architecture-guard.yml"
DOCS_CI_CD_PIPELINE = "docs/ci-cd-pipeline.md"

# ═══════════════════════════════════════════════════════════════════════════════
# ARCHITECTURE CONTRACT — THE SOURCE OF TRUTH
# ═══════════════════════════════════════════════════════════════════════════════

ARCHITECTURE_VERSION = "2.3.0"
PIPELINE_VERSION = "2.3.0"
CONTRACT_VERSION = "2.3.0"

# Every required job that MUST exist in ci.yml
REQUIRED_JOBS: set[str] = {
    "lint-fast",
    "test-shard-1",
    "test-shard-2",
    "test-shard-3",
    "test-shard-4",
    "shard-validation",
    "contract-tests",
    "django-check",
    "hypothesis-fast",
    "architecture",
    "security-fast",
    "mutation-smoke",
    "migration-rollback-validation",
    "quality",
    "deploy-readiness",
    "deploy",
}

# Every required workflow file that MUST exist on disk (ERROR severity)
REQUIRED_WORKFLOW_FILES: set[str] = {
    CI_YAML,
    ".github/workflows/lint.yml",
    ".github/workflows/test.yml",
    ".github/workflows/django-check.yml",
    ".github/workflows/hypothesis.yml",
    ".github/workflows/contract-tests.yml",
    ".github/workflows/architecture.yml",
    ".github/workflows/security.yml",
    ".github/workflows/security-deep.yml",
    ".github/workflows/quality.yml",
    ".github/workflows/performance.yml",
    ".github/workflows/mutation.yml",
    ".github/workflows/migration-rollback.yml",
    ".github/workflows/deploy-readiness.yml",
    ".github/workflows/deploy.yml",
    ".github/workflows/nightly.yml",
    ARCHITECTURE_GUARD_YAML,
    ".github/workflows/benchmark.yml",
    ".github/workflows/load-test.yml",
    ".github/workflows/weekly.yml",
    ".github/workflows/ci-metrics.yml",
    ".github/workflows/sbom.yml",
    ".github/workflows/rollback.yml",
}

# Protected files that are critical to the governance system itself (CRITICAL severity)
PROTECTED_FILES: set[str] = {
    CI_YAML,
    ".github/workflows/lint.yml",
    ".github/workflows/test.yml",
    ".github/workflows/security.yml",
    ".github/workflows/security-deep.yml",
    ".github/workflows/quality.yml",
    ".github/workflows/deploy.yml",
    ".github/workflows/architecture.yml",
    ".github/workflows/deploy-readiness.yml",
    ".github/workflows/nightly.yml",
    ARCHITECTURE_GUARD_YAML,
    ".github/workflows/sbom.yml",
    "scripts/architecture_contract.py",
    "docs/architecture-contract.md",
    DOCS_CI_CD_PIPELINE,
    "docs/governance.md",
}

# Contract self-protection files (CRITICAL severity)
SELF_PROTECTION_FILES: set[str] = {
    "scripts/architecture_contract.py",
    ARCHITECTURE_GUARD_YAML,
}

# Approved dependency chain
APPROVED_DEPENDENCY_CHAIN: dict[str, list[str] | None] = {
    "lint-fast": None,
    "test-shard-1": ["lint-fast"],
    "test-shard-2": ["lint-fast"],
    "test-shard-3": ["lint-fast"],
    "test-shard-4": ["lint-fast"],
    "shard-validation": [
        "test-shard-1",
        "test-shard-2",
        "test-shard-3",
        "test-shard-4",
    ],
    "contract-tests": ["lint-fast"],
    "django-check": ["lint-fast"],
    "hypothesis-fast": ["lint-fast"],
    "architecture": ["lint-fast"],
    "security-fast": ["lint-fast"],
    "mutation-smoke": ["lint-fast"],
    "migration-rollback-validation": ["lint-fast"],
    "quality": [
        "test-shard-1",
        "test-shard-2",
        "test-shard-3",
        "test-shard-4",
        "shard-validation",
        "contract-tests",
        "architecture",
    ],
    "deploy-readiness": [
        "quality",
        "security-fast",
        "django-check",
    ],
    "deploy": ["deploy-readiness"],
}

# Stage labels
STAGE_MAP: dict[str, str] = {
    "lint-fast": "Stage 1   │ Lint Fast",
    "test-shard-1": "Stage 2a  │ Pytest + Coverage (Shard 1/4)",
    "test-shard-2": "Stage 2a  │ Pytest + Coverage (Shard 2/4)",
    "test-shard-3": "Stage 2a  │ Pytest + Coverage (Shard 3/4)",
    "test-shard-4": "Stage 2a  │ Pytest + Coverage (Shard 4/4)",
    "shard-validation": "Stage 2b  │ Shard Distribution Validation",
    "contract-tests": "Stage 2c  │ API Contract Tests",
    "django-check": "Stage 2c  │ Django System & Migration Checks",
    "hypothesis-fast": "Stage 2d  │ Hypothesis Property Tests (Fast)",
    "architecture": "Stage 2e  │ Architecture & Contracts",
    "security-fast": "Stage 2f  │ Security Fast-Track",
    "mutation-smoke": "Stage 2g  │ Mutation Testing (Smoke)",
    "migration-rollback-validation": "Stage 2h │ Migration Rollback Validation",
    "quality": "Stage 3   │ Quality Gate (SonarCloud)",
    "deploy-readiness": "Stage 4   │ Deploy Readiness Check",
    "deploy": "Stage 5   │ Deploy to Production",
}

# Required stage names for documentation sync validation
REQUIRED_DOC_STAGES: list[str] = [
    "Setup",
    "Code Quality",
    "Tests",
    "Django Checks",
    "Architecture",
    "Security",
    "Quality Gate",
    "Deploy",
]

# The topological order that defines valid stage sequencing
APPROVED_STAGE_ORDER: list[str] = [
    "lint-fast",
    "test-shard-1",
    "test-shard-2",
    "test-shard-3",
    "test-shard-4",
    "shard-validation",
    "contract-tests",
    "django-check",
    "hypothesis-fast",
    "architecture",
    "security-fast",
    "mutation-smoke",
    "quality",
    "deploy-readiness",
    "deploy",
]

# Compliance score categories
CATEGORY_WORKFLOW_STRUCTURE = "Workflow Structure"
CATEGORY_DEPENDENCY_GRAPH = "Dependency Graph"
CATEGORY_SECURITY_CONTROLS = "Security Controls"
CATEGORY_QUALITY_GATES = "Quality Gates"
CATEGORY_DOCUMENTATION_SYNC = "Documentation Sync"
CATEGORY_PROTECTED_FILES = "Protected Files"
CATEGORY_VERSION_ALIGNMENT = "Version Alignment"

SCORE_CATEGORIES: list[str] = [
    CATEGORY_WORKFLOW_STRUCTURE,
    CATEGORY_DEPENDENCY_GRAPH,
    CATEGORY_SECURITY_CONTROLS,
    CATEGORY_QUALITY_GATES,
    CATEGORY_DOCUMENTATION_SYNC,
    CATEGORY_PROTECTED_FILES,
    CATEGORY_VERSION_ALIGNMENT,
]


# ═══════════════════════════════════════════════════════════════════════════════
# VIOLATION TYPES
# ═══════════════════════════════════════════════════════════════════════════════


class Violation:
    MISSING_JOB = "missing_job"
    EXTRA_JOB = "extra_job"
    MISSING_WORKFLOW = "missing_workflow"
    MISSING_PROTECTED_FILE = "missing_protected_file"
    MISSING_DEPENDENCY = "missing_dependency"
    EXTRA_DEPENDENCY = "extra_dependency"
    STAGE_REORDERED = "stage_reordered"
    SECURITY_BYPASSED = "security_bypassed"
    QUALITY_GATE_BYPASSED = "quality_gate_bypassed"
    DEPLOY_READINESS_BYPASSED = "deploy_readiness_bypassed"
    DEPLOY_ON_PR = "deploy_on_pr"
    VERSION_MISMATCH = "version_mismatch"
    DOC_SYNC = "documentation_out_of_sync"
    GUARD_REMOVED = "architecture_guard_removed"
    CONTRACT_DELETED = "contract_deleted"


class ArchitectureContractValidator:
    """Validates the CI/CD pipeline against the approved architecture contract."""

    def __init__(
        self,
        ci_yaml_path: str = CI_YAML,
        verbose: bool = False,
        repo_root: str | None = None,
    ):
        self.ci_yaml_path = Path(ci_yaml_path)
        self.repo_root = Path(repo_root) if repo_root else self._find_repo_root()
        self.verbose = verbose
        self.violations: list[dict[str, Any]] = []
        self.ci_config: dict[str, Any] | None = None
        self.actual_jobs: set[str] = set()
        self.actual_dependencies: dict[str, list[str] | None] = {}
        self.actual_stage_order: list[str] = []

    def _find_repo_root(self) -> Path:
        """Find the repository root."""
        cwd = Path.cwd()
        for parent in [cwd] + list(cwd.parents):
            if (parent / ".git").exists() or (parent / ".github").exists():
                return parent
            if (parent / "manage.py").exists():  # nosonar
                return parent
        return cwd

    def log(self, message: str) -> None:
        """Print verbose log messages."""
        if self.verbose:
            print(f"[VERBOSE] {message}")

    # ── Parsing ───────────────────────────────────────────────────────────────

    def parse_ci_yaml(self) -> dict[str, Any]:
        """Parse ci.yml and extract job definitions and dependencies."""
        if not self.ci_yaml_path.exists():
            raise FileNotFoundError(
                f"CI configuration not found at {self.ci_yaml_path}."
            )

        with open(self.ci_yaml_path, encoding="utf-8") as f:
            loaded = yaml.safe_load(f)

        if not isinstance(loaded, dict):
            raise ValueError(f"Empty or invalid YAML in {self.ci_yaml_path}")

        config: dict[str, Any] = loaded

        self.ci_config = config

        jobs = config.get("jobs", {})
        self.actual_jobs = set(jobs.keys())

        for job_name, job_def in jobs.items():
            if isinstance(job_def, dict):
                needs = job_def.get("needs")
                if needs is None:
                    self.actual_dependencies[job_name] = None
                elif isinstance(needs, list):
                    self.actual_dependencies[job_name] = needs
                else:
                    self.actual_dependencies[job_name] = [needs]

        self.actual_stage_order = self._topological_order(self.actual_dependencies)

        self.log(f"Parsed {len(self.actual_jobs)} jobs from ci.yml")
        self.log(f"Actual jobs: {sorted(self.actual_jobs)}")
        self.log(f"Actual stage order: {self.actual_stage_order}")

        return config

    @staticmethod
    def _topological_order(
        dependencies: dict[str, list[str] | None],
    ) -> list[str]:
        """Produce a topological ordering."""
        visited: set[str] = set()
        result: list[str] = []

        def visit(job: str) -> None:
            if job in visited:
                return
            visited.add(job)
            deps = dependencies.get(job)
            if deps:
                for dep in deps:
                    if dep in dependencies:
                        visit(dep)
            result.append(job)

        for job in dependencies:
            visit(job)

        return result

    # ═══════════════════════════════════════════════════════════════════════════
    # CHECK 1: Protected File Validation (CRITICAL)
    # ═══════════════════════════════════════════════════════════════════════════

    def check_protected_files(self) -> None:
        """Verify all protected files exist. Missing → CRITICAL."""
        self.log("Checking protected files...")
        for filepath in PROTECTED_FILES:
            full_path = self.repo_root / filepath
            exists = full_path.exists()
            self.log(f"  {filepath}: {'✓ EXISTS' if exists else '✗ MISSING'}")
            if not exists:
                self.violations.append(
                    {
                        "type": Violation.MISSING_PROTECTED_FILE,
                        "severity": "CRITICAL",
                        "message": f"Protected file missing: {filepath}",
                        "details": {"expected_path": str(full_path)},
                    }
                )

    # ═══════════════════════════════════════════════════════════════════════════
    # CHECK 2: Architecture Version Enforcement
    # ═══════════════════════════════════════════════════════════════════════════

    def check_versions(self) -> None:
        """Verify architecture, pipeline, and contract versions are in sync."""
        self.log("Checking version alignment...")
        versions = {
            "ARCHITECTURE_VERSION": ARCHITECTURE_VERSION,
            "PIPELINE_VERSION": PIPELINE_VERSION,
            "CONTRACT_VERSION": CONTRACT_VERSION,
        }

        # All three must be equal
        unique = set(versions.values())
        if len(unique) != 1:
            self.violations.append(
                {
                    "type": Violation.VERSION_MISMATCH,
                    "severity": "CRITICAL",
                    "message": (
                        f"Architecture version mismatch: "
                        f"ARCHITECTURE_VERSION={ARCHITECTURE_VERSION}, "
                        f"PIPELINE_VERSION={PIPELINE_VERSION}, "
                        f"CONTRACT_VERSION={CONTRACT_VERSION}. "
                        "All three must be identical."
                    ),
                    "details": versions,
                }
            )
            return

        # Verify version appears in docs/architecture-contract.md
        doc_path = self.repo_root / "docs" / "architecture-contract.md"
        if doc_path.exists():
            content = doc_path.read_text()
            if CONTRACT_VERSION not in content:
                self.violations.append(
                    {
                        "type": Violation.VERSION_MISMATCH,
                        "severity": "CRITICAL",
                        "message": (
                            f"Version {CONTRACT_VERSION} not found in "
                            f"docs/architecture-contract.md. Documentation "
                            f"version must match CONTRACT_VERSION."
                        ),
                        "details": {
                            "expected_version": CONTRACT_VERSION,
                            "file": "docs/architecture-contract.md",
                        },
                    }
                )

        # Verify version appears in docs/ci-cd-pipeline.md
        pipeline_doc = self.repo_root / DOCS_CI_CD_PIPELINE
        if pipeline_doc.exists():
            content = pipeline_doc.read_text()
            if PIPELINE_VERSION not in content:
                self.violations.append(
                    {
                        "type": Violation.VERSION_MISMATCH,
                        "severity": "CRITICAL",
                        "message": (
                            f"Version {PIPELINE_VERSION} not found in "
                            f"{DOCS_CI_CD_PIPELINE}. Documentation "
                            f"version must match PIPELINE_VERSION."
                        ),
                        "details": {
                            "expected_version": PIPELINE_VERSION,
                            "file": DOCS_CI_CD_PIPELINE,
                        },
                    }
                )

        self.log(f"  ✓ Versions aligned: {CONTRACT_VERSION}")

    # ═══════════════════════════════════════════════════════════════════════════
    # CHECK 3: Documentation Synchronization
    # ═══════════════════════════════════════════════════════════════════════════

    def check_documentation_sync(self) -> None:
        """Verify docs contain all required pipeline stages."""
        self.log("Checking documentation synchronization...")

        doc_path = self.repo_root / DOCS_CI_CD_PIPELINE
        if not doc_path.exists():
            self.violations.append(
                {
                    "type": Violation.DOC_SYNC,
                    "severity": "ERROR",
                    "message": (
                        f"{DOCS_CI_CD_PIPELINE} is missing. "
                        "Pipeline documentation is required."
                    ),
                    "details": {"expected_path": str(doc_path)},
                }
            )
            return

        content = doc_path.read_text()

        for stage in REQUIRED_DOC_STAGES:
            if stage.lower() not in content.lower():
                self.violations.append(
                    {
                        "type": Violation.DOC_SYNC,
                        "severity": "ERROR",
                        "message": (
                            f"Pipeline documentation out of sync: Stage '{stage}' "
                            f"is defined in {CI_YAML} but missing from "
                            f"{DOCS_CI_CD_PIPELINE}."
                        ),
                        "details": {
                            "missing_stage": stage,
                            "document": DOCS_CI_CD_PIPELINE,
                        },
                    }
                )

    # ═══════════════════════════════════════════════════════════════════════════
    # CHECK 4: Contract Self-Protection (CRITICAL)
    # ═══════════════════════════════════════════════════════════════════════════

    def check_self_protection(self) -> None:
        """Verify the contract and guard workflow are present and active."""
        self.log("Checking contract self-protection...")

        for filepath in SELF_PROTECTION_FILES:
            full_path = self.repo_root / filepath
            exists = full_path.exists()
            self.log(f"  {filepath}: {'✓ EXISTS' if exists else '✗ MISSING'}")
            if not exists:
                violation_type = (
                    Violation.GUARD_REMOVED
                    if "architecture-guard" in filepath
                    else Violation.CONTRACT_DELETED
                )
                label = (
                    "Architecture Guard"
                    if "architecture-guard" in filepath
                    else "Contract Validator"
                )
                self.violations.append(
                    {
                        "type": violation_type,
                        "severity": "CRITICAL",
                        "message": (
                            f"{label} removed: {filepath}. "
                            f"The architecture governance system requires this file."
                        ),
                        "details": {"expected_path": str(full_path)},
                    }
                )

    # ═══════════════════════════════════════════════════════════════════════════
    # CHECK 5: Required Workflow Files
    # ═══════════════════════════════════════════════════════════════════════════

    def check_required_workflow_files(self) -> None:
        """Check that all required workflow files exist on disk."""
        self.log("Checking required workflow files...")
        for filepath in REQUIRED_WORKFLOW_FILES:
            full_path = self.repo_root / filepath
            exists = full_path.exists()
            self.log(f"  {filepath}: {'✓ EXISTS' if exists else '✗ MISSING'}")
            if not exists:
                self.violations.append(
                    {
                        "type": Violation.MISSING_WORKFLOW,
                        "severity": "ERROR",
                        "message": f"Required workflow file missing: {filepath}",
                        "details": {"expected_path": str(full_path)},
                    }
                )

    # ═══════════════════════════════════════════════════════════════════════════
    # CHECK 6: Required Jobs
    # ═══════════════════════════════════════════════════════════════════════════

    def check_required_jobs(self) -> None:
        """Check that all required jobs exist in ci.yml."""
        self.log("Checking required jobs...")
        for job in REQUIRED_JOBS:
            exists = job in self.actual_jobs
            self.log(f"  {job}: {'✓ EXISTS' if exists else '✗ MISSING'}")
            if not exists:
                self.violations.append(
                    {
                        "type": Violation.MISSING_JOB,
                        "severity": "ERROR",
                        "message": f"Required job '{job}' is missing from ci.yml",
                        "details": {
                            "expected_job": job,
                            "stage": STAGE_MAP.get(job, "unknown"),
                        },
                    }
                )

    # ═══════════════════════════════════════════════════════════════════════════
    # CHECK 7: Extra Jobs (advisory)
    # ═══════════════════════════════════════════════════════════════════════════

    def check_extra_jobs(self) -> None:
        """Warn about unrecognized jobs."""
        self.log("Checking for unrecognized jobs...")
        known_jobs = REQUIRED_JOBS | {"architecture-guard"}
        for job in self.actual_jobs:
            if job not in known_jobs:
                self.log(f"  {job}: ⚠ UNRECOGNIZED (non-breaking advisory)")
                self.violations.append(
                    {
                        "type": Violation.EXTRA_JOB,
                        "severity": "WARNING",
                        "message": f"Unrecognized job '{job}' found in ci.yml",
                        "details": {"extra_job": job},
                    }
                )

    # ═══════════════════════════════════════════════════════════════════════════
    # CHECK 8: Dependency Integrity
    # ═══════════════════════════════════════════════════════════════════════════

    def check_dependencies(self) -> None:
        """Verify every job's dependencies match the approved contract exactly."""
        self.log("Checking dependency chains...")
        for job, expected_needs in APPROVED_DEPENDENCY_CHAIN.items():
            if job not in self.actual_dependencies:
                continue

            actual_needs = self.actual_dependencies[job]
            self._check_job_dependencies(job, expected_needs, actual_needs)

    def _check_job_dependencies(
        self,
        job: str,
        expected_needs: list[str] | None,
        actual_needs: list[str] | None,
    ) -> None:
        if expected_needs is None and actual_needs is None:
            self.log(f"  {job}: ✓ no dependencies (root)")
            return

        if expected_needs is None:
            self._append_violation(
                job,
                Violation.MISSING_DEPENDENCY,
                f"Job '{job}' has no dependencies, but should have: {expected_needs}",
                expected=expected_needs,
                actual=None,
            )
            return

        if actual_needs is None:
            self._append_violation(
                job,
                Violation.MISSING_DEPENDENCY,
                f"Job '{job}' had dependencies removed. "
                f"Expected: {sorted(expected_needs)}",
                expected=sorted(expected_needs),
                actual=None,
            )
            return

        expected_sorted = sorted(expected_needs)
        actual_sorted = sorted(actual_needs)
        if expected_sorted != actual_sorted:
            violation_type = (
                Violation.EXTRA_DEPENDENCY
                if set(actual_sorted) - set(expected_sorted)
                else Violation.MISSING_DEPENDENCY
            )
            self._append_violation(
                job,
                violation_type,
                f"Job '{job}' dependencies changed.\n"
                f"  Expected: {expected_sorted}\n"
                f"  Actual:   {actual_sorted}",
                expected=expected_sorted,
                actual=actual_sorted,
            )
        else:
            self.log(f"  {job}: ✓ dependencies match: {expected_sorted}")

    def _append_violation(
        self,
        job: str,
        violation_type: str,
        message: str,
        expected: object = None,
        actual: object = None,
    ) -> None:
        self.violations.append(
            {
                "type": violation_type,
                "severity": "ERROR",
                "message": message,
                "details": {
                    "job": job,
                    "expected": expected,
                    "actual": actual,
                },
            }
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # CHECK 9: Stage Ordering (transitive)
    # ═══════════════════════════════════════════════════════════════════════════

    def _transitive_deps(
        self,
        job: str,
        deps: dict[str, list[str] | None],
        memo: dict[str, set[str]],
    ) -> set[str]:
        """Compute transitive dependencies for a job."""
        if job in memo:
            return memo[job]
        result: set[str] = set()
        needs = deps.get(job)
        if needs:
            for n in needs:
                result.add(n)
                result |= self._transitive_deps(n, deps, memo)
        memo[job] = result
        return result

    def check_stage_order(self) -> None:
        """Verify transitive dependencies enforce correct stage ordering."""
        self.log("Checking stage ordering via transitive dependencies...")

        memo: dict[str, set[str]] = {}
        actual_transitive = {
            j: self._transitive_deps(j, self.actual_dependencies, memo)
            for j in self.actual_dependencies
        }

        for job, expected_needs in APPROVED_DEPENDENCY_CHAIN.items():
            if job not in self.actual_dependencies:
                continue
            if expected_needs is None:
                continue

            actual_trans = actual_transitive.get(job, set())
            missing_deps = [dep for dep in expected_needs if dep not in actual_trans]
            if missing_deps:
                for missing_dep in missing_deps:
                    self.violations.append(
                        {
                            "type": Violation.STAGE_REORDERED,
                            "severity": "ERROR",
                            "message": (
                                f"Stage ordering violation: '{job}' "
                                f"({STAGE_MAP.get(job, job)}) should depend on "
                                f"'{missing_dep}' "
                                f"({STAGE_MAP.get(missing_dep, missing_dep)}), "
                                f"but no transitive dependency path exists."
                            ),
                            "details": {
                                "job": job,
                                "missing_dependency": missing_dep,
                                "actual_transitive_deps": list(actual_trans),
                            },
                        }
                    )

        if not self.violations or all(
            v["type"] != Violation.STAGE_REORDERED for v in self.violations
        ):
            self.log("  ✓ Stage ordering is correct")

    # ═══════════════════════════════════════════════════════════════════════════
    # CHECK 10-12: Bypass Protections
    # ═══════════════════════════════════════════════════════════════════════════

    def _check_bypass(
        self,
        job_name: str,
        violation_type: str,
        severity: str,
        message_template: str,
        expected_needs: list[str],
    ) -> None:
        """Generic bypass check."""
        if job_name not in self.actual_dependencies:
            return

        actual_needs = self.actual_dependencies[job_name]
        if actual_needs is None:
            self.violations.append(
                {
                    "type": violation_type,
                    "severity": severity,
                    "message": message_template.format(
                        job_name=job_name, expected=expected_needs, actual=None
                    ),
                    "details": {"expected_needs": expected_needs, "actual_needs": None},
                }
            )
            return

        if sorted(actual_needs) != sorted(expected_needs):
            self.violations.append(
                {
                    "type": violation_type,
                    "severity": severity,
                    "message": message_template.format(
                        job_name=job_name, expected=expected_needs, actual=actual_needs
                    ),
                    "details": {
                        "expected_needs": expected_needs,
                        "actual_needs": actual_needs,
                    },
                }
            )

    def check_security_not_bypassed(self) -> None:
        """Verify security-fast cannot be bypassed."""
        self.log("Checking security-fast stage integrity...")
        self._check_bypass(
            job_name="security-fast",
            violation_type=Violation.SECURITY_BYPASSED,
            severity="CRITICAL",
            message_template=(
                "SECURITY BYPASS: The 'security-fast' job dependencies"
                " have been altered. Security must always run after lint-fast."
            ),
            expected_needs=["lint-fast"],
        )

    def check_quality_gate_not_bypassed(self) -> None:
        """Verify quality gate cannot be bypassed."""
        self.log("Checking quality gate integrity...")
        self._check_bypass(
            job_name="quality",
            violation_type=Violation.QUALITY_GATE_BYPASSED,
            severity="CRITICAL",
            message_template=(
                "QUALITY GATE BYPASS: The 'quality' job dependencies have been altered."
            ),
            expected_needs=[
                "test-shard-1",
                "test-shard-2",
                "test-shard-3",
                "test-shard-4",
                "shard-validation",
                "contract-tests",
                "architecture",
            ],
        )

    def check_deploy_readiness_not_bypassed(self) -> None:
        """Verify deploy-readiness cannot be bypassed."""
        self.log("Checking deploy-readiness integrity...")
        self._check_bypass(
            job_name="deploy-readiness",
            violation_type=Violation.DEPLOY_READINESS_BYPASSED,
            severity="CRITICAL",
            message_template=(
                "DEPLOY READINESS BYPASS: The 'deploy-readiness' job "
                "dependencies have been altered."
            ),
            expected_needs=[
                "quality",
                "security-fast",
                "django-check",
            ],
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # CHECK 13: Deploy on PR
    # ═══════════════════════════════════════════════════════════════════════════

    def check_deploy_not_on_pr(self) -> None:
        """Verify deploy job cannot run on pull_request events."""
        self.log("Checking deploy trigger restrictions...")

        deploy_job = "deploy"
        if self.ci_config is None or deploy_job not in self.ci_config.get("jobs", {}):
            return

        deploy_def = self.ci_config["jobs"][deploy_job]
        if isinstance(deploy_def, dict):
            deploy_if = deploy_def.get("if", "")
            if "github.event_name == 'push'" not in str(deploy_if):
                self.violations.append(
                    {
                        "type": Violation.DEPLOY_ON_PR,
                        "severity": "ERROR",
                        "message": (
                            "Deploy job is not properly restricted to "
                            "push events only. "
                            "Deploy must have: if: github.event_name == 'push'"
                        ).strip(),
                        "details": {
                            "job": "deploy",
                            "current_if": str(deploy_if),
                            "expected_condition": "github.event_name == 'push'",
                        },
                    }
                )

    # ═══════════════════════════════════════════════════════════════════════════
    # COMPLIANCE SCORE
    # ═══════════════════════════════════════════════════════════════════════════

    def _compute_score(self) -> dict[str, Any]:
        """Compute the Architecture Compliance Score out of 100."""
        violations = self.violations
        categories: dict[str, dict[str, int]] = {
            CATEGORY_WORKFLOW_STRUCTURE: {
                "pass": 0,
                "fail": sum(
                    1
                    for v in violations
                    if v["type"]
                    in (
                        Violation.MISSING_JOB,
                        Violation.EXTRA_JOB,
                        Violation.MISSING_WORKFLOW,
                    )
                ),
            },
            CATEGORY_DEPENDENCY_GRAPH: {
                "pass": 0,
                "fail": sum(
                    1
                    for v in violations
                    if v["type"]
                    in (
                        Violation.MISSING_DEPENDENCY,
                        Violation.EXTRA_DEPENDENCY,
                        Violation.STAGE_REORDERED,
                    )
                ),
            },
            CATEGORY_SECURITY_CONTROLS: {
                "pass": 0,
                "fail": sum(
                    1 for v in violations if v["type"] == Violation.SECURITY_BYPASSED
                ),
            },
            CATEGORY_QUALITY_GATES: {
                "pass": 0,
                "fail": sum(
                    1
                    for v in violations
                    if v["type"] == Violation.QUALITY_GATE_BYPASSED
                ),
            },
            CATEGORY_DOCUMENTATION_SYNC: {
                "pass": 0,
                "fail": sum(1 for v in violations if v["type"] == Violation.DOC_SYNC),
            },
            CATEGORY_PROTECTED_FILES: {
                "pass": 0,
                "fail": sum(
                    1
                    for v in violations
                    if v["type"]
                    in (
                        Violation.MISSING_PROTECTED_FILE,
                        Violation.GUARD_REMOVED,
                        Violation.CONTRACT_DELETED,
                    )
                ),
            },
            CATEGORY_VERSION_ALIGNMENT: {
                "pass": 0,
                "fail": sum(
                    1 for v in violations if v["type"] == Violation.VERSION_MISMATCH
                ),
            },
        }

        max_score = 100
        per_category = max_score // len(categories)
        remainder = max_score % len(categories)
        total_score = 0

        breakdown: dict[str, Any] = {}
        for i, (cat_name, cat_data) in enumerate(categories.items()):
            cat_max = per_category + (1 if i < remainder else 0)
            cat_penalty = min(cat_data["fail"] * (cat_max // 2), cat_max)
            cat_score = max(cat_max - cat_penalty, 0)
            if cat_data["fail"] == 0:
                cat_data["pass"] = 1
                cat_score = cat_max
            total_score += cat_score
            breakdown[cat_name] = {
                "score": cat_score,
                "max": cat_max,
                "pass": cat_data["pass"],
                "fail": cat_data["fail"],
                "status": "PASS" if cat_data["fail"] == 0 else "FAIL",
            }

        # Final: clamp and ensure non-negative
        total_score = max(0, min(total_score, max_score))

        return {
            "total": total_score,
            "max": max_score,
            "percentage": f"{(total_score / max_score) * 100:.0f}%",
            "categories": breakdown,
        }

    # ── Reporting ─────────────────────────────────────────────────────────────

    def generate_report(self) -> dict[str, Any]:
        """Generate a comprehensive compliance report with score."""
        report: dict[str, Any] = {
            "contract_version": CONTRACT_VERSION,
            "architecture_version": ARCHITECTURE_VERSION,
            "pipeline_version": PIPELINE_VERSION,
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_violations": len(self.violations),
                "errors": sum(1 for v in self.violations if v["severity"] == "ERROR"),
                "critical": sum(
                    1 for v in self.violations if v["severity"] == "CRITICAL"
                ),
                "warnings": sum(
                    1 for v in self.violations if v["severity"] == "WARNING"
                ),
                "compliant": len(self.violations) == 0,
            },
            "expected_graph": {
                "jobs": sorted(REQUIRED_JOBS),
                "stage_order": APPROVED_STAGE_ORDER,
                "dependencies": APPROVED_DEPENDENCY_CHAIN,
                "workflow_files": sorted(REQUIRED_WORKFLOW_FILES),
            },
            "actual_graph": {
                "jobs": sorted(self.actual_jobs),
                "stage_order": self.actual_stage_order,
                "dependencies": self.actual_dependencies,
            },
            "compliance_score": self._compute_score(),
            "protected_files": sorted(PROTECTED_FILES),
            "self_protection_files": sorted(SELF_PROTECTION_FILES),
            "violations": self.violations,
        }
        # Inject compliance score properly
        report["compliance_score"] = self._compute_score()
        return report

    def print_report(self, report: dict[str, Any]) -> None:
        """Print a human-readable compliance report."""
        summary = report["summary"]
        score = report["compliance_score"]

        border = "═" * 78
        print()
        print(border)
        print("  ARCHITECTURE CONTRACT COMPLIANCE REPORT")
        print(f"  Version: {CONTRACT_VERSION}  |  Architecture: {ARCHITECTURE_VERSION}")
        print(f"  Pipeline: {PIPELINE_VERSION}  |  {report['timestamp']}")
        print(border)
        print()

        # Compliance Score
        score_line = (
            f"  COMPLIANCE SCORE:  {score['total']}/{score['max']} "
            f"({score['percentage']})"
        )
        print(score_line)
        print(f"  {'─' * 72}")
        for cat_name, cat_data in score["categories"].items():
            status_icon = "✅" if cat_data["status"] == "PASS" else "❌"
            line = (
                f"  {status_icon}  {cat_name:25s}  "
                f"{cat_data['score']:3d}/{cat_data['max']:3d}  "
                f"({cat_data['status']})"
            )
            print(line)
        print()

        # Summary
        status = "✅ COMPLIANT" if summary["compliant"] else "❌ VIOLATIONS DETECTED"
        print(f"  Status:      {status}")
        print(
            f"  Violations:  {summary['total_violations']} "
            f"(CRITICAL: {summary['critical']}, "
            f"ERROR: {summary['errors']}, "
            f"WARNING: {summary['warnings']})"
        )
        print()

        # Expected vs Actual graph
        print("  ┌─ Expected Graph ─────────────────────────────────────────────┐")
        for job in APPROVED_STAGE_ORDER:
            needs = APPROVED_DEPENDENCY_CHAIN.get(job)
            stage_label = STAGE_MAP.get(job, job)
            if needs:
                print(f"  │  {stage_label:50s} ← {', '.join(needs)}")
            else:
                print(f"  │  {stage_label:50s}  (root)")
        print(f"  └{'─' * 72}┘")
        print()

        print("  ┌─ Actual Graph ──────────────────────────────────────────────┐")
        for job in self.actual_stage_order:
            needs = self.actual_dependencies.get(job)
            stage_label = STAGE_MAP.get(job, job)
            if needs:
                print(f"  │  {stage_label:50s} ← {', '.join(needs)}")
            else:
                print(f"  │  {stage_label:50s}  (root)")
        print(f"  └{'─' * 72}┘")
        print()

        # Violations
        if self.violations:
            print(
                f"  ┌─ Violations ({len(self.violations)}) "
                f"─────────────────────────────────────────────┐"
            )
            for i, v in enumerate(self.violations, 1):
                severity_tag = {
                    "CRITICAL": "🔴",
                    "ERROR": "🟠",
                    "WARNING": "🟡",
                }.get(v["severity"], "⚪")
                print(f"  │  #{i} {severity_tag} [{v['severity']}] {v['type']}")
                print(f"  │     {v['message']}")
                print()
            print(f"  └{'─' * 72}┘")

        print()
        print(border)

    def _write_file(self, path: Path, content: str) -> None:
        safe_path = _validate_safe_path(path, Path.cwd())
        safe_path.parent.mkdir(parents=True, exist_ok=True)
        safe_path.write_text(content, encoding="utf-8")
        self.log(f"Wrote report: {path}")

    def _build_structured_report(self) -> dict[str, Any]:
        report = self.generate_report()
        summary = report["summary"]
        score = report["compliance_score"]
        categories = {
            CATEGORY_WORKFLOW_STRUCTURE: score["categories"].get(
                CATEGORY_WORKFLOW_STRUCTURE, {}
            ),
            CATEGORY_DEPENDENCY_GRAPH: score["categories"].get(
                CATEGORY_DEPENDENCY_GRAPH, {}
            ),
            CATEGORY_SECURITY_CONTROLS: score["categories"].get(
                CATEGORY_SECURITY_CONTROLS, {}
            ),
            CATEGORY_QUALITY_GATES: score["categories"].get(CATEGORY_QUALITY_GATES, {}),
            CATEGORY_DOCUMENTATION_SYNC: score["categories"].get(
                CATEGORY_DOCUMENTATION_SYNC, {}
            ),
            CATEGORY_PROTECTED_FILES: score["categories"].get(
                CATEGORY_PROTECTED_FILES, {}
            ),
            CATEGORY_VERSION_ALIGNMENT: score["categories"].get(
                CATEGORY_VERSION_ALIGNMENT, {}
            ),
        }
        category_scores = {
            name: data.get("score", 0) for name, data in categories.items()
        }
        return {
            "version": CONTRACT_VERSION,
            "timestamp": report["timestamp"],
            "repository": str(self.repo_root),
            "score": score["total"],
            "status": "COMPLIANT" if summary["compliant"] else "VIOLATIONS_DETECTED",
            "violations": {
                "critical": summary.get("critical", 0),
                "error": summary.get("errors", 0),
                "warning": summary.get("warnings", 0),
            },
            "workflow_structure": category_scores.get(CATEGORY_WORKFLOW_STRUCTURE, {}),
            "dependency_graph": category_scores.get(CATEGORY_DEPENDENCY_GRAPH, {}),
            "security_controls": category_scores.get(CATEGORY_SECURITY_CONTROLS, {}),
            "quality_gates": category_scores.get(CATEGORY_QUALITY_GATES, {}),
            "documentation_sync": category_scores.get(CATEGORY_DOCUMENTATION_SYNC, {}),
            "protected_files": category_scores.get(CATEGORY_PROTECTED_FILES, {}),
            "version_alignment": category_scores.get(CATEGORY_VERSION_ALIGNMENT, {}),
            "expected_graph": report.get("expected_graph", {}),
            "actual_graph": report.get("actual_graph", {}),
        }

    def _build_markdown_report(self, report: dict[str, Any]) -> str:
        summary = report["summary"]
        score = report["compliance_score"]
        lines: list[str] = []
        lines.append("# Architecture Compliance Report")
        lines.append("")
        lines.append(f"- **Repository:** `{self.repo_root}`")
        lines.append(f"- **Version:** {CONTRACT_VERSION}")
        lines.append(f"- **Architecture:** {ARCHITECTURE_VERSION}")
        lines.append(f"- **Pipeline:** {PIPELINE_VERSION}")
        lines.append(f"- **Timestamp:** {report['timestamp']}")
        lines.append(
            f"- **Score:** {score['total']}/{score['max']} ({score['percentage']})"
        )
        status_label = (
            "✅ COMPLIANT" if summary["compliant"] else "❌ VIOLATIONS_DETECTED"
        )
        lines.append(f"- **Status:** {status_label}")
        lines.append("")
        lines.append("## Summary")
        lines.append("")
        lines.append(
            f"Violations: {summary['total_violations']} "
            f"(CRITICAL: {summary['critical']}, "
            f"ERROR: {summary['errors']}, "
            f"WARNING: {summary['warnings']})"
        )
        lines.append("")
        lines.append("## Category Breakdown")
        lines.append("")
        lines.append("| Category | Score | Status |")
        lines.append("|----------|-------|--------|")
        for cat_name, cat_data in score["categories"].items():
            status = cat_data.get("status", "FAIL")
            score_part = f"{cat_data.get('score', 0)}/{cat_data.get('max', 0)}"
            lines.append(f"| {cat_name} | {score_part} | {status} |")
        lines.append("")
        lines.append("## Expected Graph")
        lines.append("")
        for job in APPROVED_STAGE_ORDER:
            needs = APPROVED_DEPENDENCY_CHAIN.get(job)
            stage_label = STAGE_MAP.get(job, job)
            if needs:
                lines.append(f"- {stage_label} ← {', '.join(needs)}")
            else:
                lines.append(f"- {stage_label} (root)")
        lines.append("")
        lines.append("## Actual Graph")
        lines.append("")
        for job in self.actual_stage_order:
            needs = self.actual_dependencies.get(job)
            stage_label = STAGE_MAP.get(job, job)
            if needs:
                lines.append(f"- {stage_label} ← {', '.join(needs)}")
            else:
                lines.append(f"- {stage_label} (root)")
        lines.append("")
        if self.violations:
            lines.append(f"## Violations ({len(self.violations)})")
            lines.append("")
            for i, v in enumerate(self.violations, 1):
                severity_tag = {
                    "CRITICAL": "🔴",
                    "ERROR": "🟠",
                    "WARNING": "🟡",
                }.get(v["severity"], "⚪")
                lines.append(f"### #{i} {severity_tag} [{v['severity']}] {v['type']}")
                lines.append("")
                lines.append(f"{v['message']}")
                lines.append("")
        lines.append("")
        lines.append("---")
        lines.append("*Generated by architecture contract validator.*")
        return "\n".join(lines)

    def _build_summary(self, report: dict[str, Any]) -> str:
        summary = report["summary"]
        score = report["compliance_score"]
        lines: list[str] = []
        score_text = f"{score['total']}/{score['max']} ({score['percentage']})"
        lines.append(f"Architecture Compliance: {score_text}")
        status_label = "COMPLIANT" if summary["compliant"] else "VIOLATIONS_DETECTED"
        lines.append(f"Status: {status_label}")
        lines.append(
            f"Violations: {summary['total_violations']} "
            f"(CRITICAL: {summary['critical']}, "
            f"ERROR: {summary['errors']}, "
            f"WARNING: {summary['warnings']})"
        )
        return "\n".join(lines)

    def _build_dot_graph(self) -> str:
        lines: list[str] = ["digraph architecture {"]
        lines.append("  rankdir=TB;")
        lines.append("  node [shape=box];")
        for job in APPROVED_STAGE_ORDER:
            stage_label = STAGE_MAP.get(job, job).split(" │ ", 1)[-1].strip()
            lines.append(f'  "{stage_label}";')
        for job, needs in APPROVED_DEPENDENCY_CHAIN.items():
            if not needs:
                continue
            stage_label = STAGE_MAP.get(job, job).split(" │ ", 1)[-1].strip()
            for dep in needs:
                dep_label = STAGE_MAP.get(dep, dep).split(" │ ", 1)[-1].strip()
                lines.append(f'  "{stage_label}" -> "{dep_label}";')
        lines.append("}")
        return "\n".join(lines)

    def _build_mermaid_graph(self) -> str:
        lines: list[str] = ["graph TD"]
        for job in APPROVED_STAGE_ORDER:
            stage_label = STAGE_MAP.get(job, job).split(" │ ", 1)[-1].strip()
            lines.append(f'  {job}["{stage_label}"]')
        for job, needs in APPROVED_DEPENDENCY_CHAIN.items():
            if not needs:
                continue
            for dep in needs:
                lines.append(f"  {dep} --> {job}")
        return "\n".join(lines)

    def write_all_reports(self, output_dir: Path) -> None:
        safe_dir = _validate_safe_path(output_dir, Path.cwd())
        safe_dir.mkdir(parents=True, exist_ok=True)
        report = self.generate_report()

        self._write_file(
            safe_dir / "architecture-compliance-report.json",
            json.dumps(self._build_structured_report(), indent=2, default=str),
        )
        self._write_file(
            safe_dir / "architecture-compliance-report.md",
            self._build_markdown_report(report),
        )
        self._write_file(
            safe_dir / "architecture-summary.txt",
            self._build_summary(report),
        )
        self._write_file(
            safe_dir / "architecture-dependency-graph.dot",
            self._build_dot_graph(),
        )
        self._write_file(
            safe_dir / "architecture-dependency-graph.mmd",
            self._build_mermaid_graph(),
        )

    # ── Main Validate ─────────────────────────────────────────────────────────

    def validate(self, output_dir: str | None = None) -> int:
        """
        Run all validation checks.
        Returns exit code: 0 = compliant, 1 = violations found.
        """
        try:
            self.parse_ci_yaml()
        except (FileNotFoundError, ValueError) as e:
            print(f"FATAL: {e}")
            return 1

        # Run all checks (order matters for reporting)
        self.check_protected_files()
        self.check_self_protection()
        self.check_versions()
        self.check_documentation_sync()
        self.check_required_workflow_files()
        self.check_required_jobs()
        self.check_extra_jobs()
        self.check_dependencies()
        self.check_stage_order()
        self.check_security_not_bypassed()
        self.check_quality_gate_not_bypassed()
        self.check_deploy_readiness_not_bypassed()
        self.check_deploy_not_on_pr()

        report = self.generate_report()
        self.print_report(report)

        if output_dir:
            self.write_all_reports(Path(output_dir))

        summary = report["summary"]
        if summary["critical"] > 0 or summary["errors"] > 0:
            return 1
        return 0


# ═══════════════════════════════════════════════════════════════════════════════
# CLI ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Architecture Contract Validator — enforce CI/CD pipeline structure"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python scripts/architecture_contract.py\n"
            "  python scripts/architecture_contract.py --verbose\n"
            "  python scripts/architecture_contract.py --json\n"
            "  python scripts/architecture_contract.py --strict\n"
        ),
    )
    parser.add_argument(
        "--ci-yaml",
        default=CI_YAML,
        help=f"Path to ci.yml (default: {CI_YAML})",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output report as JSON",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat WARNING-level violations as failures",
    )
    parser.add_argument(
        "--output-dir",
        default=".",
        help="Directory to write report artifacts",
    )

    args = parser.parse_args()

    validator = ArchitectureContractValidator(
        ci_yaml_path=args.ci_yaml,
        verbose=args.verbose,
    )

    exit_code = validator.validate(output_dir=args.output_dir)

    if args.json:
        report = validator.generate_report()
        print(json.dumps(report, indent=2, default=str))

    if args.strict:
        report = validator.generate_report()
        if report["summary"]["warnings"] > 0:
            print("\nSTRICT MODE: WARNING violations treated as failures.")
            exit_code = 1

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
