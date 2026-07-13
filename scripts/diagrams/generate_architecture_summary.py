#!/usr/bin/env python3
"""Generate architecture summary from metadata."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


def load_metadata(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)  # type: ignore[no-any-return]


def generate_summary(metadata: dict, output_path: str) -> None:
    lines = [
        "# Architecture Summary",
        "",
        f"**Generated:** {datetime.now().isoformat()}",
        "",
        "## Overview",
        "",
        f"- **Total Apps:** {len(metadata.get('apps', {}))}",
        f"- **Total URLs:** {len(metadata.get('urls', []))}",
        f"- **Feature Flags:** {len(metadata.get('feature_flags', []))}",
        "",
        "## App Breakdown",
        "",
        "| App | Models | Views | Serializers | Services | Files |",
        "|-----|--------|-------|-------------|----------|-------|",
    ]

    for app_name, app_data in metadata.get("apps", {}).items():
        lines.append(
            f"| {app_name} | {app_data.get('model_count', 0)} | "
            f"{app_data.get('view_count', 0)} | "
            f"{app_data.get('serializer_count', 0)} | "
            f"{app_data.get('service_count', 0)} | {len(app_data.get('files', []))} |"
        )

    lines.extend(
        [
            "",
            "## Dependencies",
            "",
            "| App | Depends On |",
            "|-----|-----------|",
        ]
    )
    for app_name, app_deps in metadata.get("dependencies", {}).items():
        if app_deps:
            lines.append(f"| {app_name} | {', '.join(app_deps)} |")

    lines.extend(
        [
            "",
            "## Infrastructure",
            "",
            "| Component | Technology |",
            "|-----------|-----------|",
        ]
    )
    for key, value in metadata.get("infrastructure", {}).items():
        lines.append(f"| {key} | {value} |")

    lines.extend(
        [
            "",
            "## Recommendations",
            "",
            "- Monitor models per app for domain cohesion",
            "- Review views for thin controller pattern compliance",
            "- Track LOC growth over time",
            "",
        ]
    )

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines))
    print(f"Generated: {output}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate architecture summary from architecture metadata"
    )
    parser.add_argument("--metadata", required=True, help="Path to architecture.json")
    parser.add_argument("--output", required=True, help="Output markdown file")
    args = parser.parse_args()

    try:
        metadata = load_metadata(args.metadata)
        generate_summary(metadata, args.output)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
