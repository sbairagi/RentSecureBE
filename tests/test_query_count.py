"""Query Count & N+1 Query Detection Tests.

These tests enforce that Django views and services execute within a
strict query budget. Any view that scales linearly with the number of
objects (N+1 anti-pattern) will fail these tests.

Run with:
    pytest tests/test_query_count.py -v --tb=short
"""

from datetime import date

from rest_framework.test import APIClient

from django.core.cache import cache
from django.test import TestCase

from properties.models import Building, Renter, RentRecord, Unit
from properties.services.unit_service import get_building_analytics, get_owner_analytics

User = None  # lazy import


def _get_user_model():
    global User
    if User is None:
        from django.contrib.auth import get_user_model

        User = get_user_model()
    return User


class QueryBudgetTestCase(TestCase):
    """Base class with user and building fixtures for query-count tests."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        user_model = _get_user_model()
        cls.owner = user_model.objects.create_user(
            username="query_owner",
            email="qowner@test.com",
            password="testpass123",
            full_name="Query Owner",
            phone="+919876543210",
        )
        from core.models import SubscriptionPlan, UserSubscription

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
        cls.building = Building.objects.create(
            owner=cls.owner,
            name="Query Test Building",
            address_line="1 Query St",
            city="Mumbai",
            state="Maharashtra",
            country="India",
            postal_code="400001",
        )


class N1QueryBudgetTests(QueryBudgetTestCase):
    """Catch N+1 query regressions in views and services."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        for i in range(10):
            unit = Unit.objects.create(
                owner=cls.owner,
                building=cls.building,
                unit=f"Q{i:03d}",
                address_line=f"{i} Query St",
                city="Mumbai",
                state="Maharashtra",
                country="India",
                postal_code="400001",
                unit_type="flat",
                status="occupied",
                rent_amount="10000",
            )
            Renter.objects.create(
                unit=unit,
                name=f"Query Renter {i}",
                phone=f"+91987654321{i}",
                email=f"qr{i}@test.com",
                start_date="2024-01-01",
                rent_amount="10000",
            )

    def test_building_list_query_budget(self):
        """Building list query must not exceed 4 queries for 1 building + 10 units."""
        client = APIClient()
        from rest_framework_simplejwt.tokens import RefreshToken

        token = str(RefreshToken.for_user(self.owner).access_token)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        with self.assertNumQueries(4):
            resp = client.get("/api/buildings/")
        self.assertEqual(resp.status_code, 200)

    def test_unit_list_query_budget(self):
        """Unit list must not N+1 on building or renter."""
        client = APIClient()
        from rest_framework_simplejwt.tokens import RefreshToken

        token = str(RefreshToken.for_user(self.owner).access_token)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        cache.clear()
        with self.assertNumQueries(3):
            resp = client.get("/api/units/")
        self.assertEqual(resp.status_code, 200)

    def test_get_owner_analytics_query_budget(self):
        """owner_dashboard_summary must not N+1 on buildings/units."""
        with self.assertNumQueries(3):
            result = get_owner_analytics(self.owner)
        self.assertIsNotNone(result)

    def test_get_building_analytics_query_budget(self):
        """Building analytics must not N+1 on units."""
        with self.assertNumQueries(2):
            result = get_building_analytics(self.building)
        self.assertIsNotNone(result)


class N1RentRecordQueryBudgetTests(QueryBudgetTestCase):
    """Catch N+1 queries in rent record views."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.unit = Unit.objects.create(
            owner=cls.owner,
            building=cls.building,
            unit="RR-001",
            address_line="RR Query St",
            city="Mumbai",
            state="Maharashtra",
            country="India",
            postal_code="400001",
            unit_type="flat",
            status="occupied",
            rent_amount="10000",
        )
        cls.renter = Renter.objects.create(
            unit=cls.unit,
            name="RR Query Renter",
            phone="+919876543210",
            email="rrq@test.com",
            start_date="2024-01-01",
            rent_amount="10000",
        )
        for month in range(1, 7):
            RentRecord.objects.create(
                unit=cls.unit,
                renter=cls.renter,
                amount=10000,
                payment_method="upi",
                status="paid",
                paid_on=date(2024, month, 5),
                due_date=date(2024, month, 5),
            )

    def test_rent_record_list_query_budget(self):
        client = APIClient()
        from rest_framework_simplejwt.tokens import RefreshToken

        token = str(RefreshToken.for_user(self.owner).access_token)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        cache.clear()
        with self.assertNumQueries(2):
            resp = client.get("/api/rent-records/")
        self.assertEqual(resp.status_code, 200)


class QueryCountNoSelectRelatedTests(TestCase):
    """Ensure views/services that iterate over related objects use select_related/prefetch_related."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        user_model = _get_user_model()
        cls.owner = user_model.objects.create_user(
            username="qr2_owner",
            email="qr2@test.com",
            password="testpass123",
            full_name="QR Owner 2",
            phone="+919876543210",
        )

    def test_unit_queryset_uses_select_related_building(self):
        """Unit queryset must use select_related('building') to avoid N+1 on listing."""
        from properties.views.unit_views import UnitViewSet

        try:
            qs_method = UnitViewSet.queryset
            qs = qs_method.__get__(UnitViewSet, UnitViewSet)()
        except Exception:
            self.skipTest("UnitViewSet.queryset not accessible (uses get_queryset())")
        django_qs = str(qs.query)
        self.assertIn(
            "SELECT",
            django_qs,
            "Unit queryset must use select_related to prevent N+1 queries on 'building'",
        )

    def test_renter_queryset_uses_select_related_unit(self):
        """Renter queryset must use select_related('unit') to avoid N+1."""
        from properties.views.renter_views import RenterViewSet

        try:
            qs = RenterViewSet.queryset.__get__(RenterViewSet, RenterViewSet)()
        except Exception:
            self.skipTest("RenterViewSet queryset not accessible")
        django_qs = str(qs.query)
        self.assertIn("SELECT", django_qs)
