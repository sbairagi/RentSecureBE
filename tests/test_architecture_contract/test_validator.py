"""
Tests for the Architecture Contract Validator v2.0
════════════════════════════════════════════════════════════════════════════════
Enterprise-grade CI/CD governance enforcement tests.
Target: 30+ tests covering all validation categories.
"""

import tempfile
from pathlib import Path
from typing import Any

import pytest
import yaml

# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def compliant_ci_yaml() -> dict[str, Any]:
    """A CI config that matches the approved architecture contract exactly."""
    return {
        "name": "CI Pipeline",
        "on": {
            "push": {"branches": ["main"]},
            "pull_request": {"branches": ["main"]},
            "merge_group": {},
        },
        "jobs": {
            "lint-fast": {"uses": "./.github/workflows/lint.yml"},
            "test-shard-1": {
                "needs": ["lint-fast"],
                "uses": "./.github/workflows/test.yml",
                "with": {"shard": 1, "total": 4},
            },
            "test-shard-2": {
                "needs": ["lint-fast"],
                "uses": "./.github/workflows/test.yml",
                "with": {"shard": 2, "total": 4},
            },
            "test-shard-3": {
                "needs": ["lint-fast"],
                "uses": "./.github/workflows/test.yml",
                "with": {"shard": 3, "total": 4},
            },
            "test-shard-4": {
                "needs": ["lint-fast"],
                "uses": "./.github/workflows/test.yml",
                "with": {"shard": 4, "total": 4},
            },
            "shard-validation": {
                "needs": [
                    "test-shard-1",
                    "test-shard-2",
                    "test-shard-3",
                    "test-shard-4",
                ],
                "runs-on": "ubuntu-latest",
                "timeout-minutes": 15,
            },
            "contract-tests": {
                "needs": ["lint-fast"],
                "uses": "./.github/workflows/contract-tests.yml",
            },
            "django-check": {
                "needs": ["lint-fast"],
                "uses": "./.github/workflows/django-check.yml",
            },
            "hypothesis-fast": {
                "needs": ["lint-fast"],
                "uses": "./.github/workflows/hypothesis.yml",
                "with": {"hypothesis_mode": "smoke"},
            },
            "architecture": {
                "needs": ["lint-fast"],
                "uses": "./.github/workflows/architecture.yml",
            },
            "security-fast": {
                "needs": ["lint-fast"],
                "uses": "./.github/workflows/security.yml",
            },
            "mutation-smoke": {
                "needs": ["lint-fast"],
                "uses": "./.github/workflows/mutation.yml",
                "with": {"mutation_mode": "smoke"},
            },
            "migration-rollback-validation": {
                "needs": ["lint-fast"],
                "uses": "./.github/workflows/migration-rollback.yml",
            },
            "quality": {
                "needs": [
                    "test-shard-1",
                    "test-shard-2",
                    "test-shard-3",
                    "test-shard-4",
                    "shard-validation",
                    "contract-tests",
                    "architecture",
                ],
                "uses": "./.github/workflows/quality.yml",
            },
            "branch-protection": {
                "needs": ["quality", "security-fast", "django-check"],
                "uses": "./.github/workflows/branch-protection.yml",
            },
            "deploy-readiness": {
                "needs": [
                    "quality",
                    "security-fast",
                    "django-check",
                    "branch-protection",
                ],
                "uses": "./.github/workflows/deploy-readiness.yml",
            },
            "deploy": {
                "needs": ["deploy-readiness"],
                "if": "github.event_name == 'push' && github.ref == 'refs/heads/main'",
                "uses": "./.github/workflows/deploy.yml",
            },
        },
    }


@pytest.fixture
def validator():
    """Create an ArchitectureContractValidator instance."""
    from scripts.architecture_contract import ArchitectureContractValidator

    val = ArchitectureContractValidator(verbose=False)
    val.repo_root = Path.cwd()
    return val


# ═══════════════════════════════════════════════════════════════════════════════
# Helper
# ═══════════════════════════════════════════════════════════════════════════════


def write_temp_env(
    content: dict[str, Any], extra_files: list[str] | None = None
) -> str:
    """Write a temporary environment with ci.yml and stub workflow files."""
    tmpdir = tempfile.mkdtemp()
    workflow_dir = Path(tmpdir) / ".github" / "workflows"
    workflow_dir.mkdir(parents=True, exist_ok=True)
    ci_path = workflow_dir / "ci.yml"
    with open(ci_path, "w") as f:
        yaml.dump(content, f, default_flow_style=False)

    # Stub workflow files
    required_files = [
        "lint.yml",
        "test.yml",
        "django-check.yml",
        "hypothesis.yml",
        "contract-tests.yml",
        "architecture.yml",
        "security.yml",
        "security-deep.yml",
        "quality.yml",
        "performance.yml",
        "mutation.yml",
        "migration-rollback.yml",
        "branch-protection.yml",
        "deploy-readiness.yml",
        "deploy.yml",
        "nightly.yml",
        "architecture-guard.yml",
        "benchmark.yml",
        "load-test.yml",
        "weekly.yml",
        "ci-metrics.yml",
        "sbom.yml",
        "rollback.yml",
    ]
    for fname in required_files:
        stub = workflow_dir / fname
        stub.write_text(
            "name: stub\non: workflow_call\njobs:\n  stub:\n    runs-on: ubuntu-latest\n    steps:\n      - run: echo stub\n"
        )

    # Stub scripts + docs
    script_dir = Path(tmpdir) / "scripts"
    script_dir.mkdir(exist_ok=True)
    contract_script = script_dir / "architecture_contract.py"
    contract_script.write_text("# version 2.0.0 — placeholder\n")

    doc_dir = Path(tmpdir) / "docs"
    doc_dir.mkdir(exist_ok=True)

    # Write doc files with all required content
    arc_contract_doc = doc_dir / "architecture-contract.md"
    arc_contract_doc.write_text(
        "# Architecture Contract\n\n> **Version:** 2.3.0\n\nSome content with 2.3.0 version.\n"
    )

    pipeline_doc = doc_dir / "ci-cd-pipeline.md"
    pipeline_doc.write_text(
        "# CI/CD Pipeline & UML Overview\n\n"
        "> **Pipeline Version:** 2.3.0\n\n"
        "## Part 1: CI/CD Pipeline Flow Diagram\n\n"
        "### Setup\n"
        "### Code Quality\n"
        "### Tests\n"
        "### Django Checks\n"
        "### Architecture\n"
        "### Security\n"
        "### Quality Gate\n"
        "### Deploy\n"
    )

    governance_doc = doc_dir / "governance.md"
    governance_doc.write_text(
        "# Enterprise CI/CD Governance\n\n> **Version:** 2.3.0\n\n"
    )

    # Add extra files if specified
    if extra_files:
        for fpath in extra_files:
            f = Path(tmpdir) / fpath
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text("placeholder\n")

    return tmpdir


# ═══════════════════════════════════════════════════════════════════════════════
# TESTS: Protected Files (Requirement 1)
# ═══════════════════════════════════════════════════════════════════════════════


class TestProtectedFiles:
    def test_all_protected_files_exist(self, validator, compliant_ci_yaml):
        """Should not report violations when all protected files exist."""
        tmpdir = write_temp_env(compliant_ci_yaml)
        validator.repo_root = Path(tmpdir)
        validator.ci_yaml_path = Path(tmpdir) / ".github" / "workflows" / "ci.yml"
        validator.parse_ci_yaml()
        validator.check_protected_files()
        violations = [
            v for v in validator.violations if v["type"] == "missing_protected_file"
        ]
        assert len(violations) == 0

    def test_missing_protected_file_is_critical(self, validator, compliant_ci_yaml):
        """Missing protected file should be CRITICAL severity."""
        tmpdir = write_temp_env(compliant_ci_yaml)
        # Delete a protected file
        (Path(tmpdir) / "docs" / "governance.md").unlink()
        validator.repo_root = Path(tmpdir)
        validator.ci_yaml_path = Path(tmpdir) / ".github" / "workflows" / "ci.yml"
        validator.parse_ci_yaml()
        validator.check_protected_files()
        violations = [
            v for v in validator.violations if v["type"] == "missing_protected_file"
        ]
        assert len(violations) == 1
        assert violations[0]["severity"] == "CRITICAL"

    def test_missing_deploy_yml_protected(self, validator, compliant_ci_yaml):
        """Missing deploy.yml should be caught as protected file."""
        tmpdir = write_temp_env(compliant_ci_yaml)
        (Path(tmpdir) / ".github" / "workflows" / "deploy.yml").unlink()
        validator.repo_root = Path(tmpdir)
        validator.ci_yaml_path = Path(tmpdir) / ".github" / "workflows" / "ci.yml"
        validator.parse_ci_yaml()
        validator.check_protected_files()
        violations = [
            v for v in validator.violations if v["type"] == "missing_protected_file"
        ]
        assert any("deploy.yml" in v["message"] for v in violations)


# ═══════════════════════════════════════════════════════════════════════════════
# TESTS: Architecture Version Enforcement (Requirement 2)
# ═══════════════════════════════════════════════════════════════════════════════


class TestVersionEnforcement:
    def test_versions_aligned(self, validator, compliant_ci_yaml):
        """No violation when all versions match."""
        tmpdir = write_temp_env(compliant_ci_yaml)
        validator.repo_root = Path(tmpdir)
        validator.ci_yaml_path = Path(tmpdir) / ".github" / "workflows" / "ci.yml"
        validator.parse_ci_yaml()
        validator.check_versions()
        violations = [
            v for v in validator.violations if v["type"] == "version_mismatch"
        ]
        assert len(violations) == 0

    def test_version_in_docs(self, validator, compliant_ci_yaml):
        """Version must appear in architecture-contract.md docs."""
        tmpdir = write_temp_env(compliant_ci_yaml)
        # Write docs without the version
        doc_dir = Path(tmpdir) / "docs"
        (doc_dir / "architecture-contract.md").write_text("# No version here\n")
        validator.repo_root = Path(tmpdir)
        validator.ci_yaml_path = Path(tmpdir) / ".github" / "workflows" / "ci.yml"
        validator.parse_ci_yaml()
        validator.check_versions()
        violations = [
            v for v in validator.violations if v["type"] == "version_mismatch"
        ]
        # The doc version check is CRITICAL
        assert any("architecture-contract.md" in v["message"] for v in violations)

    def test_version_in_pipeline_docs(self, validator, compliant_ci_yaml):
        """Version must appear in ci-cd-pipeline.md docs."""
        tmpdir = write_temp_env(compliant_ci_yaml)
        doc_dir = Path(tmpdir) / "docs"
        (doc_dir / "ci-cd-pipeline.md").write_text("# No version here\n")
        validator.repo_root = Path(tmpdir)
        validator.ci_yaml_path = Path(tmpdir) / ".github" / "workflows" / "ci.yml"
        validator.parse_ci_yaml()
        validator.check_versions()
        violations = [
            v for v in validator.violations if v["type"] == "version_mismatch"
        ]
        assert any("ci-cd-pipeline.md" in v["message"] for v in violations)


# ═══════════════════════════════════════════════════════════════════════════════
# TESTS: Documentation Synchronization (Requirement 3)
# ═══════════════════════════════════════════════════════════════════════════════


class TestDocumentationSync:
    def test_docs_synced(self, validator, compliant_ci_yaml):
        """No violation when docs contain all required stages."""
        tmpdir = write_temp_env(compliant_ci_yaml)
        validator.repo_root = Path(tmpdir)
        validator.ci_yaml_path = Path(tmpdir) / ".github" / "workflows" / "ci.yml"
        validator.parse_ci_yaml()
        validator.check_documentation_sync()
        violations = [
            v for v in validator.violations if v["type"] == "documentation_out_of_sync"
        ]
        assert len(violations) == 0

    def test_missing_stage_in_docs(self, validator, compliant_ci_yaml):
        """Missing a stage in docs should generate ERROR."""
        tmpdir = write_temp_env(compliant_ci_yaml)
        doc_dir = Path(tmpdir) / "docs"
        # Write docs missing all stages
        (doc_dir / "ci-cd-pipeline.md").write_text("# Pipeline\n")
        validator.repo_root = Path(tmpdir)
        validator.ci_yaml_path = Path(tmpdir) / ".github" / "workflows" / "ci.yml"
        validator.parse_ci_yaml()
        validator.check_documentation_sync()
        violations = [
            v for v in validator.violations if v["type"] == "documentation_out_of_sync"
        ]
        assert len(violations) > 0
        assert violations[0]["severity"] == "ERROR"

    def test_doc_sync_missing_file(self, validator, compliant_ci_yaml):
        """Missing docs file should be reported."""
        tmpdir = write_temp_env(compliant_ci_yaml)
        (Path(tmpdir) / "docs" / "ci-cd-pipeline.md").unlink()
        validator.repo_root = Path(tmpdir)
        validator.ci_yaml_path = Path(tmpdir) / ".github" / "workflows" / "ci.yml"
        validator.parse_ci_yaml()
        validator.check_documentation_sync()
        violations = [
            v for v in validator.violations if v["type"] == "documentation_out_of_sync"
        ]
        assert len(violations) == 1


# ═══════════════════════════════════════════════════════════════════════════════
# TESTS: Contract Self-Protection (Requirement 4)
# ═══════════════════════════════════════════════════════════════════════════════


class TestSelfProtection:
    def test_guard_present(self, validator, compliant_ci_yaml):
        """Should not report violations when guard and contract are present."""
        tmpdir = write_temp_env(compliant_ci_yaml)
        validator.repo_root = Path(tmpdir)
        validator.ci_yaml_path = Path(tmpdir) / ".github" / "workflows" / "ci.yml"
        validator.parse_ci_yaml()
        validator.check_self_protection()
        violations = [
            v
            for v in validator.violations
            if v["type"] in ("architecture_guard_removed", "contract_deleted")
        ]
        assert len(violations) == 0

    def test_guard_removed_critical(self, validator, compliant_ci_yaml):
        """Removing architecture-guard.yml should be CRITICAL."""
        tmpdir = write_temp_env(compliant_ci_yaml)
        (Path(tmpdir) / ".github" / "workflows" / "architecture-guard.yml").unlink()
        validator.repo_root = Path(tmpdir)
        validator.ci_yaml_path = Path(tmpdir) / ".github" / "workflows" / "ci.yml"
        validator.parse_ci_yaml()
        validator.check_self_protection()
        violations = [
            v for v in validator.violations if v["type"] == "architecture_guard_removed"
        ]
        assert len(violations) == 1
        assert violations[0]["severity"] == "CRITICAL"

    def test_contract_deleted_critical(self, validator, compliant_ci_yaml):
        """Removing architecture_contract.py should be CRITICAL."""
        tmpdir = write_temp_env(compliant_ci_yaml)
        (Path(tmpdir) / "scripts" / "architecture_contract.py").unlink()
        validator.repo_root = Path(tmpdir)
        validator.ci_yaml_path = Path(tmpdir) / ".github" / "workflows" / "ci.yml"
        validator.parse_ci_yaml()
        validator.check_self_protection()
        violations = [
            v for v in validator.violations if v["type"] == "contract_deleted"
        ]
        assert len(violations) == 1
        assert violations[0]["severity"] == "CRITICAL"


# ═══════════════════════════════════════════════════════════════════════════════
# TESTS: Compliance Score (Requirement 6)
# ═══════════════════════════════════════════════════════════════════════════════


class TestComplianceScore:
    def test_score_100_when_compliant(self, validator, compliant_ci_yaml):
        """Compliant pipeline should score 100/100."""
        tmpdir = write_temp_env(compliant_ci_yaml)
        validator.repo_root = Path(tmpdir)
        validator.ci_yaml_path = Path(tmpdir) / ".github" / "workflows" / "ci.yml"
        validator.validate()
        report = validator.generate_report()
        score = report["compliance_score"]
        assert score["total"] == 100
        assert score["max"] == 100
        assert score["percentage"] == "100%"

    def test_score_reduced_with_violations(self, validator, compliant_ci_yaml):
        """Pipeline with violations should score less than 100."""
        tmpdir = write_temp_env(compliant_ci_yaml)
        # Remove a protected file
        (Path(tmpdir) / "docs" / "governance.md").unlink()
        validator.repo_root = Path(tmpdir)
        validator.ci_yaml_path = Path(tmpdir) / ".github" / "workflows" / "ci.yml"
        validator.parse_ci_yaml()
        validator.check_protected_files()
        report = validator.generate_report()
        score = report["compliance_score"]
        assert score["total"] < 100

    def test_score_categories_present(self, validator, compliant_ci_yaml):
        """Score should have all 7 categories."""
        tmpdir = write_temp_env(compliant_ci_yaml)
        validator.repo_root = Path(tmpdir)
        validator.ci_yaml_path = Path(tmpdir) / ".github" / "workflows" / "ci.yml"
        validator.validate()
        report = validator.generate_report()
        score = report["compliance_score"]
        expected_categories = [
            "Workflow Structure",
            "Dependency Graph",
            "Security Controls",
            "Quality Gates",
            "Documentation Sync",
            "Protected Files",
            "Version Alignment",
        ]
        for cat in expected_categories:
            assert cat in score["categories"], f"Missing category: {cat}"


# ═══════════════════════════════════════════════════════════════════════════════
# TESTS: Parsing
# ═══════════════════════════════════════════════════════════════════════════════


class TestParsing:
    def test_parse_compliant_ci(self, compliant_ci_yaml):
        """Should parse a compliant ci.yml without errors."""
        tmpdir = write_temp_env(compliant_ci_yaml)
        from scripts.architecture_contract import ArchitectureContractValidator

        val = ArchitectureContractValidator(
            ci_yaml_path=str(Path(tmpdir) / ".github" / "workflows" / "ci.yml"),
            verbose=False,
        )
        val.repo_root = Path(tmpdir)
        config = val.parse_ci_yaml()
        assert config["name"] == "CI Pipeline"
        assert len(val.actual_jobs) == 17
        assert "lint-fast" in val.actual_jobs
        assert "deploy" in val.actual_jobs

    def test_parse_missing_file(self):
        """Should raise FileNotFoundError for missing ci.yml."""
        from scripts.architecture_contract import ArchitectureContractValidator

        val = ArchitectureContractValidator(
            ci_yaml_path="/nonexistent/path/ci.yml", verbose=False
        )
        with pytest.raises(FileNotFoundError):
            val.parse_ci_yaml()

    def test_parse_empty_yaml(self):
        """Should raise ValueError for empty YAML."""
        tmpdir = tempfile.mkdtemp()
        ci_path = Path(tmpdir) / "ci.yml"
        ci_path.write_text("")
        from scripts.architecture_contract import ArchitectureContractValidator

        val = ArchitectureContractValidator(ci_yaml_path=str(ci_path), verbose=False)
        with pytest.raises(ValueError):
            val.parse_ci_yaml()


# ═══════════════════════════════════════════════════════════════════════════════
# TESTS: Required Jobs
# ═══════════════════════════════════════════════════════════════════════════════


class TestRequiredJobs:
    def test_all_jobs_present(self, validator, compliant_ci_yaml):
        """Should not report violations when all required jobs are present."""
        tmpdir = write_temp_env(compliant_ci_yaml)
        validator.repo_root = Path(tmpdir)
        validator.ci_yaml_path = Path(tmpdir) / ".github" / "workflows" / "ci.yml"
        validator.parse_ci_yaml()
        validator.check_required_jobs()
        job_violations = [v for v in validator.violations if v["type"] == "missing_job"]
        assert len(job_violations) == 0

    def test_missing_job_detected(self, validator):
        """Should report violation when a required job is missing."""
        broken = {
            "name": "CI Pipeline",
            "on": {"push": {"branches": ["main"]}},
            "jobs": {
                "lint-fast": {"uses": "./lint.yml"},
                "test-shard-1": {"needs": "lint-fast", "uses": "./test.yml"},
            },
        }
        tmpdir = write_temp_env(broken)
        validator.repo_root = Path(tmpdir)
        validator.ci_yaml_path = Path(tmpdir) / ".github" / "workflows" / "ci.yml"
        validator.parse_ci_yaml()
        validator.check_required_jobs()
        job_violations = [v for v in validator.violations if v["type"] == "missing_job"]
        assert len(job_violations) >= 10


# ═══════════════════════════════════════════════════════════════════════════════
# TESTS: Required Workflow Files
# ═══════════════════════════════════════════════════════════════════════════════


class TestRequiredWorkflowFiles:
    def test_all_workflow_files_present(self, validator, compliant_ci_yaml):
        """Should not report violations when all workflow files exist."""
        tmpdir = write_temp_env(compliant_ci_yaml)
        validator.repo_root = Path(tmpdir)
        validator.ci_yaml_path = Path(tmpdir) / ".github" / "workflows" / "ci.yml"
        validator.parse_ci_yaml()
        validator.check_required_workflow_files()
        violations = [
            v for v in validator.violations if v["type"] == "missing_workflow"
        ]
        assert len(violations) == 0

    def test_missing_workflow_file_detected(self, validator, compliant_ci_yaml):
        """Should report violation when a workflow file is missing."""
        tmpdir = write_temp_env(compliant_ci_yaml)
        (Path(tmpdir) / ".github" / "workflows" / "security.yml").unlink()
        validator.repo_root = Path(tmpdir)
        validator.ci_yaml_path = Path(tmpdir) / ".github" / "workflows" / "ci.yml"
        validator.parse_ci_yaml()
        validator.check_required_workflow_files()
        violations = [
            v for v in validator.violations if v["type"] == "missing_workflow"
        ]
        assert len(violations) == 1
        assert "security.yml" in violations[0]["message"]


# ═══════════════════════════════════════════════════════════════════════════════
# TESTS: Dependencies
# ═══════════════════════════════════════════════════════════════════════════════


class TestDependencies:
    def test_compliant_dependencies(self, validator, compliant_ci_yaml):
        """Should not report violations when dependencies match the contract."""
        tmpdir = write_temp_env(compliant_ci_yaml)
        validator.repo_root = Path(tmpdir)
        validator.ci_yaml_path = Path(tmpdir) / ".github" / "workflows" / "ci.yml"
        validator.parse_ci_yaml()
        validator.check_dependencies()
        violations = [v for v in validator.violations if "dependency" in v["type"]]
        assert len(violations) == 0

    def test_changed_dependency_detected(self, validator):
        """Should report violation when a dependency is changed."""
        broken = {
            "name": "CI Pipeline",
            "on": {"push": {"branches": ["main"]}},
            "jobs": {
                "lint-fast": {"uses": "./lint.yml"},
                "test-shard-1": {"needs": "lint-fast", "uses": "./test.yml"},
                "hypothesis-fast": {"needs": "lint-fast", "uses": "./hypothesis.yml"},
                "contract-tests": {"needs": "lint", "uses": "./contract-tests.yml"},
                "mutation-smoke": {"needs": "lint-fast", "uses": "./mutation.yml"},
                "performance": {"needs": "lint", "uses": "./performance.yml"},
                "django-check": {"needs": "lint", "uses": "./django-check.yml"},
                "architecture": {"needs": "lint", "uses": "./architecture.yml"},
                "security-fast": {"needs": "architecture", "uses": "./security.yml"},
                "quality": {
                    "needs": ["test", "contract-tests"],
                    "uses": "./quality.yml",
                },
                "deploy-readiness": {
                    "needs": [
                        "security-fast",
                        "quality",
                        "performance",
                        "mutation-smoke",
                    ],
                    "uses": "./deploy-readiness.yml",
                },
                "deploy": {"needs": "deploy-readiness", "uses": "./deploy.yml"},
            },
        }
        tmpdir = write_temp_env(broken)
        validator.repo_root = Path(tmpdir)
        validator.ci_yaml_path = Path(tmpdir) / ".github" / "workflows" / "ci.yml"
        validator.parse_ci_yaml()
        validator.check_dependencies()
        violations = [v for v in validator.violations if "dependency" in v["type"]]
        assert len(violations) >= 1

    def test_removed_dependency_detected(self, validator):
        """Should report violation when a dependency is removed."""
        broken = {
            "name": "CI Pipeline",
            "on": {"push": {"branches": ["main"]}},
            "jobs": {
                "lint-fast": {"uses": "./lint.yml"},
                "test-shard-1": {"needs": "lint-fast", "uses": "./test.yml"},
                "hypothesis-fast": {"needs": "lint-fast", "uses": "./hypothesis.yml"},
                "contract-tests": {"uses": "./contract-tests.yml"},
                "mutation-smoke": {"needs": "lint-fast", "uses": "./mutation.yml"},
                "performance": {"needs": "lint", "uses": "./performance.yml"},
                "django-check": {"needs": "lint", "uses": "./django-check.yml"},
                "architecture": {"needs": "django-check", "uses": "./architecture.yml"},
                "security-fast": {"needs": "architecture", "uses": "./security.yml"},
                "quality": {
                    "needs": ["test", "contract-tests"],
                    "uses": "./quality.yml",
                },
                "deploy-readiness": {
                    "needs": [
                        "security-fast",
                        "quality",
                        "performance",
                        "mutation-smoke",
                    ],
                    "uses": "./deploy-readiness.yml",
                },
                "deploy": {"needs": "deploy-readiness", "uses": "./deploy.yml"},
            },
        }
        tmpdir = write_temp_env(broken)
        validator.repo_root = Path(tmpdir)
        validator.ci_yaml_path = Path(tmpdir) / ".github" / "workflows" / "ci.yml"
        validator.parse_ci_yaml()
        validator.check_dependencies()
        violations = [v for v in validator.violations if "dependency" in v["type"]]
        assert len(violations) >= 1


# ═══════════════════════════════════════════════════════════════════════════════
# TESTS: Bypass Protections
# ═══════════════════════════════════════════════════════════════════════════════


class TestBypassProtections:
    def test_security_bypass_detected(self, validator):
        """Security bypass should be CRITICAL."""
        broken = {
            "name": "CI Pipeline",
            "on": {"push": {"branches": ["main"]}},
            "jobs": {
                "lint-fast": {"uses": "./lint.yml"},
                "test-shard-1": {"needs": "lint-fast", "uses": "./test.yml"},
                "hypothesis-fast": {"needs": "lint-fast", "uses": "./hypothesis.yml"},
                "contract-tests": {"needs": "lint", "uses": "./contract-tests.yml"},
                "mutation-smoke": {"needs": "lint-fast", "uses": "./mutation.yml"},
                "performance": {"needs": "lint", "uses": "./performance.yml"},
                "django-check": {"needs": "lint", "uses": "./django-check.yml"},
                "architecture": {"needs": "django-check", "uses": "./architecture.yml"},
                "security-fast": {"uses": "./security.yml"},
                "quality": {
                    "needs": ["test", "contract-tests"],
                    "uses": "./quality.yml",
                },
                "deploy-readiness": {
                    "needs": [
                        "security-fast",
                        "quality",
                        "performance",
                        "mutation-smoke",
                    ],
                    "uses": "./deploy-readiness.yml",
                },
                "deploy": {"needs": "deploy-readiness", "uses": "./deploy.yml"},
            },
        }
        tmpdir = write_temp_env(broken)
        validator.repo_root = Path(tmpdir)
        validator.ci_yaml_path = Path(tmpdir) / ".github" / "workflows" / "ci.yml"
        validator.parse_ci_yaml()
        validator.check_security_not_bypassed()
        violations = [
            v for v in validator.violations if v["type"] == "security_bypassed"
        ]
        assert len(violations) >= 1
        assert violations[0]["severity"] == "CRITICAL"

    def test_quality_gate_bypass_detected(self, validator):
        """Quality gate bypass should be CRITICAL."""
        broken = {
            "name": "CI Pipeline",
            "on": {"push": {"branches": ["main"]}},
            "jobs": {
                "lint-fast": {"uses": "./lint.yml"},
                "test-shard-1": {"needs": "lint-fast", "uses": "./test.yml"},
                "hypothesis-fast": {"needs": "lint-fast", "uses": "./hypothesis.yml"},
                "contract-tests": {"needs": "lint", "uses": "./contract-tests.yml"},
                "mutation-smoke": {"needs": "lint-fast", "uses": "./mutation.yml"},
                "performance": {"needs": "lint", "uses": "./performance.yml"},
                "django-check": {"needs": "lint", "uses": "./django-check.yml"},
                "architecture": {"needs": "django-check", "uses": "./architecture.yml"},
                "security-fast": {"needs": "architecture", "uses": "./security.yml"},
                "quality": {"uses": "./quality.yml"},
                "deploy-readiness": {
                    "needs": [
                        "security-fast",
                        "quality",
                        "performance",
                        "mutation-smoke",
                    ],
                    "uses": "./deploy-readiness.yml",
                },
                "deploy": {"needs": "deploy-readiness", "uses": "./deploy.yml"},
            },
        }
        tmpdir = write_temp_env(broken)
        validator.repo_root = Path(tmpdir)
        validator.ci_yaml_path = Path(tmpdir) / ".github" / "workflows" / "ci.yml"
        validator.parse_ci_yaml()
        validator.check_quality_gate_not_bypassed()
        violations = [
            v for v in validator.violations if v["type"] == "quality_gate_bypassed"
        ]
        assert len(violations) >= 1
        assert violations[0]["severity"] == "CRITICAL"

    def test_deploy_readiness_bypass_detected(self, validator):
        """Deploy readiness bypass should be CRITICAL."""
        broken = {
            "name": "CI Pipeline",
            "on": {"push": {"branches": ["main"]}},
            "jobs": {
                "lint-fast": {"uses": "./lint.yml"},
                "test-shard-1": {"needs": "lint-fast", "uses": "./test.yml"},
                "hypothesis-fast": {"needs": "lint-fast", "uses": "./hypothesis.yml"},
                "contract-tests": {"needs": "lint", "uses": "./contract-tests.yml"},
                "mutation-smoke": {"needs": "lint-fast", "uses": "./mutation.yml"},
                "performance": {"needs": "lint", "uses": "./performance.yml"},
                "django-check": {"needs": "lint", "uses": "./django-check.yml"},
                "architecture": {"needs": "django-check", "uses": "./architecture.yml"},
                "security-fast": {"needs": "architecture", "uses": "./security.yml"},
                "quality": {
                    "needs": ["test", "contract-tests"],
                    "uses": "./quality.yml",
                },
                "deploy-readiness": {"uses": "./deploy-readiness.yml"},
                "deploy": {"needs": "deploy-readiness", "uses": "./deploy.yml"},
            },
        }
        tmpdir = write_temp_env(broken)
        validator.repo_root = Path(tmpdir)
        validator.ci_yaml_path = Path(tmpdir) / ".github" / "workflows" / "ci.yml"
        validator.parse_ci_yaml()
        validator.check_deploy_readiness_not_bypassed()
        violations = [
            v for v in validator.violations if v["type"] == "deploy_readiness_bypassed"
        ]
        assert len(violations) >= 1
        assert violations[0]["severity"] == "CRITICAL"


# ═══════════════════════════════════════════════════════════════════════════════
# TESTS: Stage Ordering
# ═══════════════════════════════════════════════════════════════════════════════


class TestStageOrdering:
    def test_compliant_stage_order(self, validator, compliant_ci_yaml):
        """Should not report stage violations for compliant pipeline."""
        tmpdir = write_temp_env(compliant_ci_yaml)
        validator.repo_root = Path(tmpdir)
        validator.ci_yaml_path = Path(tmpdir) / ".github" / "workflows" / "ci.yml"
        validator.parse_ci_yaml()
        validator.check_stage_order()
        violations = [v for v in validator.violations if v["type"] == "stage_reordered"]
        assert len(violations) == 0

    def test_reversed_dependency_detected(self, validator):
        """Reversed architecture/security dependency should be caught."""
        broken = {
            "name": "CI Pipeline",
            "on": {"push": {"branches": ["main"]}},
            "jobs": {
                "lint-fast": {"uses": "./lint.yml"},
                "test-shard-1": {"needs": "lint-fast", "uses": "./test.yml"},
                "hypothesis-fast": {"needs": "lint-fast", "uses": "./hypothesis.yml"},
                "contract-tests": {"needs": "lint", "uses": "./contract-tests.yml"},
                "mutation-smoke": {"needs": "lint-fast", "uses": "./mutation.yml"},
                "performance": {"needs": "lint", "uses": "./performance.yml"},
                "django-check": {"needs": "lint", "uses": "./django-check.yml"},
                "security-fast": {"needs": "django-check", "uses": "./security.yml"},
                "architecture": {"needs": "security", "uses": "./architecture.yml"},
                "quality": {
                    "needs": ["test", "contract-tests"],
                    "uses": "./quality.yml",
                },
                "deploy-readiness": {
                    "needs": [
                        "security-fast",
                        "quality",
                        "performance",
                        "mutation-smoke",
                    ],
                    "uses": "./deploy-readiness.yml",
                },
                "deploy": {"needs": "deploy-readiness", "uses": "./deploy.yml"},
            },
        }
        tmpdir = write_temp_env(broken)
        validator.repo_root = Path(tmpdir)
        validator.ci_yaml_path = Path(tmpdir) / ".github" / "workflows" / "ci.yml"
        validator.parse_ci_yaml()
        validator.check_stage_order()
        violations = [v for v in validator.violations if v["type"] == "stage_reordered"]
        assert len(violations) >= 1


# ═══════════════════════════════════════════════════════════════════════════════
# TESTS: Deploy on PR
# ═══════════════════════════════════════════════════════════════════════════════


class TestDeployOnPR:
    def test_deploy_restricted_to_push(self, validator, compliant_ci_yaml):
        """Should not report if deploy is properly restricted."""
        tmpdir = write_temp_env(compliant_ci_yaml)
        validator.repo_root = Path(tmpdir)
        validator.ci_yaml_path = Path(tmpdir) / ".github" / "workflows" / "ci.yml"
        validator.parse_ci_yaml()
        validator.check_deploy_not_on_pr()
        violations = [v for v in validator.violations if v["type"] == "deploy_on_pr"]
        assert len(violations) == 0

    def test_deploy_without_restriction_detected(self, validator):
        """Deploy without 'if' restriction should be caught."""
        broken = {
            "name": "CI Pipeline",
            "on": {"push": {"branches": ["main"]}},
            "jobs": {
                "lint-fast": {"uses": "./lint.yml"},
                "test-shard-1": {"needs": "lint-fast", "uses": "./test.yml"},
                "hypothesis-fast": {"needs": "lint-fast", "uses": "./hypothesis.yml"},
                "contract-tests": {"needs": "lint", "uses": "./contract-tests.yml"},
                "mutation-smoke": {"needs": "lint-fast", "uses": "./mutation.yml"},
                "performance": {"needs": "lint", "uses": "./performance.yml"},
                "django-check": {"needs": "lint", "uses": "./django-check.yml"},
                "architecture": {"needs": "django-check", "uses": "./architecture.yml"},
                "security-fast": {"needs": "architecture", "uses": "./security.yml"},
                "quality": {
                    "needs": ["test", "contract-tests"],
                    "uses": "./quality.yml",
                },
                "deploy-readiness": {
                    "needs": [
                        "security-fast",
                        "quality",
                        "performance",
                        "mutation-smoke",
                    ],
                    "uses": "./deploy-readiness.yml",
                },
                "deploy": {"needs": "deploy-readiness", "uses": "./deploy.yml"},
            },
        }
        tmpdir = write_temp_env(broken)
        validator.repo_root = Path(tmpdir)
        validator.ci_yaml_path = Path(tmpdir) / ".github" / "workflows" / "ci.yml"
        validator.parse_ci_yaml()
        validator.check_deploy_not_on_pr()
        violations = [v for v in validator.violations if v["type"] == "deploy_on_pr"]
        assert len(violations) >= 1


# ═══════════════════════════════════════════════════════════════════════════════
# TESTS: Full Validation
# ═══════════════════════════════════════════════════════════════════════════════


class TestFullValidation:
    def test_compliant_pipeline_exit_zero(self, validator, compliant_ci_yaml):
        """A fully compliant pipeline should return exit code 0."""
        tmpdir = write_temp_env(compliant_ci_yaml)
        validator.repo_root = Path(tmpdir)
        validator.ci_yaml_path = Path(tmpdir) / ".github" / "workflows" / "ci.yml"
        exit_code = validator.validate()
        assert exit_code == 0

    def test_broken_pipeline_exit_one(self, validator):
        """A broken pipeline should return exit code 1."""
        broken = {
            "name": "CI Pipeline",
            "on": {"push": {"branches": ["main"]}},
            "jobs": {"lint": {"uses": "./lint.yml"}},
        }
        tmpdir = write_temp_env(broken)
        validator.repo_root = Path(tmpdir)
        validator.ci_yaml_path = Path(tmpdir) / ".github" / "workflows" / "ci.yml"
        exit_code = validator.validate()
        assert exit_code == 1

    def test_report_contains_score(self, validator, compliant_ci_yaml):
        """Report should contain compliance score."""
        tmpdir = write_temp_env(compliant_ci_yaml)
        validator.repo_root = Path(tmpdir)
        validator.ci_yaml_path = Path(tmpdir) / ".github" / "workflows" / "ci.yml"
        validator.validate()
        report = validator.generate_report()
        assert "compliance_score" in report
        assert "total" in report["compliance_score"]
        assert "categories" in report["compliance_score"]

    def test_report_contains_self_protection(self, validator, compliant_ci_yaml):
        """Report should contain self-protection file lists."""
        tmpdir = write_temp_env(compliant_ci_yaml)
        validator.repo_root = Path(tmpdir)
        validator.ci_yaml_path = Path(tmpdir) / ".github" / "workflows" / "ci.yml"
        validator.validate()
        report = validator.generate_report()
        assert "self_protection_files" in report
        assert "protected_files" in report


# ═══════════════════════════════════════════════════════════════════════════════
# TESTS: Topological Order
# ═══════════════════════════════════════════════════════════════════════════════


class TestTopologicalOrder:
    def test_topological_sort_correct(self):
        """The topological sort should produce correct order."""
        from scripts.architecture_contract import ArchitectureContractValidator

        deps = {
            "deploy": ["deploy-readiness"],
            "deploy-readiness": ["security-fast", "quality"],
            "security-fast": ["architecture"],
            "architecture": ["django-check"],
            "django-check": ["lint"],
            "quality": ["test"],
            "test": ["lint"],
            "lint": None,
        }
        result = ArchitectureContractValidator._topological_order(deps)
        assert result[0] == "lint"
        assert result[-1] == "deploy"
        assert set(result) == set(deps.keys())
