"""Seed load test data for Locust/performance testing."""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rentsecure_be.settings")

import django

django.setup()

from django.contrib.auth import get_user_model  # noqa: E402

from core.models import SubscriptionPlan  # noqa: E402

User = get_user_model()

for i in range(5):
    User.objects.get_or_create(
        username=f"loadtest_user_{i}",
        defaults={
            "email": f"loadtest{i}@test.com",
            "password": "testpass123",
            "full_name": f"User {i}",
            "phone": f"+91987654321{i}",
        },
    )

plan, _ = SubscriptionPlan.objects.get_or_create(
    name="pro",
    defaults={"monthly_price": 2999, "yearly_price": 9999},
)

print(f"Seeded {User.objects.count()} users, plan={plan.name}")
