#!/usr/bin/env python3
"""Validate diagram links in documentation."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def find_links(content: str) -> list[str]:
    """Find all markdown links in content."""
    pattern = r"\[.*?\]\((.*?)\)"
    return re.findall(pattern, content)


def validate_links(docs_dir: str, fail_on_broken: bool = False) -> int:
    """Validate all links in documentation."""
    docs_path = Path(docs_dir)
    broken_links = []

    for md_file in docs_path.rglob("*.md"):
        content = md_file.read_text()
        links = find_links(content)

        for link in links:
            if link.startswith("http"):
                continue
            if link.startswith("#"):
                continue

            link_path = md_file.parent / link
            if not link_path.exists():
                broken_links.append(f"{md_file}: {link}")

    if broken_links:
        for link in broken_links:
            print(f"BROKEN: {link}")
        if fail_on_broken:
            return 1
    else:
        print("All diagram links validated successfully")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate diagram links")
    parser.add_argument("--docs-dir", required=True, help="Documentation directory")
    parser.add_argument(
        "--fail-on-broken", action="store_true", help="Fail on broken links"
    )
    args = parser.parse_args()

    return validate_links(args.docs_dir, args.fail_on_broken)


if __name__ == "__main__":
    sys.exit(main())
