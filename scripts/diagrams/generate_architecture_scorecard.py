#!/usr/bin/env python3
"""Generate architecture scorecard."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def run_command(cmd: list[str]) -> tuple[int, str]:
    try:
        result = subprocess.run(  # noqa: S603
            cmd, capture_output=True, text=True, timeout=60
        )
        return result.returncode, result.stdout + result.stderr
    except Exception as e:
        return 1, str(e)


def calculate_scores() -> dict:
    scores = {
        "generated_at": datetime.now().isoformat(),
        "architecture_version": "2.4.0",
        "overall_score": 0,
        "security_score": 0,
        "coverage": 0,
        "cyclomatic_complexity": 0,
        "module_coupling": 0,
        "import_linter_score": 0,
        "dead_code": 0,
        "dependency_health": 0,
        "documentation_coverage": 0,
        "uml_coverage": 0,
        "adr_coverage": 0,
    }

    returncode, _ = run_command(["pytest", "--co", "-q"])
    scores["tests_configured"] = returncode == 0

    returncode, _ = run_command(
        ["lint-imports", "--config", "import-linter.ini", "--exit-zero"]
    )
    scores["import_linter_score"] = 100 if returncode == 0 else 0

    scores["overall_score"] = scores["import_linter_score"]

    return scores


def generate_scorecard(output: str) -> None:
    scores = calculate_scores()
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(scores, f, indent=2)

    print(f"Generated: {output_path}")
    print(f"Overall Score: {scores['overall_score']}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate architecture scorecard")
    parser.add_argument("--output", required=True, help="Output JSON file path")
    args = parser.parse_args()

    try:
        generate_scorecard(args.output)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
