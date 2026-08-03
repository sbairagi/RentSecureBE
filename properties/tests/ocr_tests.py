"""Tests for Form 16 / rent receipt OCR extraction API."""

from unittest.mock import patch

from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import get_user_model
from django.test import TestCase

from core.models import SubscriptionPlan, UserSubscription
from properties.models import Building, Unit

User = get_user_model()


class ExtractForm16Tests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.o = User.objects.create_user(
            username="ocr_user@t.com",
            email="ocr_user@t.com",
            password="p",
            full_name="OCRUser",
            phone="+1",
        )
        cls.pp, _ = SubscriptionPlan.objects.get_or_create(
            name="ocr_pro",
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
            name="OCRB",
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
            unit="OCR101",
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

    def _make_pdf_file(self, filename: str = "form16.pdf"):
        from django.core.files.uploadedfile import SimpleUploadedFile

        return SimpleUploadedFile(
            filename, b"fake pdf content", content_type="application/pdf"
        )

    @patch("properties.services.ocr_service.extract_pdf_text")
    def test_extract_form16_returns_extracted_data(self, mock_extract_text):
        mock_extract_text.return_value = (
            "Employee Name: Test User\n"
            "PAN: ABCDE1234F\n"
            "Gross Salary: 1200000\n"
            "HRA: 180000\n"
            "Rent Paid: 250000\n"
        )
        response = self._auth().post(
            "/properties/itr/extract-form16/",
            {"file": self._make_pdf_file()},
            format="multipart",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["pan"], "ABCDE1234F")
        self.assertEqual(data["salary"], 1200000.0)
        self.assertEqual(data["hra_received"], 180000.0)
        self.assertEqual(data["rent_paid"], 250000.0)
        self.assertIn("raw_text", data)

    def test_extract_form16_requires_file(self):
        response = self._auth().post(
            "/properties/itr/extract-form16/",
            {},
            format="multipart",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("file", response.json().get("error", "").lower())

    def test_extract_form16_requires_authentication(self):
        response = self.client.post(
            "/properties/itr/extract-form16/",
            {"file": self._make_pdf_file()},
            format="multipart",
        )
        self.assertEqual(response.status_code, 401)
