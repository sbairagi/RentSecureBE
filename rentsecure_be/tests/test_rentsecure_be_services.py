"""Tests for rentsecure_be service utilities."""

from unittest.mock import MagicMock, patch

from django.test import TestCase

from notification.services.i18n_service import translate_msg
from rentsecure_be.services.razorpay_service import create_payment_link
from rentsecure_be.utils.cashfree_payout import (
    add_beneficiary,
    get_auth_token,
    make_payout,
)


class TranslateMsgTest(TestCase):
    def test_translate_english_returns_original(self):
        self.assertEqual(translate_msg("Hello", "en"), "Hello")

    def test_translate_non_english_success(self):
        with patch(
            "notification.services.i18n_service.GoogleTranslator"
        ) as mock_translator:
            instance = MagicMock()
            instance.translate.return_value = "Hola"
            mock_translator.return_value = instance
            result = translate_msg("Hello", "es")
            self.assertEqual(result, "Hola")
            instance.translate.assert_called_once_with("Hello")

    def test_translate_non_english_failure_returns_original(self):
        with patch(
            "notification.services.i18n_service.GoogleTranslator",
            side_effect=RuntimeError("API down"),
        ):
            result = translate_msg("Hello", "fr")
            self.assertEqual(result, "Hello")

    def test_translate_returns_original_when_translated_is_none(self):
        with patch(
            "notification.services.i18n_service.GoogleTranslator"
        ) as mock_translator:
            instance = MagicMock()
            instance.translate.return_value = None
            mock_translator.return_value = instance
            result = translate_msg("Hello", "es")
            self.assertEqual(result, "Hello")


class CreatePaymentLinkTest(TestCase):
    def test_create_payment_link_returns_short_url(self):
        mock_rent = MagicMock()
        mock_rent.amount = 1500
        mock_rent.month = "January"
        mock_rent.year = 2024
        mock_renter = MagicMock()
        mock_renter.name = "Test Renter"
        mock_renter.phone = "+919999999999"
        mock_renter.email = "renter@test.com"
        mock_rent.renter = mock_renter

        with patch("rentsecure_be.services.razorpay_service.client") as mock_client:
            mock_client.payment_link.create.return_value = {
                "short_url": "https://rzp.io/test"
            }
            result = create_payment_link(mock_rent)
            self.assertEqual(result, "https://rzp.io/test")
            mock_client.payment_link.create.assert_called_once()

    def test_create_payment_link_amount_in_paise(self):
        mock_rent = MagicMock()
        mock_rent.amount = 1500
        mock_rent.month = "January"
        mock_rent.year = 2024
        mock_renter = MagicMock()
        mock_renter.name = "Test Renter"
        mock_renter.phone = "+919999999999"
        mock_renter.email = "renter@test.com"
        mock_rent.renter = mock_renter

        with patch("rentsecure_be.services.razorpay_service.client") as mock_client:
            mock_client.payment_link.create.return_value = {
                "short_url": "https://rzp.io/test"
            }
            create_payment_link(mock_rent)
            call_args = mock_client.payment_link.create.call_args[0][0]
            self.assertEqual(call_args["amount"], 150000)


class GetAuthTokenTest(TestCase):
    def test_get_auth_token_success(self):
        with patch("rentsecure_be.utils.cashfree_payout.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {"data": {"token": "test-token-123"}}
            mock_post.return_value = mock_response
            result = get_auth_token()
            self.assertEqual(result, "test-token-123")

    def test_get_auth_token_missing_data_returns_none(self):
        with patch("rentsecure_be.utils.cashfree_payout.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {}
            mock_post.return_value = mock_response
            result = get_auth_token()
            self.assertIsNone(result)

    def test_get_auth_token_missing_token_returns_none(self):
        with patch("rentsecure_be.utils.cashfree_payout.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {"data": {}}
            mock_post.return_value = mock_response
            result = get_auth_token()
            self.assertIsNone(result)


class AddBeneficiaryTest(TestCase):
    def test_add_beneficiary_returns_json(self):
        with patch("rentsecure_be.utils.cashfree_payout.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {"status": "SUCCESS"}
            mock_post.return_value = mock_response
            with patch(
                "rentsecure_be.utils.cashfree_payout.get_auth_token",
                return_value="token",
            ):
                result = add_beneficiary({"beneId": "test"})
                self.assertEqual(result, {"status": "SUCCESS"})
                self.assertEqual(mock_post.call_count, 1)


class MakePayoutTest(TestCase):
    def test_make_payout_returns_json(self):
        with patch("rentsecure_be.utils.cashfree_payout.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {"status": "SUCCESS"}
            mock_post.return_value = mock_response
            with patch(
                "rentsecure_be.utils.cashfree_payout.get_auth_token",
                return_value="token",
            ):
                result = make_payout(
                    transfer_id="txn_1",
                    amount=1000.0,
                    remarks="test",
                    bene_id="bene_1",
                )
                self.assertEqual(result, {"status": "SUCCESS"})
                payload = mock_post.call_args[1]["json"]
                self.assertEqual(payload["beneId"], "bene_1")
                self.assertEqual(payload["amount"], "1000.0")
