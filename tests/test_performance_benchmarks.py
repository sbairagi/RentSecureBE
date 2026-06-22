"""Performance Regression Benchmarks.

Uses pytest-benchmark to track performance of critical business operations.
Detects performance regressions in:

- Rent record creation (hot path)
- Building analytics calculation
- Subscription plan lookup
- User authentication flow
- Query performance for common queries

Run with:
    pytest tests/test_performance_benchmarks.py \
      --benchmark-only \
      --benchmark-json=benchmark-results.json \
      --benchmark-sort=mean \
      --benchmark-columns=min,max,mean,stddev,median,rounds

CI note: These run on a schedule (Mon/Wed/Fri) not on every PR.
"""

import pytest
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from core.models import (
    SubscriptionPlan,
    UserSubscription,
)
from properties.models import (
    Building,
    Renter,
    RentRecord,
    Unit,
)
from properties.services.unit_service import (
    get_building_analytics,
    get_owner_analytics,
)

User = get_user_model()


class PerformanceBenchmarkBase(TestCase):
    """Base with fresh database state for benchmarks."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = User.objects.create_user(
            username="perf_bench_owner",
            email="perfbench@test.com",
            password="testpass123",
            full_name="Perf Bench Owner",
            phone="+919876543210",
        )
        plan, _ = SubscriptionPlan.objects.get_or_create(
            name="pro",
            defaults={
                "monthly_price": "29.99",
                "yearly_price": "299.99",
                "features": "Pro",
                "is_active": True,
            },
        )
        UserSubscription.objects.get_or_create(
            user=cls.owner, defaults={"plan": plan, "is_active": True}
        )
        cls.buildings = [
            Building.objects.create(
                owner=cls.owner,
                name=f"Perf Bldg {i}",
                address_line=f"{i} Perf St",
                city="Mumbai",
                state="Maharashtra",
                country="India",
                postal_code="400001",
            )
            for i in range(5)
        ]
        cls.units = []
        cls.renters = []
        for b in cls.buildings:
            for _j in range(4):
                u = Unit.objects.create(
                    owner=cls.owner,
                    building=b,
                    unit=f"PB{b.pk}-{_j}",
                    address_line=f"{b.pk} Perf St",
                    city="Mumbai",
                    state="Maharashtra",
                    country="India",
                    postal_code="400001",
                    unit_type="flat",
                    status="occupied",
                    rent_amount="10000",
                )
                cls.units.append(u)
                r = Renter.objects.create(
                    unit=u,
                    owner=cls.owner,
                    name=f"Perf Renter {u.pk}",
                    phone="+919876543210",
                    email=f"pr{u.pk}@test.com",
                    address_line=f"{b.pk} Renter St",
                    city="Mumbai",
                    state="Maharashtra",
                    country="India",
                    postal_code="400001",
                    id_proof_type="aadhaar",
                    id_proof_number=f"PERF{u.pk:010d}",
                    start_date="2024-01-01",
                    rent_amount="10000",
                    security_deposit="20000",
                )
                cls.renters.append(r)


@pytest.mark.django_db
class TestPerformanceBenchmarks(PerformanceBenchmarkBase):
    """Benchmark critical business operations."""

    def test_benchmark_owner_analytics(self, benchmark):
        """Benchmark: get_owner_analytics should complete under 100ms with 5 buildings."""
        result = benchmark(get_owner_analytics, self.owner)
        self.assertIsNotNone(result)

    def test_benchmark_building_analytics(self, benchmark):
        """Benchmark: get_building_analytics for single building."""
        b = self.buildings[0]
        result = benchmark(get_building_analytics, b)
        self.assertIsNotNone(result)

    def test_benchmark_jwt_token_generation(self, benchmark):
        """Benchmark: JWT token generation for a user."""
        benchmark(RefreshToken.for_user, self.owner)

    def test_benchmark_unit_list_api(self, benchmark):
        """Benchmark: Unit list API response time."""
        client = APIClient()
        token = str(RefreshToken.for_user(self.owner).access_token)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        benchmark(client.get, "/api/properties/units/")

    def test_benchmark_building_list_api(self, benchmark):
        """Benchmark: Building list API response time."""
        client = APIClient()
        token = str(RefreshToken.for_user(self.owner).access_token)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        benchmark(client.get, "/api/properties/buildings/")

    def test_benchmark_rent_record_creation(self, benchmark):
        """Benchmark: Rent record creation (critical hot path)."""

        def create_rent_record():
            RentRecord.objects.create(
                unit=self.units[0],
                renter=self.renters[0],
                owner=self.owner,
                rent_month=timezone.now().date().replace(day=1),
                amount="10000",
                payment_method="upi",
                status="pending",
                due_date=timezone.now().date().replace(day=5),
            )

        benchmark(create_rent_record)

    def test_benchmark_bulk_rent_record_creation(self, benchmark):
        """Benchmark: Bulk rent record creation for monthly batch job."""

        def bulk_create():
            records = [
                RentRecord(
                    unit=u,
                    renter=r,
                    owner=self.owner,
                    rent_month=timezone.now().date().replace(day=1),
                    amount="10000",
                    payment_method="upi",
                    status="pending",
                    due_date=timezone.now().date().replace(day=5),
                )
                for u, r in zip(self.units[:5], self.renters[:5], strict=True)
            ]
            RentRecord.objects.bulk_create(records, ignore_conflicts=True)

        benchmark(bulk_create)

    def test_benchmark_subscription_plan_lookup(self, benchmark):
        """Benchmark: Subscription plan lookup via get_or_create."""

        def lookup_plan():
            SubscriptionPlan.objects.get_or_create(
                name="bench",
                defaults={
                    "monthly_price": "9.99",
                    "yearly_price": "99.99",
                    "features": "Bench",
                },
            )

        benchmark(lookup_plan)

    def test_benchmark_user_subscription_upsert(self, benchmark):
        """Benchmark: User subscription upsert (update_or_create)."""
        new_user = User.objects.create_user(
            username="bench_user",
            email="bench@test.com",
            password="testpass123",
            full_name="Bench User",
            phone="+919876543210",
        )
        plan = SubscriptionPlan.objects.get(name="pro")

        def upsert_subscription():
            UserSubscription.objects.update_or_create(
                user=new_user,
                defaults={"plan": plan, "is_active": True},
            )

        benchmark(upsert_subscription)

    def test_benchmark_unit_queryset_with_building(self, benchmark):
        """Benchmark: Unit queryset with select_related('building')."""
        benchmark(
            list,
            Unit.objects.select_related("building").filter(owner=self.owner)[:10],
        )

    def test_benchmark_unit_queryset_without_select_related(self, benchmark):
        """Benchmark: Same query WITHOUT select_related (regression baseline)."""
        benchmark(
            list,
            Unit.objects.filter(owner=self.owner)[:10],
        )
