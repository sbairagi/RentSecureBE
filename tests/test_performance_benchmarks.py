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
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import get_user_model
from django.utils import timezone

from core.models import SubscriptionPlan, UserSubscription
from properties.models import Building, Renter, RentRecord, Unit
from properties.services.unit_service import get_building_analytics, get_owner_analytics

User = get_user_model()


@pytest.fixture
def benchmark_data(db):
    """Shared benchmark dataset: owner, 5 buildings, 20 units, 20 renters, pro plan."""
    owner = User.objects.create_user(
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
        user=owner, defaults={"plan": plan, "is_active": True}
    )
    buildings = [
        Building.objects.create(
            owner=owner,
            name=f"Perf Bldg {i}",
            address_line=f"{i} Perf St",
            city="Mumbai",
            state="Maharashtra",
            country="India",
            postal_code="400001",
        )
        for i in range(5)
    ]
    units = []
    renters = []
    for b in buildings:
        for _j in range(4):
            u = Unit.objects.create(
                owner=owner,
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
            units.append(u)
            renter_user = User.objects.create_user(
                username=f"perf_renter_{u.pk}",
                email=f"pr{u.pk}@test.com",
                password="testpass123",
            )
            r = Renter.objects.create(
                unit=u,
                user=renter_user,
                name=f"Perf Renter {u.pk}",
                phone="+919876543210",
                email=f"pr{u.pk}@test.com",
                start_date="2024-01-01",
                rent_amount="10000",
            )
            renters.append(r)

    return type(
        "BenchmarkData",
        (),
        {
            "owner": owner,
            "plan": plan,
            "buildings": buildings,
            "units": units,
            "renters": renters,
        },
    )()


@pytest.mark.django_db
class TestPerformanceBenchmarks:
    """Benchmark critical business operations."""

    def test_benchmark_owner_analytics(self, benchmark, benchmark_data):
        """Benchmark: get_owner_analytics should complete under 100ms with 5 buildings."""
        result = benchmark(get_owner_analytics, benchmark_data.owner)
        assert result is not None

    def test_benchmark_building_analytics(self, benchmark, benchmark_data):
        """Benchmark: get_building_analytics for single building."""
        b = benchmark_data.buildings[0]
        result = benchmark(get_building_analytics, b)
        assert result is not None

    def test_benchmark_jwt_token_generation(self, benchmark, benchmark_data):
        """Benchmark: JWT token generation for a user."""
        benchmark(RefreshToken.for_user, benchmark_data.owner)

    def test_benchmark_unit_list_api(self, benchmark, benchmark_data):
        """Benchmark: Unit list API response time."""
        client = APIClient()
        token = str(RefreshToken.for_user(benchmark_data.owner).access_token)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        benchmark(client.get, "/api/properties/units/")

    def test_benchmark_building_list_api(self, benchmark, benchmark_data):
        """Benchmark: Building list API response time."""
        client = APIClient()
        token = str(RefreshToken.for_user(benchmark_data.owner).access_token)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        benchmark(client.get, "/api/properties/buildings/")

    def test_benchmark_rent_record_creation(self, benchmark, benchmark_data):
        """Benchmark: Rent record creation (critical hot path)."""

        def create_rent_record():
            RentRecord.objects.get_or_create(
                unit=benchmark_data.units[0],
                renter=benchmark_data.renters[0],
                defaults={
                    "amount": "10000",
                    "payment_method": "upi",
                    "status": "pending",
                    "due_date": timezone.now().date().replace(day=5),
                },
            )

        benchmark(create_rent_record)

    def test_benchmark_bulk_rent_record_creation(self, benchmark, benchmark_data):
        """Benchmark: Bulk rent record creation for monthly batch job."""

        def bulk_create():
            records = [
                RentRecord(
                    unit=u,
                    renter=r,
                    amount="10000",
                    payment_method="upi",
                    status="pending",
                    due_date=timezone.now().date().replace(day=5),
                )
                for u, r in zip(
                    benchmark_data.units[:5], benchmark_data.renters[:5], strict=True
                )
            ]
            RentRecord.objects.bulk_create(records, ignore_conflicts=True)

        benchmark(bulk_create)

    def test_benchmark_subscription_plan_lookup(self, benchmark, benchmark_data):
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

    def test_benchmark_user_subscription_upsert(self, benchmark, benchmark_data):
        """Benchmark: User subscription upsert (update_or_create)."""
        new_user = User.objects.create_user(
            username="bench_user",
            email="bench@test.com",
            password="testpass123",
            full_name="Bench User",
            phone="+919876543210",
        )
        plan = benchmark_data.plan

        def upsert_subscription():
            UserSubscription.objects.update_or_create(
                user=new_user,
                defaults={"plan": plan, "is_active": True},
            )

        benchmark(upsert_subscription)

    def test_benchmark_unit_queryset_with_building(self, benchmark, benchmark_data):
        """Benchmark: Unit queryset with select_related('building')."""
        benchmark(
            list,
            Unit.objects.select_related("building").filter(owner=benchmark_data.owner)[
                :10
            ],
        )

    def test_benchmark_unit_queryset_without_select_related(
        self, benchmark, benchmark_data
    ):
        """Benchmark: Same query WITHOUT select_related (regression baseline)."""
        benchmark(
            list,
            Unit.objects.filter(owner=benchmark_data.owner)[:10],
        )
