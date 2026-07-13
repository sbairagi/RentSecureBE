#!/usr/bin/env python3
"""Generate DDD bounded context diagrams for RentSecureBE from architecture metadata."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def load_metadata(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)  # type: ignore[no-any-return]


def generate_ddd_diagram(metadata: dict) -> str:  # noqa: C901
    context_keywords = {
        "Property Management Context": [
            "Building",
            "Unit",
            "Renter",
            "CareTaker",
            "RentRecord",
            "ExtraCharge",
            "PropertyTaxRecord",
            "UnitVacancy",
            "UnitDocument",
            "UnitImage",
        ],
        "Financial Context": [
            "RentRecord",
            "ExtraCharge",
            "OwnerBankDetails",
            "SubscriptionPlan",
            "UserSubscription",
            "TaxSubmissionToCA",
            "CAProfile",
        ],
        "Notification Context": [
            "Notification",
            "DeviceToken",
            "NotificationPreference",
        ],
        "Authentication Context": ["User", "UserProfile", "OTP"],
        "Document Context": [
            "RentAgreementDraft",
            "AgreementRevocationLog",
            "PoliceVerification",
            "ArchivedRenter",
        ],
        "AI Assistant Context": ["SmartBotChat", "SmartBotMessage", "AIAlert"],
        "Referral Context": ["Referral"],
    }

    all_model_names = set()
    for app_data in metadata.get("apps", {}).values():
        for model in app_data.get("models", []):
            all_model_names.add(model["name"])

    context_map: dict[str, list[str]] = {ctx: [] for ctx in context_keywords}
    for ctx, keywords in context_keywords.items():
        for keyword in keywords:
            if keyword in all_model_names:
                context_map[ctx].append(keyword)

    lines = ["@startuml ddd-bounded-contexts", "!theme plain", ""]
    for ctx, models in context_map.items():
        if models:
            lines.append(f'package "{ctx}" {{')
            for model in models:
                lines.append(f"  [{model}]")
            lines.append("}")
            lines.append("")

    lines.append("' Context relationships")
    if context_map.get("Authentication Context") and context_map.get(
        "Property Management Context"
    ):
        lines.append(
            "[Authentication Context] --> [Property Management Context] : owns"
        )
    if context_map.get("Authentication Context") and context_map.get(
        "Financial Context"
    ):
        lines.append("[Authentication Context] --> [Financial Context] : owns")
    if context_map.get("Property Management Context") and context_map.get(
        "Financial Context"
    ):
        lines.append(
            "[Property Management Context] --> [Financial Context] : generates rent"
        )
    if context_map.get("Property Management Context") and context_map.get(
        "Notification Context"
    ):
        lines.append(
            "[Property Management Context] --> [Notification Context] "
            ": triggers notifications"
        )
    if context_map.get("Property Management Context") and context_map.get(
        "Document Context"
    ):
        lines.append(
            "[Property Management Context] --> [Document Context] : references"
        )
    if context_map.get("AI Assistant Context") and context_map.get(
        "Property Management Context"
    ):
        lines.append(
            "[AI Assistant Context] --> [Property Management Context] : queries"
        )
    if context_map.get("AI Assistant Context") and context_map.get("Financial Context"):
        lines.append("[AI Assistant Context] --> [Financial Context] : queries")
    if context_map.get("Referral Context") and context_map.get(
        "Authentication Context"
    ):
        lines.append("[Referral Context] --> [Authentication Context] : references")

    lines.append("")
    lines.append("@enduml")
    return "\n".join(lines)


def generate_repository_dependency(metadata: dict) -> str:
    lines = ["@startuml repository-dependency", "!theme plain", ""]
    for app_name, app_data in metadata.get("apps", {}).items():
        lines.append(f'package "{app_name}" {{')
        if app_data.get("views"):
            lines.append("  [views]")
        if app_data.get("serializers"):
            lines.append("  [serializers]")
        if app_data.get("services"):
            lines.append("  [services]")
        if app_data.get("models"):
            lines.append("  [models]")
        lines.append("}")

    lines.append("")
    deps = metadata.get("dependencies", {})
    for app_name, app_deps in deps.items():
        for dep in app_deps:
            lines.append(f"{app_name} --> {dep}")

    lines.append("")
    lines.append("@enduml")
    return "\n".join(lines)


def generate_drf_lifecycle(metadata: dict) -> str:
    lines = ["@startuml drf-lifecycle", "!theme plain", ""]
    lines.append("actor Client")
    lines.append('participant "URL Router" as router')
    lines.append('participant "API View" as view')
    lines.append('participant "Permissions" as perms')
    lines.append('participant "Authentication" as auth')
    lines.append('participant "Serializer" as ser')
    lines.append('participant "Service Layer" as svc')
    lines.append('participant "Model" as model')
    lines.append('database "Database" as db')
    lines.append("")
    lines.append("Client -> router : HTTP Request")
    lines.append("router -> view : Route to view")
    lines.append("view -> auth : Authenticate request")
    lines.append("auth --> view : User object")
    lines.append("view -> perms : Check permissions")
    lines.append("perms --> view : Permission granted")
    lines.append("view -> ser : Serialize/Deserialize")
    lines.append("ser -> model : Create/Update/Query")
    lines.append("model -> db : SQL Query")
    lines.append("db --> model : Data")
    lines.append("model --> ser : Model instance")
    lines.append("ser --> view : Serialized data")
    lines.append("view --> Client : JSON Response")
    lines.append("")
    lines.append("@enduml")
    return "\n".join(lines)


def generate_celery_task_flow(metadata: dict) -> str:
    lines = ["@startuml celery-task-flow", "!theme plain", ""]
    lines.append('participant "API" as api')
    lines.append('participant "Celery Beat" as beat')
    lines.append('queue "Redis Queue" as queue')
    lines.append('participant "Celery Worker" as worker')
    lines.append('database "PostgreSQL" as db')
    lines.append('storage "S3" as s3')
    lines.append('participant "External API" as ext')
    lines.append("")
    lines.append("api -> queue : Enqueue task (send_pdf)")
    lines.append("beat -> queue : Schedule task (daily_reminder)")
    lines.append("")
    lines.append("queue -> worker : Dequeue task")
    lines.append("worker -> db : Query data")
    lines.append("worker -> worker : Generate PDF")
    lines.append("worker -> s3 : Upload PDF")
    lines.append("worker -> ext : Call external API (if needed)")
    lines.append("worker -> db : Update task status")
    lines.append("")
    lines.append("@enduml")
    return "\n".join(lines)


def generate_rent_lifecycle(metadata: dict) -> str:
    rent_model = None
    for app_data in metadata.get("apps", {}).values():
        for model in app_data.get("models", []):
            if model["name"] == "RentRecord":
                rent_model = model
                break
    statuses = [
        "pending",
        "paid",
        "overdue",
        "payout_processing",
        "payout_success",
        "payout_failed",
    ]
    if rent_model:
        for field in rent_model.get("fields", []):
            if "status" in field.get("name", "").lower():
                statuses = [field.get("raw", "")] + statuses
                break

    lines = ["@startuml rent-lifecycle", "!theme plain", ""]
    lines.append("[*] --> Created : Owner creates rent record")
    lines.append("Created --> Pending : Status = pending")
    lines.append("Pending --> Paid : Payment received")
    lines.append("Pending --> Overdue : Due date passed")
    lines.append("Paid --> PayoutProcessing : Trigger payout")
    lines.append("PayoutProcessing --> PayoutSuccess : Success")
    lines.append("PayoutProcessing --> PayoutFailed : Failed")
    lines.append("PayoutFailed --> PayoutProcessing : Retry")
    lines.append("Overdue --> Paid : Late payment received")
    lines.append("Paid --> [*]")
    lines.append("PayoutSuccess --> [*]")
    lines.append("PayoutFailed --> [*]")
    lines.append("")
    lines.append("@enduml")
    return "\n".join(lines)


def generate_all(metadata: dict, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    ddd = generate_ddd_diagram(metadata)
    (output_dir / "ddd-bounded-contexts.puml").write_text(ddd)
    print(f"Generated: {output_dir / 'ddd-bounded-contexts.puml'}")

    repo_dep = generate_repository_dependency(metadata)
    (output_dir / "repository-dependency.puml").write_text(repo_dep)
    print(f"Generated: {output_dir / 'repository-dependency.puml'}")

    drf = generate_drf_lifecycle(metadata)
    (output_dir / "drf-lifecycle.puml").write_text(drf)
    print(f"Generated: {output_dir / 'drf-lifecycle.puml'}")

    celery = generate_celery_task_flow(metadata)
    (output_dir / "celery-task-flow.puml").write_text(celery)
    print(f"Generated: {output_dir / 'celery-task-flow.puml'}")

    rent = generate_rent_lifecycle(metadata)
    (output_dir / "rent-lifecycle.puml").write_text(rent)
    print(f"Generated: {output_dir / 'rent-lifecycle.puml'}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate DDD diagrams from architecture metadata"
    )
    parser.add_argument(
        "--output", type=str, default="docs/uml/generated/ddd", help="Output directory"
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
