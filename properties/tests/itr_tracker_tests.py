"""Tests for ITR tracker API."""

from datetime import date

from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import get_user_model
from django.test import TestCase

from core.models import SubscriptionPlan, UserSubscription
from properties.models import Building, ITRTracker, Unit

User = get_user_model()


class ITRTrackerTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.o = User.objects.create_user(
            username="itr_tracker@t.com",
            email="itr_tracker@t.com",
            password="p",
            full_name="ITRTracker",
            phone="+1",
        )
        cls.pp, _ = SubscriptionPlan.objects.get_or_create(
            name="itr_tracker_pro",
            defaults={
                "monthly_price": 0,
                "yearly_price": 0,
                "features": "Pro",
            },
        )

    def setUp(self):
        UserSubscription.objects.update_or_create(
            user=self.o, defaults={"plan": self.pp, "is_active": True}
        )
        b, _ = Building.objects.get_or_create(
            owner=self.o,
            name="ITRTB",
            defaults={
                "address_line": "1 St",
                "city": "C",
                "state": "S",
                "country": "CO",
                "postal_code": "1",
            },
        )
        Unit.objects.get_or_create(
            owner=self.o,
            building=b,
            unit="ITRT101",
            defaults={
                "unit_type": "flat",
                "address_line": "1 St",
                "city": "C",
                "state": "S",
                "country": "CO",
                "postal_code": "1",
            },
        )

    def _auth(self):
        c = APIClient()
        c.credentials(
            HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(self.o).access_token}"
        )
        return c

    def test_itr_tracker_creates_default_tracker(self):
        response = self._auth().get("/properties/itr/tracker/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("fy", data)
        self.assertIn("total_rent_income", data)
        self.assertIn("total_deductions", data)
        self.assertIn("ca_review_status", data)
        self.assertIn("last_updated", data)
        self.assertEqual(data["total_rent_income"], 0)
        self.assertEqual(data["total_deductions"], 0)
        self.assertEqual(data["ca_review_status"], "PENDING")
        self.assertTrue(ITRTracker.objects.filter(user=self.o).exists())

    def test_itr_tracker_returns_existing_data(self):
        ITRTracker.objects.create(
            user=self.o,
            fy_start=date(2024, 4, 1),
            fy_end=date(2025, 3, 31),
            total_rent_income=280000,
            total_deductions=50000,
            ca_review_status=ITRTracker.CAReviewStatus.READY,
        )
        response = self._auth().get("/properties/itr/tracker/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["fy"], "2024-2025")
        self.assertEqual(data["total_rent_income"], 280000)
        self.assertEqual(data["total_deductions"], 50000)
        self.assertEqual(data["ca_review_status"], "READY")

    def test_anonymous_user_cannot_access_itr_tracker(self):
        response = self.client.get("/properties/itr/tracker/")
        self.assertEqual(response.status_code, 401)
