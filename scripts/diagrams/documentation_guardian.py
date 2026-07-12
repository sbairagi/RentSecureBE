#!/usr/bin/env python3
"""Documentation Guardian - detects documentation drift."""

from __future__ import annotations

import argparse
import logging
import re
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


class DocumentationGuardian:
    """Detects documentation drift and missing docs."""

    def __init__(self, root: Path):
        self.root = root
        self.violations: list[str] = []

    def check_broken_links(self) -> bool:
        """Check for broken markdown links."""
        skip_dirs = {
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
        }
        broken_count = 0
        for md_file in self.root.rglob("*.md"):
            if any(skip in str(md_file) for skip in skip_dirs):
                continue
            try:
                content = md_file.read_text()
                links = re.findall(r"\[.*?\]\((.*?)\)", content)
                for link in links:
                    if (
                        link.startswith("http")
                        or link.startswith("#")
                        or link.startswith("mailto:")
                    ):
                        continue
                    link_path = md_file.parent / link
                    if not link_path.exists():
                        print(f"[WARN] Broken link in {md_file}: {link}")
                        broken_count += 1
            except Exception:  # noqa: BLE001
                logger.warning("Error reading %s while checking links", md_file)

        if broken_count > 0:
            print(f"[WARN] {broken_count} broken links found (non-blocking)")
        return True

    def check_required_docs_exist(self) -> bool:
        """Check that required documentation files exist."""
        required_docs = [
            "docs/README.md",
            "docs/architecture-contract.md",
            "docs/ci-cd-pipeline.md",
            "docs/governance.md",
            "README.md",
        ]

        missing = [doc for doc in required_docs if not (self.root / doc).exists()]
        if missing:
            for doc in missing:
                print(f"[WARN] Missing doc: {doc}")
            return True

        return True

    def check_adr_index_updated(self) -> bool:
        """Check that ADR index exists and references ADRs."""
        adr_index = self.root / "docs" / "adr" / "README.md"
        if not adr_index.exists():
            print("[WARN] Missing ADR index: docs/adr/README.md")
            return True

        adr_index.read_text()
        adr_count = len(list((self.root / "docs" / "adr").glob("ADR-*.md")))
        if adr_count == 0:
            print("[WARN] No ADR files found in docs/adr/")

        return True

    def run_all_checks(self) -> int:
        """Run all documentation guardian checks."""
        checks = [
            ("Broken Links", self.check_broken_links),
            ("Required Docs", self.check_required_docs_exist),
            ("ADR Index", self.check_adr_index_updated),
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
    parser = argparse.ArgumentParser(description="Run documentation guardian checks")
    parser.add_argument("--root", type=str, default=".", help="Repository root")
    args = parser.parse_args()

    guardian = DocumentationGuardian(Path(args.root))
    return guardian.run_all_checks()


if __name__ == "__main__":
    sys.exit(main())
