"""Tests for finance views."""

from unittest.mock import MagicMock, patch

from rest_framework.test import APIRequestFactory, force_authenticate

from django.contrib.auth import get_user_model
from django.test import TestCase

from finance.views import (
    CAProfileViewSet,
    DownloadTaxFilesView,
    TaxSubmissionToCAViewSet,
)

User = get_user_model()


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
