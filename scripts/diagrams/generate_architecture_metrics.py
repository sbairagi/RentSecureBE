#!/usr/bin/env python3
"""Generate architecture metrics for RentSecureBE from architecture metadata."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def load_metadata(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)  # type: ignore[no-any-return]


def generate_metrics(metadata: dict, output: str) -> None:
    metrics: dict[str, Any] = {
        "generated_at": "auto",
        "apps": {},
        "totals": {
            "models": 0,
            "views": 0,
            "serializers": 0,
            "services": 0,
            "tests": 0,
            "loc": 0,
            "files": 0,
        },
    }

    for app_name, app_data in metadata.get("apps", {}).items():
        app_metrics = {
            "models": app_data.get("model_count", 0),
            "views": app_data.get("view_count", 0),
            "serializers": app_data.get("serializer_count", 0),
            "services": app_data.get("service_count", 0),
            "tests": 0,
            "loc": sum(f.get("sha256", 0) != "" for f in app_data.get("files", [])),
            "files": len(app_data.get("files", [])),
        }
        metrics["apps"][app_name] = app_metrics
        for key in metrics["totals"]:
            metrics["totals"][key] += app_metrics.get(key, 0)

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"Generated: {output_path}")
    print(f"Total apps: {len(metrics['apps'])}")
    print(f"Total models: {metrics['totals']['models']}")
    print(f"Total views: {metrics['totals']['views']}")
    print(f"Total services: {metrics['totals']['services']}")
    print(f"Total files: {metrics['totals']['files']}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate architecture metrics from architecture metadata"
    )
    parser.add_argument("--output", required=True, help="Output JSON file path")
    parser.add_argument(
        "--metadata",
        type=str,
        default="architecture/generated/architecture.json",
        help="Path to architecture.json",
    )
    args = parser.parse_args()

    try:
        metadata = load_metadata(args.metadata)
        generate_metrics(metadata, args.output)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
