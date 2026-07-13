#!/usr/bin/env python3
"""Generate domain/ER diagrams for RentSecureBE from architecture metadata."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def load_metadata(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)  # type: ignore[no-any-return]


def generate_er_diagram(metadata: dict) -> str:  # noqa: C901
    lines = ["@startuml er-diagram", "!theme plain", ""]
    for _app_name, app_data in metadata.get("apps", {}).items():
        for model in app_data.get("models", []):
            entity_alias = model["name"].lower()
            lines.append(f'entity "{model["name"]}" as {entity_alias} {{')
            for field in model.get("fields", [])[:8]:
                lines.append(f"  {field['name']} : {field['type']}")
            lines.append("}")
            lines.append("")

    lines.append("' Relationships")
    seen = set()
    for _app_name, app_data in metadata.get("apps", {}).items():
        for model in app_data.get("models", []):
            for rel in model.get("relationships", []):
                to_model = rel.get("to")
                if not to_model:
                    continue
                key = (model["name"], to_model, rel["from"])
                if key in seen:
                    continue
                seen.add(key)
                if rel["type"] == "ForeignKey":
                    lines.append(
                        f'{model["name"].lower()} ||--o{{ '
                        f'{to_model.lower()} : "{rel["from"]}"'
                    )
                elif rel["type"] == "OneToOne":
                    lines.append(
                        f'{model["name"].lower()} ||--|| '
                        f'{to_model.lower()} : "{rel["from"]}"'
                    )
                elif rel["type"] == "ManyToMany":
                    lines.append(
                        f'{model["name"].lower()} }}|--|| '
                        f'{to_model.lower()} : "{rel["from"]}"'
                    )

    lines.append("")
    lines.append("@enduml")
    return "\n".join(lines)


def generate_all(metadata: dict, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    er_diagram = generate_er_diagram(metadata)
    (output_dir / "er-diagram.puml").write_text(er_diagram)
    print(f"Generated: {output_dir / 'er-diagram.puml'}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate domain diagrams from architecture metadata"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="docs/uml/generated/domain",
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
