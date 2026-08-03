"""Tests for ITR CA contact API."""

from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import get_user_model
from django.test import TestCase

from core.models import SubscriptionPlan, UserSubscription
from properties.models import Building, ITRCAContactRequest, Unit

User = get_user_model()


class ITRCAContactTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.o = User.objects.create_user(
            username="ca_contact@t.com",
            email="ca_contact@t.com",
            password="p",
            full_name="CAContact",
            phone="+1",
        )
        cls.pp, _ = SubscriptionPlan.objects.get_or_create(
            name="ca_pro",
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
            name="CACB",
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
            unit="CA101",
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

    def test_submit_ca_contact_returns_success(self):
        response = self._auth().post(
            "/properties/itr/contact-ca/",
            {
                "phone": "+911111111111",
                "email": "owner@example.com",
                "pan_number": "ABCDE1234F",
                "message": "Need help with ITR",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "submitted")
        self.assertTrue(
            ITRCAContactRequest.objects.filter(
                user=self.o, pan_number="ABCDE1234F"
            ).exists()
        )

    def test_submit_ca_contact_missing_fields_returns_400(self):
        response = self._auth().post(
            "/properties/itr/contact-ca/",
            {"pan_number": "ABCDE1234F"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_anonymous_user_cannot_submit_ca_contact(self):
        response = self.client.post(
            "/properties/itr/contact-ca/",
            {
                "phone": "+911111111111",
                "email": "owner@example.com",
                "pan_number": "ABCDE1234F",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 401)
