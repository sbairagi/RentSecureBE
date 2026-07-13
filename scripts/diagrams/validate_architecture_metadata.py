#!/usr/bin/env python3
"""Validate architecture/generated/architecture.json structure."""

import json
import sys
from pathlib import Path


def main() -> int:
    path = Path("architecture/generated/architecture.json")
    if not path.exists():
        print("ERROR: architecture.json not found")
        sys.exit(1)

    data = json.loads(path.read_text())
    required_keys = [
        "generated_at",
        "root",
        "django_apps",
        "installed_apps",
        "feature_flags",
        "apps",
        "urls",
        "dependencies",
        "celery",
        "infrastructure",
    ]
    missing = [k for k in required_keys if k not in data]
    if missing:
        print(f"ERROR: Missing required keys: {missing}")
        sys.exit(1)

    if not isinstance(data["apps"], dict) or len(data["apps"]) == 0:
        print("ERROR: apps must be a non-empty dict")
        sys.exit(1)

    for app_name, app_data in data["apps"].items():
        if not isinstance(app_data, dict):
            print(f"ERROR: app {app_name} must be a dict")
            sys.exit(1)
        for key in ["models", "views", "serializers", "urls", "services", "files"]:
            if key not in app_data:
                print(f"ERROR: app {app_name} missing key: {key}")
                sys.exit(1)

    print("Architecture metadata validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
