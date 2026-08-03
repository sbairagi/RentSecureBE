"""Tests for ITR deduction suggestions API."""

from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import get_user_model
from django.test import TestCase

from core.models import SubscriptionPlan, UserSubscription
from properties.models import Building, Unit

User = get_user_model()


class ITRDeductionSuggestionsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.o = User.objects.create_user(
            username="itr_deduct@t.com",
            email="itr_deduct@t.com",
            password="p",
            full_name="ITRDeduct",
            phone="+1",
        )
        cls.pp, _ = SubscriptionPlan.objects.get_or_create(
            name="itr_deduct_pro",
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
            name="ITRDB",
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
            unit="ITRD101",
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

    def test_deduction_suggestions_returns_suggestions(self):
        response = self._auth().post(
            "/properties/itr/deduction-suggestions/",
            {
                "monthly_salary": 100000,
                "monthly_rent": 25000,
                "monthly_hra": 15000,
                "city": "metro",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("hra_exemption", data)
        self.assertIn("standard_deduction", data)
        self.assertIn("repairs_and_tax", data)
        self.assertIn("total_suggested_deductions", data)
        self.assertIn("messages", data)
        self.assertGreaterEqual(data["hra_exemption"], 0)
        self.assertEqual(data["standard_deduction"], 50000)

    def test_deduction_suggestions_with_zero_values(self):
        response = self._auth().post(
            "/properties/itr/deduction-suggestions/",
            {
                "monthly_salary": 0,
                "monthly_rent": 0,
                "monthly_hra": 0,
                "city": "non_metro",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["hra_exemption"], 0)
        self.assertEqual(data["standard_deduction"], 50000)
        self.assertEqual(data["repairs_and_tax"], 0)

    def test_deduction_suggestions_requires_authentication(self):
        response = self.client.post(
            "/properties/itr/deduction-suggestions/",
            {},
            format="json",
        )
        self.assertEqual(response.status_code, 401)
