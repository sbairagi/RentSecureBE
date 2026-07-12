#!/usr/bin/env python3
"""Generate Mermaid diagrams for RentSecureBE from architecture metadata."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def load_metadata(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def generate_class_diagram(metadata: dict) -> str:
    lines = ["classDiagram"]
    for _app_name, app_data in metadata.get("apps", {}).items():
        for model in app_data.get("models", []):
            lines.append(f"    class {model['name']} {{")
            for field in model.get("fields", [])[:12]:
                field_type = field.get("type", "unknown")
                lines.append(f"      +{field['name']}: {field_type}")
            lines.append("    }")

    lines.append("")
    for _app_name, app_data in metadata.get("apps", {}).items():
        for model in app_data.get("models", []):
            for rel in model.get("relationships", []):
                if rel.get("to"):
                    lines.append(f"    {model['name']} --> {rel['to']} : {rel['from']}")
    return "\n".join(lines)


def generate_ci_flow(metadata: dict) -> str:
    ci_stages = [
        "Lint",
        "Tests",
        "Architecture",
        "UML",
        "UML Validation",
        "Security",
        "Quality",
        "Deploy Readiness",
        "Deploy",
    ]
    lines = ["flowchart LR"]
    for i, stage in enumerate(ci_stages):
        lines.append(f'    S{i}["{stage}"]')
        if i > 0:
            lines.append(f"    S{i-1} --> S{i}")
    return "\n".join(lines)


def generate_dependency_graph(metadata: dict) -> str:
    lines = ["graph TD"]
    apps = list(metadata.get("apps", {}).keys())
    for app in apps:
        lines.append(f'    {app}["{app}"]')
    deps = metadata.get("dependencies", {})
    for app_name, app_deps in deps.items():
        for dep in app_deps:
            lines.append(f"    {app_name} --> {dep}")
    return "\n".join(lines)


def generate_all(metadata: dict, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    class_diagram = generate_class_diagram(metadata)
    (output_dir / "class-diagram.mmd").write_text(class_diagram)
    print(f"Generated: {output_dir / 'class-diagram.mmd'}")

    ci_flow = generate_ci_flow(metadata)
    (output_dir / "ci-flow.mmd").write_text(ci_flow)
    print(f"Generated: {output_dir / 'ci-flow.mmd'}")

    dep_graph = generate_dependency_graph(metadata)
    (output_dir / "dependency-graph.mmd").write_text(dep_graph)
    print(f"Generated: {output_dir / 'dependency-graph.mmd'}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate Mermaid diagrams from architecture metadata"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="docs/uml/generated/mermaid",
        help="Output directory",
    )
    parser.add_argument("--all", action="store_true", help="Generate all diagrams")
    parser.add_argument(
        "--metadata",
        type=str,
        default="architecture/generated/architecture.json",
        help="Path to architecture.json",
    )
    args = parser.parse_args()

    try:
        metadata = load_metadata(args.metadata)
        if args.all:
            generate_all(metadata, Path(args.output))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
