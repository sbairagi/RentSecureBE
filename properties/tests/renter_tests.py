"""Tests for renter viewset"""

from datetime import date
from decimal import Decimal

from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase

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


class RenterViewSetLimitAndPermissionTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.o = User.objects.create_user(
            username="renterlim@t.com",
            email="renterlim@t.com",
            password="p",
            full_name="RenterLimOwner",
            phone="+1",
        )
        cls.sub = SubscriptionPlan.objects.create(
            name="r_limit_pro",
            monthly_price=Decimal("29.99"),
            yearly_price=Decimal("299.99"),
        )
        UserSubscription.objects.create(user=cls.o, plan=cls.sub, is_active=True)
        PlanFeatureLimit.objects.create(
            plan=cls.sub, feature_key="max_renters", value="1"
        )
        cls.b, _ = Building.objects.get_or_create(
            owner=cls.o,
            name="RLB",
            defaults={
                "address_line": "1 St",
                "city": "C",
                "state": "S",
                "country": "CO",
                "postal_code": "1",
            },
        )
        cls.u, _ = Unit.objects.get_or_create(
            owner=cls.o,
            building=cls.b,
            unit="RL101",
            defaults={
                "unit_type": "flat",
                "address_line": "1 St",
                "city": "C",
                "state": "S",
                "country": "CO",
                "postal_code": "1",
            },
        )

    def setUp(self):
        cache.clear()

    def _auth(self, u):
        c = APIClient()
        c.credentials(
            HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(u).access_token}"
        )
        return c

    def test_create_renter_denied_when_limit_reached(self):
        Renter.objects.create(
            unit=self.u,
            name="Renter 1",
            email="r1@t.com",
            phone="+1111111111",
            rent_amount=Decimal("1000"),
            start_date=date.today(),
        )
        response = self._auth(self.o).post(
            "/properties/renters/",
            {
                "unit": self.u.id,
                "name": "Renter 2",
                "email": "r2@t.com",
                "phone": "+1222222222",
                "rent_amount": "1000",
                "start_date": str(date.today()),
            },
        )
        self.assertEqual(response.status_code, 403)

    def test_other_user_cannot_delete_renter(self):
        attacker = User.objects.create_user(
            username="att@t.com",
            email="att@t.com",
            password="p",
            full_name="Attacker",
            phone="+2",
        )
        renter = Renter.objects.create(
            unit=self.u,
            name="RenterX",
            email="rx@t.com",
            phone="+1333333333",
            rent_amount=Decimal("1000"),
            start_date=date.today(),
        )
        response = self._auth(attacker).delete(f"/properties/renters/{renter.id}/")
        self.assertEqual(response.status_code, 404)
