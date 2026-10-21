"""Regression tests for the rent agreement draft quota.

The free plan shipped with ``rent_agreement_drafts = "1"`` and the paid plans
had no ``rent_agreement_drafts`` row at all. ``FeatureEnforcer`` resolves a
missing row to ``0``, so agreement uploads failed for every subscriber with
*"You have reached your draft creation limit."*
"""

from datetime import date
from decimal import Decimal
from unittest.mock import patch

from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase

from core.models import PlanFeatureLimit, SubscriptionPlan, UserSubscription
from core.plan_limits import FREE_PLAN_LIMITS, PLAN_LIMITS
from properties.models import Building, Renter, Unit

User = get_user_model()

DRAFTS_URL = "/properties/rent-agreement-drafts/"


def _auth(user):
    client = APIClient()
    client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}"
    )
    return client


class AgreementDraftQuotaTests(TestCase):
    def setUp(self):
        cache.clear()
        self.owner = User.objects.create_user(
            username="quota_owner", password="p", full_name="QuotaOwner", phone="+1"
        )
        self.plan = SubscriptionPlan.objects.get(name="free")
        UserSubscription.objects.create(user=self.owner, plan=self.plan, is_active=True)
        for feature_key, value in FREE_PLAN_LIMITS.items():
            PlanFeatureLimit.objects.update_or_create(
                plan=self.plan, feature_key=feature_key, defaults={"value": value}
            )
        self.building = Building.objects.create(
            owner=self.owner,
            name="QuotaB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        self.unit = Unit.objects.create(
            owner=self.owner,
            building=self.building,
            unit="Q1",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        self.client_api = _auth(self.owner)

    def _renter(self, suffix: str) -> Renter:
        return Renter.objects.create(
            unit=self.unit,
            name=f"Quota Renter {suffix}",
            phone=f"+9112345679{suffix}",
            email=f"quota{suffix}@test.com",
            rent_amount=Decimal("10000"),
            start_date=date.today(),
        )

    def _upload(self, renter: Renter):
        from django.core.files.uploadedfile import SimpleUploadedFile

        return self.client_api.post(
            DRAFTS_URL,
            {
                "renter": renter.id,
                "unit": self.unit.id,
                "file": SimpleUploadedFile("draft.pdf", b"PDF content"),
            },
            format="multipart",
        )

    def test_free_plan_uploads_more_than_one_agreement(self):
        first = self._renter("01")
        second = self._renter("02")
        with patch("properties.views.unit_views.send_agreement_for_signature"):
            first_response = self._upload(first)
            second_response = self._upload(second)
        self.assertEqual(first_response.status_code, 201)
        self.assertEqual(second_response.status_code, 201)

    def test_quota_is_still_enforced_at_the_plan_limit(self):
        PlanFeatureLimit.objects.filter(
            plan=self.plan, feature_key="rent_agreement_drafts"
        ).update(value="1")
        renter = self._renter("03")
        with patch("properties.views.unit_views.send_agreement_for_signature"):
            self.assertEqual(self._upload(renter).status_code, 201)
        second = self._renter("04")
        with patch("properties.views.unit_views.send_agreement_for_signature"):
            response = self._upload(second)
        self.assertEqual(response.status_code, 403)
        self.assertIn("draft creation limit", str(response.data).lower())

    def test_paid_plan_uploads_agreements_without_a_quota_row(self):
        """A plan missing the quota row used to resolve to a limit of 0."""
        paid_plan = SubscriptionPlan.objects.create(
            name="quota_pro",
            monthly_price=Decimal("29.99"),
            yearly_price=Decimal("299.99"),
            features="Pro",
            is_active=True,
        )
        for feature_key, value in PLAN_LIMITS["pro"].items():
            PlanFeatureLimit.objects.create(
                plan=paid_plan, feature_key=feature_key, value=value
            )
        UserSubscription.objects.filter(user=self.owner).update(plan=paid_plan)
        renter = self._renter("05")
        with patch("properties.views.unit_views.send_agreement_for_signature"):
            response = self._upload(renter)
        self.assertEqual(response.status_code, 201)
