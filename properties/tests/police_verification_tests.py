"""Tests for police verification dashboard stats."""

from datetime import date

from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import get_user_model
from django.test import TestCase

from core.models import SubscriptionPlan, UserSubscription
from properties.models import Building, PoliceVerification, Renter, Unit

User = get_user_model()


class PoliceVerificationDashboardStatsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.o = User.objects.create_user(
            username="pvd@t.com",
            email="pvd@t.com",
            password="p",
            full_name="PVD",
            phone="+1",
        )
        cls.pp, _ = SubscriptionPlan.objects.get_or_create(
            name="pvd_pro",
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
            name="PVDB",
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
            unit="PV101",
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

    def test_dashboard_stats_returns_counts(self):
        renter1 = Renter.objects.create(
            unit=self.u,
            name="PV Renter 1",
            phone="+911111111111",
            rent_amount=10000,
            start_date=date.today(),
        )
        renter2 = Renter.objects.create(
            unit=self.u,
            name="PV Renter 2",
            phone="+922222222222",
            rent_amount=10000,
            start_date=date.today(),
        )
        PoliceVerification.objects.create(
            user=self.o,
            renter=renter1,
            unit=self.u,
            status=PoliceVerification.PoliceVerificationStatus.VERIFIED,
        )
        PoliceVerification.objects.create(
            user=self.o,
            renter=renter2,
            unit=self.u,
            status=PoliceVerification.PoliceVerificationStatus.SUBMITTED,
        )

        response = self._auth().get("/properties/police-verifications/dashboard_stats/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["verified"], 1)
        self.assertEqual(data["submitted"], 1)
        self.assertEqual(data["not_started"], 0)

    def test_dashboard_stats_empty_when_no_verifications(self):
        response = self._auth().get("/properties/police-verifications/dashboard_stats/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["verified"], 0)
        self.assertEqual(data["submitted"], 0)
        self.assertEqual(data["not_started"], 0)
