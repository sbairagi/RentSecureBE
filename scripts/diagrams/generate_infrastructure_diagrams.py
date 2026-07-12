#!/usr/bin/env python3
"""Generate infrastructure diagrams for RentSecureBE from architecture metadata."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def load_metadata(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def generate_aws_deployment(metadata: dict) -> str:
    metadata.get("infrastructure", {})
    lines = ["@startuml aws-deployment", "!theme plain", ""]
    lines.append('node "Client" as client {')
    lines.append("  [React Native App]")
    lines.append("  [Web Browser]")
    lines.append("}")
    lines.append("")
    lines.append('node "AWS Cloud" as aws {')
    lines.append('  node "VPC" as vpc {')
    lines.append('    node "Public Subnet" as pub {')
    lines.append("      [Nginx]")
    lines.append("      [Load Balancer]")
    lines.append("    }")
    lines.append('    node "Private Subnet" as priv {')
    lines.append("      [Gunicorn + Django]")
    lines.append("      [Celery Worker]")
    lines.append("      [Celery Beat]")
    lines.append("    }")
    lines.append('    node "Data Layer" as data {')
    lines.append('      database "PostgreSQL" as pg')
    lines.append('      database "Redis" as redis')
    lines.append("    }")
    lines.append("  }")
    lines.append('  storage "S3 Bucket" as s3')
    lines.append("}")
    lines.append("")
    lines.append("client --> [Load Balancer] : HTTPS")
    lines.append("[Load Balancer] --> [Nginx] : HTTP")
    lines.append("[Nginx] --> [Gunicorn + Django] : HTTP")
    lines.append("[Gunicorn + Django] --> pg : SQL")
    lines.append("[Gunicorn + Django] --> redis : Redis protocol")
    lines.append("[Celery Worker] --> redis : AMQP")
    lines.append("[Celery Beat] --> redis : AMQP")
    lines.append("[Celery Worker] --> pg : SQL")
    lines.append("[Celery Worker] --> s3 : S3 API")
    lines.append("[Gunicorn + Django] --> s3 : S3 API")
    lines.append("")
    lines.append("@enduml")
    return "\n".join(lines)


def generate_cicd_pipeline(metadata: dict) -> str:
    urls = metadata.get("urls", [])
    any("uml" in u.get("path", "").lower() for u in urls) or True
    stages = [
        "Lint",
        "Tests",
        "Architecture",
        "UML Generation",
        "UML Validation",
        "Security",
        "Quality Gate",
        "Deploy Readiness",
        "Deploy",
    ]
    lines = ["@startuml cicd-pipeline", "!theme plain", ""]
    lines.append("start")
    for i, stage in enumerate(stages):
        lines.append(f":{stage};")
        if i < len(stages) - 1:
            lines.append("if (Pass?) then (yes)")
    lines.append(":Deploy to EC2;")
    lines.append("stop")
    for _ in stages[:-1]:
        lines.append("else (no)")
        lines.append("  stop")
        lines.append("endif")
    lines.append("@enduml")
    return "\n".join(lines)


def generate_runtime(metadata: dict) -> str:
    lines = ["@startuml runtime", "!theme plain", ""]
    lines.append("[Django] --> [Gunicorn] : WSGI")
    lines.append("[Gunicorn] --> [Nginx] : HTTP")
    lines.append("[Nginx] --> [Client] : HTTPS")
    lines.append("[Django] --> [PostgreSQL] : SQL")
    lines.append("[Django] --> [Redis] : Cache/Queue")
    lines.append("[Celery Worker] --> [Redis] : AMQP")
    lines.append("[Celery Beat] --> [Redis] : AMQP")
    lines.append("[Celery Worker] --> [PostgreSQL] : SQL")
    lines.append("")
    lines.append("@enduml")
    return "\n".join(lines)


def generate_all(metadata: dict, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    aws = generate_aws_deployment(metadata)
    (output_dir / "aws-deployment.puml").write_text(aws)
    print(f"Generated: {output_dir / 'aws-deployment.puml'}")

    cicd = generate_cicd_pipeline(metadata)
    (output_dir / "cicd-pipeline.puml").write_text(cicd)
    print(f"Generated: {output_dir / 'cicd-pipeline.puml'}")

    runtime = generate_runtime(metadata)
    (output_dir / "runtime.puml").write_text(runtime)
    print(f"Generated: {output_dir / 'runtime.puml'}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate infrastructure diagrams from architecture metadata"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="docs/diagrams/generated/infrastructure",
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
