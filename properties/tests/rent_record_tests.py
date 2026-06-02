"""Tests for rent record and extra charge viewsets"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from core.models import SubscriptionPlan, UserSubscription
from properties.models import Building, Unit

User = get_user_model()


class RentRecordViewSetTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.o = User.objects.create_user(
            username="rro@t.com",
            email="rro@t.com",
            password="p",
            full_name="RRO",
            phone="+1",
        )
        cls.pp, _ = SubscriptionPlan.objects.get_or_create(
            name="rr_pro",
            defaults={
                "monthly_price": Decimal("29.99"),
                "yearly_price": Decimal("299.99"),
                "features": "Pro",
            },
        )

    def setUp(self):
        UserSubscription.objects.update_or_create(
            user=self.o, defaults={"plan": self.pp, "is_active": True}
        )
        b, _ = Building.objects.get_or_create(
            owner=self.o,
            name="RRB",
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
            unit="RR101",
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

    def test_unauth_list(self):
        self.assertEqual(self.client.get("/properties/rent-records/").status_code, 401)

    def test_list(self):
        self.assertEqual(self._auth().get("/properties/rent-records/").status_code, 200)


class ExtraChargeViewSetTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.o = User.objects.create_user(
            username="eco@t.com",
            email="eco@t.com",
            password="p",
            full_name="ECO",
            phone="+1",
        )
        cls.pp, _ = SubscriptionPlan.objects.get_or_create(
            name="ec_pro",
            defaults={
                "monthly_price": Decimal("29.99"),
                "yearly_price": Decimal("299.99"),
                "features": "Pro",
            },
        )

    def setUp(self):
        UserSubscription.objects.update_or_create(
            user=self.o, defaults={"plan": self.pp, "is_active": True}
        )
        b, _ = Building.objects.get_or_create(
            owner=self.o,
            name="ECB",
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
            unit="EC101",
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

    def test_extra_charge_unauth(self):
        self.assertEqual(
            self.client.post("/properties/extra-charges/", {}).status_code, 401
        )
