#!/usr/bin/env python3
"""Generate dependency graphs for RentSecureBE from architecture metadata."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def load_metadata(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def generate_dot(metadata: dict, graph_type: str) -> str:  # noqa: C901
    apps = list(metadata.get("apps", {}).keys())
    deps = metadata.get("dependencies", {})

    lines = [
        "digraph architecture {",
        "  rankdir=TB;",
        '  node [shape=box, style=filled, fillcolor="#E3F2FD"];',
        "",
    ]

    if graph_type == "package":
        for app in apps:
            lines.append(f'  "{app}" [fillcolor="#E3F2FD"];')
        lines.append("")
        for app_name, app_deps in deps.items():
            for dep in app_deps:
                lines.append(f'  "{app_name}" -> "{dep}" [style=dashed];')
    elif graph_type == "module":
        lines.append('  node [fillcolor="#FFF3E0"];')
        for app in apps:
            lines.append(f'  "{app}" [fillcolor="#FFF3E0"];')
        lines.append("")
        for app_name, app_deps in deps.items():
            for dep in app_deps:
                lines.append(f'  "{app_name}" -> "{dep}" [label="depends on"];')
    elif graph_type == "component":
        lines.append('  node [fillcolor="#E8F5E9"];')
        components = ["Views", "Serializers", "Services", "Models", "URLs", "Utils"]
        for comp in components:
            lines.append(f'  "{comp}" [fillcolor="#E8F5E9"];')
        lines.append("")
        for comp in components:
            if comp != "Views":
                lines.append(f'  "Views" -> "{comp}" [label="uses"];')

    lines.append("}")
    return "\n".join(lines)


def generate_mermaid(metadata: dict, graph_type: str) -> str:  # noqa: C901
    apps = list(metadata.get("apps", {}).keys())
    deps = metadata.get("dependencies", {})
    lines = ["graph TD"]

    if graph_type == "package":
        for app in apps:
            lines.append(f'    {app}["{app}"]')
        for app_name, app_deps in deps.items():
            for dep in app_deps:
                lines.append(f"    {app_name} --> {dep}")
    elif graph_type == "module":
        for app in apps:
            lines.append(f'    {app}["{app}"]')
        for app_name, app_deps in deps.items():
            for dep in app_deps:
                lines.append(f"    {app_name} --> {dep}")
    elif graph_type == "component":
        components = ["Views", "Serializers", "Services", "Models"]
        for comp in components:
            lines.append(f'    {comp}["{comp}"]')
        lines.append("    Views --> Serializers")
        lines.append("    Views --> Services")
        lines.append("    Services --> Models")
        lines.append("    Serializers --> Models")

    return "\n".join(lines)


def generate_plantuml(metadata: dict, graph_type: str) -> str:
    apps = list(metadata.get("apps", {}).keys())
    deps = metadata.get("dependencies", {})
    lines = ["@startuml", "!theme plain", ""]

    if graph_type == "package":
        lines.append("package rentsecure_be {")
        for app in apps:
            lines.append(f"    package {app} {{")
            lines.append("    }")
        lines.append("}")
        for app_name, app_deps in deps.items():
            for dep in app_deps:
                lines.append(f"{app_name} --> {dep}")
    elif graph_type == "module":
        for app in apps:
            lines.append(f"package {app} {{")
            lines.append("}")
        for app_name, app_deps in deps.items():
            for dep in app_deps:
                lines.append(f"{app_name} --> {dep}")
    elif graph_type == "component":
        lines.append('package "Presentation Layer" {')
        lines.append("    [Views]")
        lines.append("    [Serializers]")
        lines.append("}")
        lines.append('package "Business Layer" {')
        lines.append("    [Services]")
        lines.append("}")
        lines.append('package "Data Layer" {')
        lines.append("    [Models]")
        lines.append("}")
        lines.append("[Views] --> [Services]")
        lines.append("[Services] --> [Models]")
        lines.append("[Views] --> [Serializers]")
        lines.append("[Serializers] --> [Models]")

    lines.append("")
    lines.append("@enduml")
    return "\n".join(lines)


def generate_dependency_graph(
    metadata: dict, output: str, formats: list[str], graph_type: str = "package"
) -> None:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if "dot" in formats:
        dot_content = generate_dot(metadata, graph_type)
        dot_path = output_path.with_suffix(".dot")
        dot_path.write_text(dot_content)
        print(f"Generated: {dot_path}")

    if "mmd" in formats:
        mmd_content = generate_mermaid(metadata, graph_type)
        mmd_path = output_path.with_suffix(".mmd")
        mmd_path.write_text(mmd_content)
        print(f"Generated: {mmd_path}")

    if "puml" in formats:
        puml_content = generate_plantuml(metadata, graph_type)
        puml_path = output_path.with_suffix(".puml")
        puml_path.write_text(puml_content)
        print(f"Generated: {puml_path}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate dependency graphs from architecture metadata"
    )
    parser.add_argument(
        "--output", required=True, help="Output file path (without extension)"
    )
    parser.add_argument(
        "--format", nargs="+", default=["dot", "mmd", "puml"], help="Output formats"
    )
    parser.add_argument(
        "--type",
        choices=["package", "module", "component"],
        default="package",
        help="Graph type",
    )
    parser.add_argument(
        "--metadata",
        type=str,
        default="architecture/generated/architecture.json",
        help="Path to architecture.json",
    )
    args = parser.parse_args()

    try:
        metadata = load_metadata(args.metadata)
        generate_dependency_graph(metadata, args.output, args.format, args.type)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
