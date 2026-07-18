#!/usr/bin/env python3
"""Documentation Guardian - detects documentation drift.

This script validates:
- Markdown link integrity
- Required documentation files
- ADR index and collection completeness

Exit codes:
  0 - All checks passed
  1 - One or more checks failed
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

SKIP_DIRS = {
    ".github",
    ".venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".hypothesis",
    ".scannerwork",
    ".kilo",
    "staticfiles",
    "htmlcov",
    "media",
    "mutants",
    "coverage-artifacts",
    "shard-metrics-1",
    "shard-metrics-2",
    "shard-metrics-3",
    "shard-metrics-4",
    ".benchmarks",
    ".nox",
}

REQUIRED_DOCS = [
    "README.md",
    "docs/README.md",
    "docs/architecture-contract.md",
    "docs/ci-cd-pipeline.md",
    "docs/governance.md",
    "docs/architecture/README.md",
    "docs/architecture/production-architecture.md",
    "docs/architecture/adr/README.md",
    "docs/business-rules/README.md",
    "docs/ai-governance/README.md",
    "docs/ai/README.md",
]

ADR_INDEX_PATH = Path("docs") / "architecture" / "adr" / "README.md"
ADR_DIR = Path("docs") / "architecture" / "adr"


@dataclass
class CheckResult:
    """Result of a single documentation check."""

    name: str
    passed: bool
    failures: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class DocumentationGuardian:
    """Validates documentation integrity."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def _iter_markdown_files(self) -> Sequence[Path]:
        """Yield markdown files, skipping known non-doc directories."""
        for md_file in self.root.rglob("*.md"):
            if any(skip in str(md_file) for skip in SKIP_DIRS):
                continue
            yield md_file

    @staticmethod
    def _is_in_code_block(line: str, in_code_block: bool) -> tuple[bool, bool]:
        """Track fenced code block state for a line."""
        stripped = line.strip()
        if stripped.startswith("```"):
            return True, not in_code_block
        return in_code_block, in_code_block

    @staticmethod
    def _is_inline_code_link(link: str, line: str) -> bool:
        """Return True if the markdown link appears inside inline code."""
        start = line.find(f"]({link})")
        if start == -1:
            return False
        before = line[:start]
        backticks_before = before.count("`")
        return backticks_before % 2 == 1

    def check_broken_links(self) -> CheckResult:
        """Check for broken markdown links."""
        result = CheckResult(name="Broken Links", passed=True)
        broken_count = 0

        for md_file in self._iter_markdown_files():
            try:
                lines = md_file.read_text(encoding="utf-8").splitlines()
            except Exception:
                logger.warning("Error reading %s while checking links", md_file)
                continue

            in_code_block = False
            for line in lines:
                in_code_block = self._is_in_code_block(line, in_code_block)[1]
                if in_code_block:
                    continue

                links = re.findall(r"\[.*?\]\((.*?)\)", line)
                for link in links:
                    if link.startswith(("http", "#", "mailto:")):
                        continue

                    if self._is_inline_code_link(link, line):
                        continue

                    link_path = (md_file.parent / link).resolve()
                    if not link_path.exists():
                        msg = f"{md_file.relative_to(self.root)}: {link}"
                        result.failures.append(msg)
                        broken_count += 1

        if broken_count:
            result.passed = False
            result.warnings.append(f"{broken_count} broken link(s) found")

        return result

    def check_required_docs_exist(self) -> CheckResult:
        """Check that required documentation files exist."""
        result = CheckResult(name="Required Docs", passed=True)

        for rel_path in REQUIRED_DOCS:
            doc_path = self.root / rel_path
            if not doc_path.exists():
                result.passed = False
                result.failures.append(f"Missing required doc: {rel_path}")

        return result

    def check_adr_index(self) -> CheckResult:
        """Validate ADR index and collection."""
        result = CheckResult(name="ADR Index", passed=True)
        adr_index = self.root / ADR_INDEX_PATH
        adr_dir = self.root / ADR_DIR

        if not adr_index.exists():
            result.passed = False
            result.failures.append(f"Missing ADR index: {ADR_INDEX_PATH}")

        if not adr_dir.exists():
            result.passed = False
            result.failures.append(f"Missing ADR directory: {ADR_DIR}")
            return result

        adr_files = sorted(adr_dir.glob("ADR-*.md"))
        if not adr_files:
            result.passed = False
            result.failures.append(f"No ADR files found in {ADR_DIR}")

        return result

    def run_all_checks(self) -> int:
        """Run all documentation guardian checks."""
        checks = [
            ("Broken Links", self.check_broken_links),
            ("Required Docs", self.check_required_docs_exist),
            ("ADR Index", self.check_adr_index),
        ]

        results: dict[str, CheckResult] = {}
        for name, check_fn in checks:
            try:
                results[name] = check_fn()
            except Exception as exc:
                logger.exception("Unexpected error in %s check", name)
                results[name] = CheckResult(
                    name=name,
                    passed=False,
                    failures=[f"Unexpected error: {exc}"],
                )

        self._print_summary(results)

        return 0 if all(r.passed for r in results.values()) else 1

    def _print_summary(self, results: dict[str, CheckResult]) -> None:
        """Print a readable validation summary."""
        print("\n" + "-" * 44)
        print("Documentation Guardian")
        print("-" * 44)

        total_errors = 0
        for name, result in results.items():
            if result.passed:
                print(f"{name:.<25} PASS")
            else:
                failure_count = len(result.failures)
                total_errors += failure_count
                print(f"{name:.<25} FAIL ({failure_count})")
                for failure in result.failures:
                    print(f"  - {failure}")
                for warning in result.warnings:
                    print(f"  [WARN] {warning}")

        print("-" * 44)
        print(f"Total Errors ........ {total_errors}")
        print("-" * 44 + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run documentation guardian checks")
    parser.add_argument("--root", type=str, default=".", help="Repository root")
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(levelname)s: %(message)s",
    )

    guardian = DocumentationGuardian(Path(args.root).resolve())
    return guardian.run_all_checks()


if __name__ == "__main__":
    sys.exit(main())
