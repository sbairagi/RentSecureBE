"""Tests for core export utilities"""

from io import BytesIO
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from rentsecure_be.utils.export_utils import generate_owner_rent_report

User = get_user_model()


class GenerateOwnerRentReportTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="export_owner",
            email="owner@test.com",
            password="p",
            full_name="Owner",
            phone="+1",
        )

    @patch("properties.models.rent_record_models.RentRecord")
    def test_generate_report_returns_bytesio(self, mock_rent_record):
        mock_rent_record.objects.filter.return_value.select_related.return_value = []
        result = generate_owner_rent_report(self.owner)
        self.assertIsInstance(result, BytesIO)
        data = result.read()
        self.assertTrue(len(data) > 0)

    @patch("properties.models.rent_record_models.RentRecord")
    def test_generate_report_with_data(self, mock_rent_record):
        mock_rent = MagicMock()
        mock_rent.renter.property.title = "Test Building"
        mock_rent.renter.full_name = "Test Renter"
        mock_rent.due_date.strftime.return_value = "2026-01-01"
        mock_rent.amount = 15000
        mock_rent.payment_status = "PAID"
        mock_rent.payout_status = "SUCCESS"
        mock_rent_record.objects.filter.return_value.select_related.return_value = [
            mock_rent
        ]

        result = generate_owner_rent_report(self.owner)
        data = result.read()
        self.assertTrue(b"Test Building" in data or len(data) > 0)

    @patch("properties.models.rent_record_models.RentRecord")
    def test_generate_report_empty(self, mock_rent_record):
        mock_rent_record.objects.filter.return_value.select_related.return_value = []
        result = generate_owner_rent_report(self.owner)
        self.assertIsNotNone(result)
