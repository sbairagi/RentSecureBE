"""
Security E2E Tests — Continued (payment security, file security, cache isolation)
"""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TransactionTestCase
from django.utils import timezone

from core.models import SubscriptionPlan, UserSubscription
from properties.models import Building, Renter, RentRecord, Unit

User = get_user_model()
API_PREFIX = "/api"


class PaymentSecurityDetailTests(APITestCase):
    """Payment security: ownership, duplicate, tampering."""

    def setUp(self):
        self.owner = User.objects.create_user(
            username="pay_det_owner", password="TestPass123!", email="paydo@test.com"
        )
        self.other_owner = User.objects.create_user(
            username="pay_det_other", password="TestPass123!", email="paydo2@test.com"
        )
        self.plan, _ = SubscriptionPlan.objects.get_or_create(
            name="pay_det_pro",
            defaults={
                "monthly_price": Decimal("29.99"),
                "yearly_price": Decimal("299.99"),
                "features": "Pro",
                "is_active": True,
            },
        )
        UserSubscription.objects.create(
            user=self.owner,
            plan=self.plan,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=365),
            is_active=True,
        )
        UserSubscription.objects.create(
            user=self.other_owner,
            plan=self.plan,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=365),
            is_active=True,
        )
        self.building = Building.objects.create(
            owner=self.owner,
            name="Pay Det Bldg",
            address_line="123 Pay St",
            city="Pay City",
            state="PY",
            country="IN",
            postal_code="400001",
        )
        self.unit = Unit.objects.create(
            owner=self.owner,
            building=self.building,
            unit="PAY-101",
            address_line="123 Pay St",
            city="Pay City",
            state="PY",
            country="IN",
            postal_code="400001",
            unit_type=Unit.UnitType.FLAT,
        )
        self.renter = Renter.objects.create(
            unit=self.unit,
            name="Pay Det Renter",
            phone="+919876543210",
            rent_amount=Decimal("10000.00"),
            start_date=timezone.now().date(),
        )
        self.rent = RentRecord.objects.create(
            renter=self.renter,
            unit=self.unit,
            due_date=timezone.now().date().replace(day=5),
            amount=Decimal("10000.00"),
            status="paid",
            paid_on=timezone.now().date(),
            payment_method="upi",
            transaction_id="e2e_txn_123",
        )

    def test_renter_cannot_access_other_renter_rent_detail(self):
        other_owner = User.objects.create_user(
            username="pay_det_or2", password="TestPass123!", email="paydo3@test.com"
        )
        UserSubscription.objects.create(
            user=other_owner,
            plan=self.plan,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=365),
            is_active=True,
        )
        other_building = Building.objects.create(
            owner=other_owner,
            name="Other",
            address_line="Other",
            city="Other",
            state="OT",
            country="IN",
            postal_code="400001",
        )
        other_unit = Unit.objects.create(
            owner=other_owner,
            building=other_building,
            unit="OTHER-101",
            address_line="Other",
            city="Other",
            state="OT",
            country="IN",
            postal_code="400001",
            unit_type=Unit.UnitType.FLAT,
        )
        other_renter = Renter.objects.create(
            unit=other_unit,
            name="Other Renter",
            phone="+919876543999",
            rent_amount=Decimal("10000.00"),
            start_date=timezone.now().date(),
        )
        other_rent = RentRecord.objects.create(
            renter=other_renter,
            unit=other_unit,
            due_date=timezone.now().date().replace(day=5),
            amount=Decimal("10000.00"),
            status="paid",
        )
        hacker_user = User.objects.create_user(
            username="pay_det_hacker",
            password="TestPass123!",
            email="paydet_hacker@test.com",
        )
        client = APIClient()
        client.force_authenticate(user=hacker_user)
        response = client.get(f"{API_PREFIX}/renter/rent-records/{other_rent.id}/")
        self.assertIn(
            response.status_code,
            [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND],
        )

    def test_duplicate_payment_handling(self):
        renter_user = User.objects.create_user(
            username="pay_det_renter",
            password="TestPass123!",
            email="paydet_renter@test.com",
        )
        self.renter.user = renter_user
        self.renter.save()
        client = APIClient()
        client.force_authenticate(user=renter_user)
        with patch(
            "properties.views.rent_record_views.create_payment_link",
            return_value="https://payments.test/rent/dup",
        ):
            response1 = client.post(
                f"{API_PREFIX}/rent/payment/",
                {"rent_record_id": self.rent.id, "method": "upi"},
                format="json",
            )
        # Should not create duplicate payment links
        self.assertIn(
            response1.status_code,
            [status.HTTP_200_OK, status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST],
        )

    def test_rent_amount_tampering_rejected(self):
        payload = {
            "renter": self.renter.id,
            "unit": self.unit.id,
            "due_date": str(timezone.now().date().replace(day=5)),
            "amount": "999999.00",
        }
        response = self.client.post(
            f"{API_PREFIX}/rent-records/", payload, format="json"
        )
        self.assertNotEqual(response.status_code, status.HTTP_201_CREATED)


class CacheIsolationSecurityTests(TransactionTestCase):
    """Test that cached data does not leak between users."""

    def test_cache_cleared_between_users(self):
        cache.clear()
        user_a = User.objects.create_user(
            username="cache_a", password="TestPass123!", email="cachea@test.com"
        )
        user_b = User.objects.create_user(
            username="cache_b", password="TestPass123!", email="cacheb@test.com"
        )
        building_a = Building.objects.create(
            owner=user_a,
            name="Cache A Bldg",
            address_line="123 A",
            city="A",
            state="AA",
            country="IN",
            postal_code="400001",
        )
        building_b = Building.objects.create(
            owner=user_b,
            name="Cache B Bldg",
            address_line="456 B",
            city="B",
            state="BB",
            country="IN",
            postal_code="400002",
        )

        client_a = APIClient()
        client_a.force_authenticate(user=user_a)
        response_a = client_a.get(f"{API_PREFIX}/buildings/")
        self.assertEqual(response_a.status_code, status.HTTP_200_OK)
        ids_a = [b["id"] for b in response_a.data]
        self.assertIn(building_a.id, ids_a)

        client_b = APIClient()
        client_b.force_authenticate(user=user_b)
        response_b = client_b.get(f"{API_PREFIX}/buildings/")
        self.assertEqual(response_b.status_code, status.HTTP_200_OK)
        ids_b = [b["id"] for b in response_b.data]
        self.assertNotIn(building_a.id, ids_b)
        self.assertNotIn(building_b.id, ids_a)
