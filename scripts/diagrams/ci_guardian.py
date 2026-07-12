#!/usr/bin/env python3
"""CI Guardian - detects duplicated workflows, CI violations, and architecture
contract drift."""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path


class CIGuardian:
    """Detects CI/CD violations and drift."""

    def __init__(self, root: Path):
        self.root = root
        self.violations: list[str] = []

    def check_duplicate_workflows(self) -> bool:
        """Check for duplicate workflow content."""
        workflows_dir = self.root / ".github" / "workflows"
        if not workflows_dir.exists():
            return True

        hashes: dict[str, list[str]] = {}
        for workflow_file in workflows_dir.glob("*.yml"):
            content = workflow_file.read_text()
            content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
            if content_hash in hashes:
                self.violations.append(
                    f"Duplicate workflow content: {workflow_file.name} == "
                    f"{hashes[content_hash][0]}"
                )
            else:
                hashes[content_hash] = [workflow_file.name]

        return len(self.violations) == 0

    def check_commit_in_workflows(self) -> bool:
        """Ensure workflows don't commit back to repo (CI loop protection)."""
        workflows_dir = self.root / ".github" / "workflows"
        if not workflows_dir.exists():
            return True

        for workflow_file in workflows_dir.glob("*.yml"):
            content = workflow_file.read_text()
            if "git commit" in content or "git push" in content:
                self.violations.append(
                    f"CI loop protection violation: {workflow_file.name} "
                    "contains git commit/push"
                )

        return len(self.violations) == 0

    def check_required_workflows_exist(self) -> bool:
        """Check that required workflows exist."""
        required = [
            "ci.yml",
            "lint.yml",
            "test.yml",
            "django-check.yml",
            "hypothesis.yml",
            "contract-tests.yml",
            "architecture.yml",
            "uml.yml",
            "uml-validation.yml",
            "security.yml",
            "security-deep.yml",
            "quality.yml",
            "performance.yml",
            "mutation.yml",
            "migration-rollback.yml",
            "deploy-readiness.yml",
            "deploy.yml",
            "nightly.yml",
            "benchmark.yml",
            "load-test.yml",
            "weekly.yml",
            "ci-metrics.yml",
            "sbom.yml",
            "rollback.yml",
            "architecture-guard.yml",
        ]

        workflows_dir = self.root / ".github" / "workflows"
        missing = [w for w in required if not (workflows_dir / w).exists()]

        if missing:
            self.violations.append(f"Missing required workflows: {', '.join(missing)}")

        return len(self.violations) == 0

    def run_all_checks(self) -> int:
        """Run all CI guardian checks."""
        checks = [
            ("Duplicate Workflows", self.check_duplicate_workflows),
            ("CI Loop Protection", self.check_commit_in_workflows),
            ("Required Workflows", self.check_required_workflows_exist),
        ]

        all_passed = True
        for name, check in checks:
            try:
                passed = check()
                status = "PASS" if passed else "FAIL"
                print(f"[{status}] {name}")
                if not passed:
                    all_passed = False
            except Exception as e:
                print(f"[ERROR] {name}: {e}")
                all_passed = False

        if self.violations:
            print("\nViolations:")
            for violation in self.violations:
                print(f"  - {violation}")

        return 0 if all_passed else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Run CI guardian checks")
    parser.add_argument("--root", type=str, default=".", help="Repository root")
    args = parser.parse_args()

    guardian = CIGuardian(Path(args.root))
    return guardian.run_all_checks()


if __name__ == "__main__":
    sys.exit(main())
