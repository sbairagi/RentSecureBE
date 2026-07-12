#!/usr/bin/env python3
"""Check for missing diagrams."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def check_missing_diagrams(
    docs_dir: str, required_file: str, fail_on_missing: bool = False
) -> int:
    """Check for missing required diagrams."""
    docs_path = Path(docs_dir)
    required_path = Path(required_file)

    if not required_path.exists():
        print(f"Required diagrams file not found: {required_file}")
        return 1

    required = required_path.read_text().strip().splitlines()
    missing = []

    for diagram in required:
        diagram = diagram.strip()
        if not diagram or diagram.startswith("#"):
            continue
        diagram_path = docs_path / diagram
        if not diagram_path.exists():
            missing.append(diagram)

    if missing:
        for diagram in missing:
            print(f"MISSING: {diagram}")
        if fail_on_missing:
            return 1
    else:
        print("All required diagrams present")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Check missing diagrams")
    parser.add_argument("--docs-dir", required=True, help="Documentation directory")
    parser.add_argument(
        "--required-diagrams", required=True, help="File listing required diagrams"
    )
    parser.add_argument(
        "--fail-on-missing", action="store_true", help="Fail on missing diagrams"
    )
    args = parser.parse_args()

    return check_missing_diagrams(
        args.docs_dir, args.required_diagrams, args.fail_on_missing
    )


if __name__ == "__main__":
    sys.exit(main())
