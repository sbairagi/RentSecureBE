"""Tests for finance views."""

import tempfile
from decimal import Decimal
from unittest.mock import MagicMock, patch

from rest_framework.test import APIRequestFactory, force_authenticate

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


class CAProfileViewSetTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            username="ca_user",
            email="ca@test.com",
            password="p",
            full_name="CA User",
            phone="+1",
        )

    def _make_request(self, method, data=None, user=None):
        request = getattr(self.factory, method)(
            "/api/finance/ca-profiles/", data=data or {}
        )
        if user is not None:
            force_authenticate(request, user=user)
        return request

    def test_list_ca_profiles(self):
        request = self._make_request("get", user=self.user)
        view = CAProfileViewSet.as_view({"get": "list"})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)

    def test_create_ca_profile(self):
        data = {
            "user": self.user.id,
            "firm_name": "Test Firm",
            "contact_email": "ca@firm.com",
            "phone": "+919999999999",
        }
        request = self._make_request("post", data=data, user=self.user)
        view = CAProfileViewSet.as_view({"post": "create"})
        response = view(request)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["firm_name"], "Test Firm")


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


class TaxSubmissionToCAViewSetTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            username="tax_user",
            email="tax@test.com",
            password="p",
            full_name="Tax User",
            phone="+1",
        )

    def _make_request(self, method, data=None, user=None):
        request = getattr(self.factory, method)(
            "/api/finance/tax-submissions/", data=data or {}
        )
        if user is not None:
            force_authenticate(request, user=user)
        return request

    def test_list_own_submissions(self):
        request = self._make_request("get", user=self.user)
        view = TaxSubmissionToCAViewSet.as_view({"get": "list"})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)

    def test_create_tax_submission(self):
        data = {
            "user": self.user.id,
            "financial_year": "2024-25",
            "sent_to_email": "ca@firm.com",
        }
        request = self._make_request("post", data=data, user=self.user)
        view = TaxSubmissionToCAViewSet.as_view({"post": "create"})
        response = view(request)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["financial_year"], "2024-25")


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


class DownloadTaxFilesViewTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            username="dl_user",
            email="dl@test.com",
            password="p",
            full_name="DL User",
            phone="+1",
        )

    @patch("finance.views.create_tax_zip")
    @patch("finance.views.generate_tax_pdf")
    @patch("finance.views.generate_tax_excel")
    def test_download_tax_files_success(self, mock_excel, mock_pdf, mock_zip):
        mock_excel.return_value = "/tmp/tax.xlsx"
        mock_pdf.return_value = "/tmp/tax.pdf"
        mock_zip.return_value = "/tmp/tax.zip"
        request = self.factory.get("/api/finance/download-tax-files/")
        force_authenticate(request, user=self.user)
        with patch("builtins.open", MagicMock()):
            view = DownloadTaxFilesView.as_view()
            response = view(request)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response["Content-Type"], "application/zip")
