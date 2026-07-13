#!/usr/bin/env python3
"""Validate generated diagrams."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def validate_plantuml(path: Path) -> list[str]:
    """Validate PlantUML syntax."""
    errors = []
    if not path.exists():
        return [f"File not found: {path}"]

    content = path.read_text()

    if "@startuml" not in content:
        errors.append(f"Missing @startuml tag: {path}")
    if "@enduml" not in content:
        errors.append(f"Missing @enduml tag: {path}")

    try:
        import plantuml  # type: ignore[import-not-found]

        plantuml_inst = plantuml.PlantUML()
        result = plantuml_inst.processes_file(str(path))
        if result != 0:
            errors.append(f"PlantUML validation failed: {path}")
    except Exception as e:
        errors.append(f"PlantUML validation error: {path}: {e}")

    return errors


def validate_mermaid(path: Path) -> list[str]:
    """Validate Mermaid syntax."""
    errors = []
    if not path.exists():
        return [f"File not found: {path}"]

    content = path.read_text()

    valid_types = [
        "graph",
        "flowchart",
        "sequenceDiagram",
        "classDiagram",
        "stateDiagram",
        "erDiagram",
        "gantt",
        "pie",
        "mindmap",
    ]

    has_valid_type = any(content.startswith(t) for t in valid_types)
    if not has_valid_type:
        errors.append(f"Invalid Mermaid diagram type: {path}")

    return errors


def validate_c4(path: Path) -> list[str]:
    """Validate C4 diagram syntax."""
    errors = []
    if not path.exists():
        return [f"File not found: {path}"]

    content = path.read_text()

    if "@startuml" not in content:
        errors.append(f"Missing @startuml tag: {path}")
    if "@enduml" not in content:
        errors.append(f"Missing @enduml tag: {path}")

    c4_keywords = ["Person", "System", "Container", "Component", "Rel"]
    has_c4 = any(kw in content for kw in c4_keywords)
    if not has_c4:
        errors.append(f"Missing C4 elements in: {path}")

    return errors


def validate_diagrams(  # noqa: C901
    diagram_type: str, path: str, fail_on_error: bool = False
) -> int:  # noqa: C901
    """Validate diagrams of a specific type."""
    diagram_path = Path(path)
    errors = []

    if diagram_path.is_dir():
        for diagram_file in diagram_path.rglob("*"):
            if diagram_file.is_file():
                if diagram_type == "plantuml":
                    errors.extend(validate_plantuml(diagram_file))
                elif diagram_type == "mermaid":
                    errors.extend(validate_mermaid(diagram_file))
                elif diagram_type == "c4":
                    errors.extend(validate_c4(diagram_file))
    elif diagram_path.is_file():
        if diagram_type == "plantuml":
            errors.extend(validate_plantuml(diagram_path))
        elif diagram_type == "mermaid":
            errors.extend(validate_mermaid(diagram_path))
        elif diagram_type == "c4":
            errors.extend(validate_c4(diagram_path))

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        if fail_on_error:
            return 1
    else:
        print(f"All {diagram_type} diagrams validated successfully")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate diagrams")
    parser.add_argument(
        "--type",
        required=True,
        choices=["plantuml", "mermaid", "c4"],
        help="Diagram type",
    )
    parser.add_argument(
        "--path", required=True, help="Path to diagram file or directory"
    )
    parser.add_argument(
        "--fail-on-error", action="store_true", help="Fail on validation errors"
    )
    args = parser.parse_args()

    return validate_diagrams(args.type, args.path, args.fail_on_error)


if __name__ == "__main__":
    sys.exit(main())
