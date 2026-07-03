"""Locust Load Test File for RentSecureBE API.

Tests the API under simulated concurrent load to detect:
- Response time degradation under load
- Error rate spikes
- Database connection exhaustion
- Memory/CPU pressure

Run with:
    locust -f tests/load/locustfile.py --headless --users=20 \
      --spawn-rate=2 --run-time=2m --host=http://localhost:8000

For CI:
    locust -f tests/load/locustfile.py --headless --users=20 \
      --spawn-rate=2 --run-time=2m --host=http://localhost:8000 \
      --exit-code-on-error 1
"""

from __future__ import annotations

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rentsecure_be.settings")

import django  # noqa: E402
from django.contrib.auth import get_user_model  # noqa: E402

django.setup()

from locust import HttpUser, TaskSet, between, task  # noqa: E402
from rest_framework_simplejwt.tokens import RefreshToken  # noqa: E402

User = get_user_model()


def get_auth_header(user: User) -> dict[str, str]:
    refresh = RefreshToken.for_user(user)
    token = str(refresh.access_token)
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


class AuthenticatedUserBehavior(TaskSet):
    """Simulates a logged-in property owner performing typical CRUD operations."""

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

    @task(3)
    def list_buildings(self) -> None:
        self.client.get("/api/properties/buildings/", headers=self._headers)

    @task(3)
    def list_units(self) -> None:
        self.client.get("/api/properties/units/", headers=self._headers)

    @task(2)
    def list_renters(self) -> None:
        self.client.get("/api/properties/renters/", headers=self._headers)

    @task(2)
    def list_rent_records(self) -> None:
        self.client.get("/api/properties/rent-records/", headers=self._headers)

    @task(1)
    def building_analytics(self) -> None:
        if self._building_id is None:
            return
        self.client.get(
            f"/api/properties/buildings/{self._building_id}/analytics/",
            headers=self._headers,
        )


class AnonymousUserBehavior(TaskSet):
    """Simulates unauthenticated endpoints (public API discovery)."""

    @task(1)
    def discover_api_root(self) -> None:
        self.client.get("/api/", name="api_root_anonymous")


class RentSecureAPIUser(HttpUser):
    """MainLocust user class — simulates authenticated property owner traffic."""

    tasks = [AuthenticatedUserBehavior]
    wait_time = between(0.5, 3.0)  # Median 1.5s between requests
    weight = 9  # 90% authenticated traffic

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self.host = os.environ.get("LOCUST_HOST", "http://127.0.0.1:8000")


class AnonymousAPIUser(HttpUser):
    """Simulates occasional unauthenticated traffic."""

    tasks = [AnonymousUserBehavior]
    wait_time = between(1.0, 5.0)
    weight = 1  # 10% anonymous traffic

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self.host = os.environ.get("LOCUST_HOST", "http://127.0.0.1:8000")
