#!/usr/bin/env python3
"""Generate flow diagrams for RentSecureBE from architecture metadata."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def load_metadata(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)  # type: ignore[no-any-return]


def _find_urls(metadata: dict, path_fragment: str) -> list[dict]:
    results = []
    for url in metadata.get("urls", []):
        if path_fragment in url.get("path", ""):
            results.append(url)
    return results


def generate_authentication_flow(metadata: dict) -> str:
    auth_urls = _find_urls(metadata, "auth") + _find_urls(metadata, "token")
    lines = [
        "@startuml auth-flow",
        "!theme plain",
        "skinparam backgroundColor #FEFEFF",
        "",
    ]
    lines.append("actor User")
    lines.append('participant "API" as api')
    lines.append('participant "Database" as db')
    lines.append('database "Database" as db')
    lines.append("")

    for url in auth_urls[:5]:
        path = url.get("path", "")
        view = url.get("view", "")
        if path and view:
            lines.append(f"User -> api : {path}")

    lines.append("")
    lines.append("@enduml")
    return "\n".join(lines)


def generate_payment_flow(metadata: dict) -> str:
    payment_urls = (
        _find_urls(metadata, "payment")
        + _find_urls(metadata, "rent")
        + _find_urls(metadata, "webhook")
    )
    lines = ["@startuml payment-flow", "!theme plain", ""]
    lines.append("actor Owner")
    lines.append("actor Renter")
    lines.append('participant "API" as api')
    lines.append('participant "Database" as db')
    lines.append('participant "Notifications" as notify')
    lines.append('participant "PDF Engine" as pdf')
    lines.append("")

    for url in payment_urls[:6]:
        path = url.get("path", "")
        if path:
            lines.append(f"api -> api : {path}")

    lines.append("")
    lines.append("@enduml")
    return "\n".join(lines)


def generate_notification_flow(metadata: dict) -> str:
    notif_urls = _find_urls(metadata, "notification") + _find_urls(
        metadata, "register-fcm"
    )
    lines = ["@startuml notification-flow", "!theme plain", ""]
    lines.append('participant "API" as api')
    lines.append('participant "Notification Service" as svc')
    lines.append('participant "Email" as email')
    lines.append('participant "Push" as push')
    lines.append('participant "WhatsApp" as wa')
    lines.append('participant "Voice" as voice')
    lines.append("")

    for url in notif_urls[:6]:
        path = url.get("path", "")
        if path:
            lines.append(f"svc -> svc : {path}")

    lines.append("")
    lines.append("@enduml")
    return "\n".join(lines)


def generate_all(metadata: dict, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    auth_flow = generate_authentication_flow(metadata)
    (output_dir / "authentication-flow.puml").write_text(auth_flow)
    print(f"Generated: {output_dir / 'authentication-flow.puml'}")

    payment_flow = generate_payment_flow(metadata)
    (output_dir / "payment-flow.puml").write_text(payment_flow)
    print(f"Generated: {output_dir / 'payment-flow.puml'}")

    notif_flow = generate_notification_flow(metadata)
    (output_dir / "notification-flow.puml").write_text(notif_flow)
    print(f"Generated: {output_dir / 'notification-flow.puml'}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate flow diagrams from architecture metadata"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="docs/diagrams/generated/flows",
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
