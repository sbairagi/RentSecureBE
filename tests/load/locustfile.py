"""Locust Load Test File for RentSecureBE API.

Tests the API under simulated concurrent load to detect:
- Response time degradation under load
- Error rate spikes
- Database connection exhaustion
- Memory/CPU pressure

Run with:
    BASE_URL=http://localhost:8000 locust -f tests/load/locustfile.py --headless \
      --users=20 --spawn-rate=2 --run-time=2m

The target host is resolved in this order:
  1. --host CLI flag
  2. BASE_URL environment variable
  3. Class-level default (http://127.0.0.1:8000)

For CI:
    locust -f tests/load/locustfile.py --headless \
      --host=http://127.0.0.1:8000 \
      --users=20 --spawn-rate=2 --run-time=2m \
      --exit-code-on-error 1
"""

from __future__ import annotations

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rentsecure_be.settings")

import django  # noqa: E402
from django.contrib.auth import get_user_model  # noqa: E402

django.setup()

from locust import HttpUser, between, task  # noqa: E402
from rest_framework_simplejwt.tokens import RefreshToken  # noqa: E402

User = get_user_model()


def get_auth_header(user: User) -> dict[str, str]:
    refresh = RefreshToken.for_user(user)
    token = str(refresh.access_token)
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def _get_base_url() -> str:
    base_url = os.environ.get("BASE_URL", "").strip()
    if base_url:
        return base_url.rstrip("/")
    return "http://127.0.0.1:8000"


class RentSecureAPIUser(HttpUser):
    """Main Locust user class — simulates authenticated property owner traffic."""

    wait_time = between(0.5, 3.0)
    weight = 9
    host: str = _get_base_url()

    _user: User | None = None
    _headers: dict[str, str] | None = None
    _building_id: int | None = None
    _unit_id: int | None = None
    _renter_id: int | None = None

    def on_start(self) -> None:
        self._user, _ = User.objects.get_or_create(
            username=f"loadtest_{id(self)}",
            defaults={
                "email": f"loadtest{id(self)}@loadtest.local",
                "full_name": "Load Test User",
                "phone": "+919876543210",
            },
        )
        self._user.set_password("loadtestpass")
        self._user.save()
        self._headers = get_auth_header(self._user)

    def _safe_get(self, path: str, name: str) -> None:
        with self.client.get(
            path,
            headers=self._headers,
            name=name,
            catch_response=True,
        ) as response:
            if response.status_code >= 400:
                response.failure(f"{name} failed with status {response.status_code}")

    @task(3)
    def list_buildings(self) -> None:
        self._safe_get("/api/properties/buildings/", "list_buildings")

    @task(3)
    def list_units(self) -> None:
        self._safe_get("/api/properties/units/", "list_units")

    @task(2)
    def list_renters(self) -> None:
        self._safe_get("/api/properties/renters/", "list_renters")

    @task(2)
    def list_rent_records(self) -> None:
        self._safe_get("/api/properties/rent-records/", "list_rent_records")

    @task(1)
    def building_analytics(self) -> None:
        if self._building_id is None:
            return
        self._safe_get(
            f"/api/properties/buildings/{self._building_id}/analytics/",
            "building_analytics",
        )


class AnonymousAPIUser(HttpUser):
    """Simulates occasional unauthenticated traffic."""

    wait_time = between(1.0, 5.0)
    weight = 1
    host: str = _get_base_url()

    @task(1)
    def discover_api_root(self) -> None:
        with self.client.get(
            "/api/",
            name="api_root_anonymous",
            catch_response=True,
        ) as response:
            if response.status_code >= 400:
                response.failure(
                    f"api_root_anonymous failed with status {response.status_code}"
                )
