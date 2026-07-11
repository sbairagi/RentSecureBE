"""Tests for rentsecure_be/services/razorpay_service.py."""

from unittest.mock import MagicMock, patch

from django.test import TestCase

from rentsecure_be.services.razorpay_service import create_payment_link


class CreatePaymentLinkTests(TestCase):
    @patch("rentsecure_be.services.razorpay_service.client")
    def test_create_payment_link_returns_url(self, mock_client):
        mock_client.payment_link.create.return_value = {
            "short_url": "https://rzp.test/pay/abc123"
        }
        renter = MagicMock()
        renter.name = "Test Renter"
        renter.phone = "+919876543210"
        renter.email = "renter@test.com"
        rent_record = MagicMock()
        rent_record.renter = renter
        rent_record.amount = 15000
        rent_record.month = "January"
        rent_record.year = 2024

        result = create_payment_link(rent_record)
        self.assertEqual(result, "https://rzp.test/pay/abc123")
        mock_client.payment_link.create.assert_called_once()
