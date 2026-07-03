#!/usr/bin/env python3
"""Report generator for CI Guard System.

Produces markdown and JSON reports from CI execution results.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


class ReportGenerator:
    """Aggregate CI results into human-readable and machine-readable reports."""

    def __init__(self, results: list[dict[str, Any]], repo_root: Path | None = None):
        self.results = results
        self.repo_root = repo_root or Path.cwd()
        self.timestamp = datetime.now().isoformat()
        self.total = len(results)
        self.passed = sum(1 for r in results if r.get("passed"))
        self.failed = self.total - self.passed
        self.failures = [r for r in results if not r.get("passed")]

    def to_markdown(self) -> str:
        lines = []
        lines.append("# CI Guard Report")
        lines.append("")
        lines.append(f"- **Generated:** {self.timestamp}")
        lines.append(f"- **Checks:** {self.total}")
        lines.append(f"- **Passed:** {self.passed}")
        lines.append(f"- **Failed:** {self.failed}")
        lines.append("")

        if self.failures:
            lines.append("## Failures")
            lines.append("")
            for r in self.failures:
                lines.append(
                    f"- **{r.get('name', 'unknown')}** — `{r.get('command', '')}`"
                )
                if r.get("error"):
                    lines.append(f"  - Error: {r['error']}")
            lines.append("")

        lines.append("## Details")
        lines.append("")
        lines.append("| Check | Status | Command | Duration |")
        lines.append("|-------|--------|---------|----------|")
        for r in self.results:
            status = "PASS" if r.get("passed") else "FAIL"
            name = r.get("name", "unknown")
            cmd = r.get("command", "")
            dur = r.get("duration", 0)
            lines.append(f"| {name} | {status} | `{cmd}` | {dur:.2f}s |")
        lines.append("")
        return "\n".join(lines)

    def to_json(self) -> str:
        payload = {
            "timestamp": self.timestamp,
            "total": self.total,
            "passed": self.passed,
            "failed": self.failed,
            "results": self.results,
        }
        return json.dumps(payload, indent=2, default=str)

    def save(self, output_dir: Path | None = None) -> Path:
        output_dir = output_dir or self.repo_root / "reports"
        output_dir.mkdir(parents=True, exist_ok=True)

        md_path = output_dir / "ci-report.md"
        json_path = output_dir / "ci-report.json"

        md_path.write_text(self.to_markdown())
        json_path.write_text(self.to_json())

        return md_path

    def print_summary(self) -> None:
        print()
        print("=" * 80)
        if self.failed == 0:
            print("  ✅ ALL CHECKS PASSED")
        else:
            print(f"  ❌ {self.failed} CHECK(S) FAILED")
        print(f"  Total: {self.total} | Passed: {self.passed} | Failed: {self.failed}")
        print("=" * 80)
        if self.failures:
            print()
            print("FAILURES:")
            for r in self.failures:
                print(f"  - {r.get('name', 'unknown')}: {r.get('error', 'unknown')}")
            print()


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Generate CI Guard reports.")
    parser.add_argument("--json", action="store_true", help="Output JSON to stdout")
    parser.add_argument(
        "--output-dir", type=str, default=None, help="Report output directory"
    )
    args = parser.parse_args()

    default_results = [
        {"name": "placeholder", "passed": True, "command": "", "duration": 0.0}
    ]
    generator = ReportGenerator(default_results)

    if args.json:
        print(generator.to_json())
    else:
        generator.print_summary()
        out = generator.save(Path(args.output_dir) if args.output_dir else None)
        print(f"Report saved to: {out}")

    return 0 if generator.failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
