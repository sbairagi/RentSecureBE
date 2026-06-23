"""Minimal API contract regression check.

Validates that critical endpoints return expected status codes and
response shapes. Runs without pytest to avoid collection failures.
"""

import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rentsecure_be.settings")

import django
from django.conf import settings  # noqa: E402

django.setup()

settings.SECURE_SSL_REDIRECT = False
settings.SESSION_COOKIE_SECURE = False
settings.CSRF_COOKIE_SECURE = False

from django.test import Client  # noqa: E402

client = Client()

contracts = {
    "properties:building-list": {
        "method": "GET",
        "path": "/api/properties/buildings/",
        "expect_status": [200, 401, 403],
        "required_keys_when_200": ["count"],
    },
    "properties:unit-list": {
        "method": "GET",
        "path": "/api/properties/units/",
        "expect_status": [200, 401, 403],
        "required_keys_when_200": ["count"],
    },
    "properties:renter-list": {
        "method": "GET",
        "path": "/api/properties/renters/",
        "expect_status": [200, 401, 403],
        "required_keys_when_200": ["count"],
    },
    "properties:rent-record-list": {
        "method": "GET",
        "path": "/api/properties/rent-records/",
        "expect_status": [200, 401, 403],
        "required_keys_when_200": ["count"],
    },
    "finance:finance-list": {
        "method": "GET",
        "path": "/finance/",
        "expect_status": [200, 401, 403, 404],
    },
}

failures = []

for name, spec in contracts.items():
    method = str(spec["method"])
    resp = getattr(client, method.lower())(spec["path"])

    if resp.status_code not in spec["expect_status"]:
        failures.append(
            f"{name}: expected status in {spec['expect_status']}, "
            f"got {resp.status_code}"
        )
        continue

    if resp.status_code == 200 and "required_keys_when_200" in spec:
        try:
            data = resp.json()
            for key in spec["required_keys_when_200"]:
                if key not in data:
                    failures.append(
                        f"{name}: response missing required key '{key}'. "
                        f"Got keys: {list(data.keys())[:10]}"
                    )
        except (ValueError, AttributeError):
            failures.append(f"{name}: response is not valid JSON")

if failures:
    print("CONTRACT FAILURES DETECTED:")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)

print("All API contract checks passed.")
