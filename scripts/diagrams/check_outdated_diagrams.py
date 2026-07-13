#!/usr/bin/env python3
"""Check for outdated diagrams."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def get_file_hash(path: Path) -> str:
    """Get MD5 hash of file contents."""
    if not path.exists():
        return ""
    content = path.read_bytes()
    return hashlib.sha256(content).hexdigest()


def load_hashes(hash_file: Path) -> dict:
    """Load previous hashes."""
    if not hash_file.exists():
        return {}
    try:
        with open(hash_file) as f:
            return json.load(f)  # type: ignore[no-any-return]
    except Exception:
        return {}


def save_hashes(hash_file: Path, hashes: dict) -> None:
    """Save hashes to file."""
    hash_file.parent.mkdir(parents=True, exist_ok=True)
    with open(hash_file, "w") as f:
        json.dump(hashes, f, indent=2)


def check_outdated(  # noqa: C901
    source_dir: str, diagram_dir: str, fail_on_outdated: bool = False
) -> int:
    """Check for outdated diagrams."""
    source_path = Path(source_dir)
    diagram_path = Path(diagram_dir)
    hash_file = diagram_path / ".diagram_hashes.json"

    previous_hashes = load_hashes(hash_file)
    current_hashes = {}

    # Check all Python files
    for py_file in source_path.rglob("*.py"):
        rel = str(py_file)
        if (
            "__pycache__" in rel
            or "migrations" in rel
            or ".venv" in rel
            or "node_modules" in rel
        ):
            continue
        rel_path = str(py_file.relative_to(source_path))
        current_hashes[f"source:{rel_path}"] = get_file_hash(py_file)

    # Check all diagram files
    for diagram_file in diagram_path.rglob("*"):
        if diagram_file.is_file() and not diagram_file.name.startswith("."):
            rel_path = str(diagram_file.relative_to(diagram_path))
            current_hashes[f"diagram:{rel_path}"] = get_file_hash(diagram_file)

    # Compare hashes
    changed_existing = []
    new_files = []
    for key, hash_val in current_hashes.items():
        if key in previous_hashes and previous_hashes[key] != hash_val:
            changed_existing.append(key)
        elif key not in previous_hashes:
            new_files.append(key)

    if changed_existing or new_files:
        for item in changed_existing:
            print(f"OUTDATED: {item}")
        for item in new_files:
            print(f"NEW: {item}")
        if fail_on_outdated and changed_existing:
            return 1
    else:
        print("No outdated diagrams detected")

    # Save current hashes
    save_hashes(hash_file, current_hashes)

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Check outdated diagrams")
    parser.add_argument("--source-dir", required=True, help="Source code directory")
    parser.add_argument("--diagram-dir", required=True, help="Diagram directory")
    parser.add_argument(
        "--fail-on-outdated", action="store_true", help="Fail on outdated diagrams"
    )
    args = parser.parse_args()

    return check_outdated(args.source_dir, args.diagram_dir, args.fail_on_outdated)


if __name__ == "__main__":
    sys.exit(main())
