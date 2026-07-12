#!/usr/bin/env python3
"""Generate C4 diagrams for RentSecureBE from architecture metadata."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def load_metadata(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def generate_context_diagram(metadata: dict) -> str:
    actors = []
    external_systems = [
        ("cashfree", "Cashfree", "Payment gateway and payouts"),
        ("twilio", "Twilio", "WhatsApp and SMS notifications"),
        ("aws_s3", "AWS S3", "File storage"),
        ("firebase", "Firebase", "Push notifications"),
    ]
    list(metadata.get("apps", {}).keys())
    actors.extend(["Property Owner", "Renter", "CA"])

    lines = ["@startuml c4-context"]
    lines.append(
        "!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Context.puml"
    )
    lines.append("")

    for actor in actors:
        safe = actor.replace(" ", "_")
        lines.append(f'Person({safe.lower()}, "{actor}", "")')

    lines.append('System(rentsecure, "RentSecureBE", "Property management platform")')
    for sys_id, sys_name, sys_desc in external_systems:
        lines.append(f'System_Ext({sys_id.lower()}, "{sys_name}", "{sys_desc}")')

    lines.append("")
    for actor in actors:
        safe = actor.replace(" ", "_")
        lines.append(f'Rel({safe.lower()}, rentsecure, "Uses", "HTTPS/JSON")')
    for sys_id, _, _ in external_systems:
        lines.append(f'Rel(rentsecure, {sys_id.lower()}, "Interacts", "HTTPS/JSON")')

    lines.append("")
    lines.append("@enduml")
    return "\n".join(lines)


def generate_container_diagram(metadata: dict) -> str:
    lines = ["@startuml c4-container"]
    lines.append(
        "!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Container.puml"
    )
    lines.append("")

    lines.append('Person(owner, "Property Owner", "Manages properties")')
    lines.append('Person(renter, "Renter", "Pays rent")')
    lines.append("")
    lines.append('Container_Boundary(backend, "RentSecureBE Backend", "Django 5.2") {')
    lines.append('  Container(api, "Django REST API", "DRF", "Handles HTTP requests")')
    lines.append(
        '  Container(celery_worker, "Celery Worker", "Celery", "Background tasks")'
    )
    lines.append('  Container(celery_beat, "Celery Beat", "Celery", "Scheduled tasks")')
    lines.append('  ContainerDb(postgres, "PostgreSQL", "PostgreSQL", "Stores data")')
    lines.append('  ContainerDb(redis, "Redis", "Redis", "Cache and queue")')
    lines.append("}")
    lines.append("")
    lines.append('Container_Ext(cashfree, "Cashfree", "Payment gateway")')
    lines.append('Container_Ext(twilio, "Twilio", "WhatsApp/SMS")')
    lines.append("")
    lines.append('Rel(owner, api, "Uses", "HTTPS/JSON")')
    lines.append('Rel(renter, api, "Uses", "HTTPS/JSON")')
    lines.append('Rel(api, postgres, "Reads/Writes", "SQL")')
    lines.append('Rel(api, redis, "Caches", "Redis protocol")')
    lines.append('Rel(api, celery_worker, "Enqueues tasks", "AMQP")')
    lines.append('Rel(celery_beat, celery_worker, "Schedules", "AMQP")')
    lines.append('Rel(celery_worker, postgres, "Reads/Writes", "SQL")')
    lines.append('Rel(celery_worker, cashfree, "Processes payouts", "HTTPS/JSON")')
    lines.append('Rel(api, twilio, "Sends notifications", "HTTPS/JSON")')
    lines.append("")
    lines.append("@enduml")
    return "\n".join(lines)


def generate_all(metadata: dict, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    context = generate_context_diagram(metadata)
    (output_dir / "c4-context.puml").write_text(context)
    print(f"Generated: {output_dir / 'c4-context.puml'}")

    container = generate_container_diagram(metadata)
    (output_dir / "c4-container.puml").write_text(container)
    print(f"Generated: {output_dir / 'c4-container.puml'}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate C4 diagrams from architecture metadata"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="docs/diagrams/generated/c4",
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
