"""Tests for renter viewset"""

from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from core.models import PlanFeatureLimit, SubscriptionPlan, UserSubscription
from properties.models import Building, Renter, Unit

User = get_user_model()


class RenterViewSetTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.o = User.objects.create_user(
            username="ro@t.com",
            email="ro@t.com",
            password="p",
            full_name="RO",
            phone="+1",
        )
        cls.ot = User.objects.create_user(
            username="rot@t.com",
            email="rot@t.com",
            password="p",
            full_name="RT",
            phone="+2",
        )
        cls.fp, _ = SubscriptionPlan.objects.get_or_create(
            name="r_free",
            defaults={
                "monthly_price": Decimal("0"),
                "yearly_price": Decimal("0"),
                "features": "Free",
            },
        )
        cls.pp, _ = SubscriptionPlan.objects.get_or_create(
            name="r_pro",
            defaults={
                "monthly_price": Decimal("29.99"),
                "yearly_price": Decimal("299.99"),
                "features": "Pro",
            },
        )

    def setUp(self):
        PlanFeatureLimit.objects.get_or_create(
            plan=self.fp, feature_key="max_renters", defaults={"value": "2"}
        )
        PlanFeatureLimit.objects.get_or_create(
            plan=self.pp, feature_key="max_renters", defaults={"value": "10"}
        )
        UserSubscription.objects.update_or_create(
            user=self.o, defaults={"plan": self.pp, "is_active": True}
        )
        b, _ = Building.objects.get_or_create(
            owner=self.o,
            name="RB",
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
            unit="R101",
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
            unit="R201",
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
        self.assertEqual(self.client.get("/properties/renters/").status_code, 401)

    def test_list_empty(self):
        self.assertEqual(
            self._auth(self.o).get("/properties/renters/").status_code, 200
        )

    def test_create_bad(self):
        self.assertEqual(
            self._auth(self.o).post("/properties/renters/", {}).status_code, 400
        )

    def test_retrieve(self):
        r = Renter.objects.create(
            unit=self.u,
            name="TR",
            email="tr@t.com",
            phone="+1222222222",
            rent_amount=Decimal("1000"),
            start_date=date.today(),
            id_proof="id.pdf",
            rent_agreement="ag.pdf",
        )
        self.assertEqual(
            self._auth(self.o).get(f"/properties/renters/{r.id}/").status_code, 200
        )

    def test_no_retrieve_other(self):
        r = Renter.objects.create(
            unit=self.u,
            name="TR2",
            email="tr2@t.com",
            phone="+1333333333",
            rent_amount=Decimal("1000"),
            start_date=date.today(),
            id_proof="id.pdf",
            rent_agreement="ag.pdf",
        )
        self.assertEqual(
            self._auth(self.ot).get(f"/properties/renters/{r.id}/").status_code, 404
        )

    def test_delete(self):
        r = Renter.objects.create(
            unit=self.u,
            name="TR3",
            email="tr3@t.com",
            phone="+1444444444",
            rent_amount=Decimal("1000"),
            start_date=date.today(),
            id_proof="id.pdf",
            rent_agreement="ag.pdf",
        )
        self.assertEqual(
            self._auth(self.o).delete(f"/properties/renters/{r.id}/").status_code, 204
        )
