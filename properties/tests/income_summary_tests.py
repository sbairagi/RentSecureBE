"""Tests for income summary API."""

from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import get_user_model
from django.test import TestCase

from core.models import SubscriptionPlan, UserProfile, UserSubscription
from properties.models import Building, Renter, RentRecord, Unit

User = get_user_model()


class IncomeSummaryTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.o = User.objects.create_user(
            username="income_user@t.com",
            email="income_user@t.com",
            password="p",
            full_name="IncomeUser",
            phone="+1",
        )
        cls.pp, _ = SubscriptionPlan.objects.get_or_create(
            name="income_pro",
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
            name="INCB",
            defaults={
                "address_line": "1 St",
                "city": "C",
                "state": "S",
                "country": "CO",
                "postal_code": "1",
            },
        )
        self.u, _ = Unit.objects.get_or_create(
            owner=self.o,
            building=b,
            unit="INC101",
            defaults={
                "unit_type": "flat",
                "address_line": "1 St",
                "city": "C",
                "state": "S",
                "country": "CO",
                "postal_code": "1",
            },
        )
        profile, _ = UserProfile.objects.get_or_create(user=self.o)
        profile.salary = 600000
        profile.other_income = 100000
        profile.save(update_fields=["salary", "other_income"])

    def _auth(self):
        c = APIClient()
        c.credentials(
            HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(self.o).access_token}"
        )
        return c

    def test_income_summary_returns_breakdown(self):
        renter = Renter.objects.create(
            unit=self.u,
            name="IncRenter",
            phone="+911111111111",
            rent_amount=10000,
            start_date="2025-01-01",
        )
        RentRecord.objects.create(
            renter=renter,
            unit=self.u,
            due_date="2025-02-01",
            amount=120000,
            payment_method="upi",
            status=RentRecord.Status.PAID,
            payout_status="SUCCESS",
        )

        response = self._auth().get("/properties/owner/income-summary/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["salary"], 600000)
        self.assertEqual(data["other_income"], 100000)
        self.assertEqual(data["rent_income"], 120000)
        self.assertEqual(data["total_income"], 820000)
        self.assertIn("estimated_tax", data)
        self.assertIn("tax_brackets", data)
        self.assertGreaterEqual(data["estimated_tax"], 0)

    def test_income_summary_empty_when_no_rent_records(self):
        response = self._auth().get("/properties/owner/income-summary/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["rent_income"], 0)
        self.assertEqual(data["salary"], 600000)
        self.assertEqual(data["other_income"], 100000)
        self.assertEqual(data["total_income"], 700000)
        self.assertIn("estimated_tax", data)

    def test_income_summary_requires_authentication(self):
        response = self.client.get("/properties/owner/income-summary/")
        self.assertEqual(response.status_code, 401)
