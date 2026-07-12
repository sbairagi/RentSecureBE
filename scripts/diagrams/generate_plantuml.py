#!/usr/bin/env python3
"""Generate PlantUML diagrams for RentSecureBE from architecture metadata."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def load_metadata(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def generate_class_diagram(metadata: dict) -> str:
    lines = [
        "@startuml class-diagram",
        "!theme plain",
        "skinparam classAttributeAlignment left",
        "",
    ]
    for app_name, app_data in metadata.get("apps", {}).items():
        lines.append(f"package {app_name} {{")
        for model in app_data.get("models", []):
            lines.append(f"  class {model['name']} {{")
            for field in model.get("fields", [])[:12]:
                field_type = field.get("type", "unknown")
                lines.append(f"    +{field['name']}: {field_type}")
            lines.append("  }")
        lines.append("}")
        lines.append("")

    lines.append("' Relationships")
    for _app_name, app_data in metadata.get("apps", {}).items():
        for model in app_data.get("models", []):
            for rel in model.get("relationships", []):
                if rel.get("to"):
                    lines.append(f'"{model["name"]}" --> "{rel["to"]}" : {rel["from"]}')

    lines.append("")
    lines.append("@enduml")
    return "\n".join(lines)


def generate_component_diagram(metadata: dict) -> str:
    lines = ["@startuml component-diagram", "!theme plain", ""]
    lines.append('package "rentsecure_be" {')
    for app_name in metadata.get("apps", {}):
        lines.append(f'  package "{app_name}" {{')
        app_data = metadata["apps"][app_name]
        if app_data.get("views"):
            lines.append("    [Views]")
        if app_data.get("serializers"):
            lines.append("    [Serializers]")
        if app_data.get("services"):
            lines.append("    [Services]")
        if app_data.get("models"):
            lines.append("    [Models]")
        lines.append("  }")
    lines.append("}")
    lines.append("")
    lines.append("[Views] --> [Serializers] : uses")
    lines.append("[Views] --> [Services] : calls")
    lines.append("[Services] --> [Models] : accesses")
    lines.append("[Serializers] --> [Models] : serializes")
    lines.append("")
    lines.append("@enduml")
    return "\n".join(lines)


def generate_package_diagram(metadata: dict) -> str:
    lines = ["@startuml package-diagram", "!theme plain", ""]
    lines.append("package rentsecure_be {")
    for app_name in metadata.get("apps", {}):
        lines.append(f"  package {app_name} {{")
        lines.append("  }")
    lines.append("}")

    deps = metadata.get("dependencies", {})
    for app_name, app_deps in deps.items():
        for dep in app_deps:
            lines.append(f"{app_name} --> {dep}")
    lines.append("")
    lines.append("@enduml")
    return "\n".join(lines)


def generate_all(metadata: dict, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    class_diagram = generate_class_diagram(metadata)
    (output_dir / "class-diagram.puml").write_text(class_diagram)
    print(f"Generated: {output_dir / 'class-diagram.puml'}")

    component_diagram = generate_component_diagram(metadata)
    (output_dir / "component-diagram.puml").write_text(component_diagram)
    print(f"Generated: {output_dir / 'component-diagram.puml'}")

    package_diagram = generate_package_diagram(metadata)
    (output_dir / "package-diagram.puml").write_text(package_diagram)
    print(f"Generated: {output_dir / 'package-diagram.puml'}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate PlantUML diagrams from architecture metadata"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="docs/uml/generated/plantuml",
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
