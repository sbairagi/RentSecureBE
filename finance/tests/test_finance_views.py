"""Tests for finance/views.py — CA profile and tax submission views."""

import tempfile
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from core.models import PlanFeatureLimit, SubscriptionPlan, UserSubscription
from finance.models import CAProfile, TaxSubmissionToCA
from finance.views import (
    CAProfileViewSet,
    DownloadTaxFilesView,
    TaxSubmissionToCAViewSet,
)
from properties.models import Building, Unit

User = get_user_model()


def _jwt_request(user, method="GET", data=None, path="/test"):
    from rest_framework_simplejwt.tokens import RefreshToken

    from django.test import RequestFactory

    factory = RequestFactory()
    token = RefreshToken.for_user(user).access_token
    kwargs = {}
    if data:
        kwargs["data"] = data
    req = getattr(factory, method.lower())(
        path, HTTP_AUTHORIZATION=f"Bearer {token}", **kwargs
    )
    return req


class CAProfileViewSetTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="ca_user", password="p", full_name="CA User", phone="+1"
        )

    def test_create_ca_profile(self):
        view = CAProfileViewSet.as_view({"post": "create"})
        response = view(
            _jwt_request(
                self.user,
                method="POST",
                data={
                    "firm_name": "Test Firm",
                    "contact_email": "ca@test.com",
                    "phone": "+919999999999",
                },
            )
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(CAProfile.objects.filter(user=self.user).exists())


class TaxSubmissionToCAViewSetTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="tax_user", password="p", full_name="TaxUser", phone="+1"
        )

    def test_create_tax_submission(self):
        view = TaxSubmissionToCAViewSet.as_view({"post": "create"})
        response = view(
            _jwt_request(
                self.user,
                method="POST",
                data={
                    "financial_year": "2024-25",
                    "sent_to_email": "ca@test.com",
                    "message": "Please review",
                },
            )
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(TaxSubmissionToCA.objects.filter(user=self.user).exists())

    def test_list_own_submissions(self):
        TaxSubmissionToCA.objects.create(
            user=self.user, financial_year="2024-25", sent_to_email="ca@test.com"
        )
        view = TaxSubmissionToCAViewSet.as_view({"get": "list"})
        response = view(_jwt_request(self.user, method="GET"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)


class DownloadTaxFilesViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="dl_tax_user", password="p", full_name="DLTaxUser", phone="+1"
        )
        self.plan = SubscriptionPlan.objects.create(
            name="dl_tax_pro",
            monthly_price=Decimal("29.99"),
            yearly_price=Decimal("299.99"),
        )
        UserSubscription.objects.create(user=self.user, plan=self.plan, is_active=True)
        PlanFeatureLimit.objects.create(
            plan=self.plan, feature_key="max_buildings", value="10"
        )
        self.building = Building.objects.create(
            owner=self.user,
            name="DLB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        self.unit = Unit.objects.create(
            owner=self.user,
            building=self.building,
            unit="DL101",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )

    def test_download_tax_files_returns_zip(self):
        view = DownloadTaxFilesView.as_view()
        fd, zip_path = tempfile.mkstemp(suffix=".zip")
        import os

        os.close(fd)
        with patch("finance.views.generate_tax_excel", return_value="/tmp/test.xlsx"):
            with patch("finance.views.generate_tax_pdf", return_value="/tmp/test.pdf"):
                with patch("finance.views.create_tax_zip", return_value=zip_path):
                    response = view(
                        _jwt_request(self.user, method="GET", data={"fy": "2024-25"})
                    )
        try:
            self.assertEqual(response.status_code, 200)
        finally:
            if hasattr(response, "close"):
                response.close()
            if os.path.exists(zip_path):
                os.unlink(zip_path)
