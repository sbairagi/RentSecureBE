"""Tests for unit viewset"""

from decimal import Decimal

from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import get_user_model
from django.test import TestCase

from core.models import PlanFeatureLimit, SubscriptionPlan, UserSubscription
from properties.models import Building, Unit

User = get_user_model()


class UnitViewSetTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.o = User.objects.create_user(
            username="uo@t.com",
            email="uo@t.com",
            password="p",
            full_name="UO",
            phone="+1",
        )
        cls.ot = User.objects.create_user(
            username="uot@t.com",
            email="uot@t.com",
            password="p",
            full_name="UT",
            phone="+2",
        )
        cls.fp, _ = SubscriptionPlan.objects.get_or_create(
            name="u_free",
            defaults={
                "monthly_price": Decimal("0"),
                "yearly_price": Decimal("0"),
                "features": "F",
            },
        )
        cls.pp, _ = SubscriptionPlan.objects.get_or_create(
            name="u_pro",
            defaults={
                "monthly_price": Decimal("29.99"),
                "yearly_price": Decimal("299.99"),
                "features": "P",
            },
        )

    def setUp(self):
        PlanFeatureLimit.objects.get_or_create(
            plan=self.fp, feature_key="max_units", defaults={"value": "3"}
        )
        PlanFeatureLimit.objects.get_or_create(
            plan=self.pp, feature_key="max_units", defaults={"value": "10"}
        )
        UserSubscription.objects.update_or_create(
            user=self.o, defaults={"plan": self.pp, "is_active": True}
        )
        self.b, _ = Building.objects.get_or_create(
            owner=self.o,
            name="UB",
            defaults={
                "address_line": "1 St",
                "city": "C",
                "state": "S",
                "country": "CO",
                "postal_code": "1",
            },
        )
        self.u1, _ = Unit.objects.get_or_create(
            owner=self.o,
            building=self.b,
            unit="101",
            defaults={
                "unit_type": "flat",
                "address_line": "1 St",
                "city": "C",
                "state": "S",
                "country": "CO",
                "postal_code": "1",
            },
        )
        self.ou, _ = Unit.objects.get_or_create(
            owner=self.ot,
            unit="201",
            defaults={
                "unit_type": "flat",
                "address_line": "2 St",
                "city": "C",
                "state": "S",
                "country": "CO",
                "postal_code": "2",
            },
        )

    def _auth(self, u):
        c = APIClient()
        c.credentials(
            HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(u).access_token}"
        )
        return c

    def test_unauth_list(self):
        self.assertEqual(self.client.get("/properties/units/").status_code, 401)

    def test_list_own(self):
        r = self._auth(self.o).get("/properties/units/")
        self.assertEqual(r.status_code, 200)

    def test_no_see_other(self):
        r = self._auth(self.ot).get("/properties/units/")
        self.assertEqual(r.status_code, 200)

    def test_retrieve_own(self):
        r = self._auth(self.o).get(f"/properties/units/{self.u1.id}/")
        self.assertEqual(r.status_code, 200)

    def test_no_retrieve_other(self):
        r = self._auth(self.ot).get(f"/properties/units/{self.u1.id}/")
        self.assertEqual(r.status_code, 404)

    def test_create(self):
        r = self._auth(self.o).post(
            "/properties/units/",
            {
                "building": self.b.id,
                "unit": "103",
                "unit_type": "flat",
                "address_line": "3 St",
                "city": "C",
                "state": "S",
                "country": "CO",
                "postal_code": "3",
            },
        )
        self.assertEqual(r.status_code, 201)

    def test_update_own(self):
        r = self._auth(self.o).patch(
            f"/properties/units/{self.u1.id}/",
            {
                "unit": "U101",
                "building": self.b.id,
                "unit_type": "flat",
                "address_line": "1 St",
                "city": "C",
                "state": "S",
                "country": "CO",
                "postal_code": "1",
            },
        )
        self.assertEqual(r.status_code, 200)

    def test_no_update_other(self):
        r = self._auth(self.ot).patch(
            f"/properties/units/{self.u1.id}/", {"unit": "Hack"}
        )
        self.assertEqual(r.status_code, 404)

    def test_delete_own(self):
        r = self._auth(self.o).delete(f"/properties/units/{self.u1.id}/")
        self.assertEqual(r.status_code, 204)

    def test_no_delete_other(self):
        r = self._auth(self.ot).delete(f"/properties/units/{self.u1.id}/")
        self.assertEqual(r.status_code, 404)
