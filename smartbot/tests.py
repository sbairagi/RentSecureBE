"""Tests for smartbot app actions and services"""

from unittest.mock import MagicMock, mock_open, patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from smartbot.actions import (
    retry_payout,
    send_agreement_for_signature,
    send_rent_agreement,
    send_rent_reminder,
)
from smartbot.services.agreement_service import generate_agreement_pdf
from smartbot.services.leegality_service import initiate_signature
from smartbot.whatsapp_service import send_agreement_via_whatsapp

User = get_user_model()


class SmartBotActionsTest(TestCase):
    @patch("smartbot.actions.Renter")
    def test_send_rent_reminder_found(self, mock_renter):
        mock_renter_instance = MagicMock()
        mock_renter_instance.rent_amount = 15000
        mock_renter_instance.name = "Test Renter"
        mock_renter_instance.phone = "+911234567890"
        mock_renter_instance.property.name = "Test Building"
        mock_renter.objects.get.return_value = mock_renter_instance
        result = send_rent_reminder("Test")
        self.assertIn("✅", result)

    @patch("smartbot.actions.Renter")
    def test_send_rent_reminder_not_found(self, mock_renter):
        mock_renter.DoesNotExist = Exception
        mock_renter.objects.get.side_effect = mock_renter.DoesNotExist
        result = send_rent_reminder("Nonexistent")
        self.assertIn("❌", result)

    @patch("smartbot.actions.RentRecord")
    @patch("smartbot.actions.process_rent_payout")
    def test_retry_payout_success(self, mock_process, mock_rent_record):
        mock_rent = MagicMock()
        mock_rent_record.objects.filter.return_value.latest.return_value = mock_rent
        mock_process.return_value = {"status": "SUCCESS"}
        result = retry_payout("Test Renter")
        self.assertIn("✅", result)

    @patch("smartbot.actions.RentRecord")
    def test_retry_payout_failure(self, mock_rent_record):
        mock_rent_record.DoesNotExist = Exception
        mock_rent_record.objects.filter.side_effect = Exception("DB Error")
        result = retry_payout("Test Renter")
        self.assertIn("❌", result)

    @patch("smartbot.actions.Renter")
    @patch("smartbot.actions.RentRecord")
    @patch("smartbot.actions.generate_agreement_pdf")
    @patch("smartbot.actions.send_agreement_via_whatsapp")
    def test_send_rent_agreement(
        self, mock_send, mock_gen_pdf, mock_rent_record, mock_renter
    ):
        mock_renter_instance = MagicMock()
        mock_renter_instance.name = "Test Renter"
        mock_renter.objects.get.return_value = mock_renter_instance
        mock_rent = MagicMock()
        mock_rent.id = 1
        mock_rent_record.objects.filter.return_value.latest.return_value = mock_rent
        mock_gen_pdf.return_value = "/tmp/agreement.pdf"
        with (
            patch("smartbot.actions.default_storage"),
            patch("builtins.open", mock_open(read_data=b"pdf")),
        ):
            result = send_rent_agreement("Test")
            self.assertIn("✅", result)

    @patch("smartbot.actions.Renter")
    def test_send_rent_agreement_failure(self, mock_renter):
        mock_renter.DoesNotExist = Exception
        mock_renter.objects.get.side_effect = Exception("Error")
        result = send_rent_agreement("Test")
        self.assertIn("❌", result)

    @patch("properties.models.RentAgreementDraft")
    @patch("smartbot.actions.Renter")
    @patch("smartbot.actions.RentRecord")
    @patch("smartbot.actions.generate_agreement_pdf")
    @patch("smartbot.actions.initiate_signature")
    def test_send_agreement_for_signature_success(
        self, mock_initiate, mock_gen_pdf, mock_rent_record, mock_renter, mock_draft
    ):
        mock_renter_instance = MagicMock()
        mock_renter_instance.name = "Test Renter"
        mock_renter.objects.get.return_value = mock_renter_instance
        mock_rent = MagicMock()
        mock_rent.id = 1
        mock_rent_record.objects.filter.return_value.latest.return_value = mock_rent
        mock_gen_pdf.return_value = "/tmp/agreement.pdf"
        mock_initiate.return_value = {"status": "success", "documentId": "doc123"}
        mock_draft.objects.filter.return_value.first.return_value = None
        result = send_agreement_for_signature("Test")
        self.assertIn("📨", result)

    @patch("smartbot.actions.Renter")
    def test_send_agreement_for_signature_failure(self, mock_renter):
        mock_renter.DoesNotExist = Exception
        mock_renter.objects.get.side_effect = Exception("Error")
        result = send_agreement_for_signature("Test")
        self.assertIn("❌", result)


class SmartBotWhatsAppServiceTest(TestCase):
    @patch("smartbot.whatsapp_service.send_whatsapp_message")
    def test_send_agreement_via_whatsapp(self, mock_send):
        renter = MagicMock()
        renter.phone = "+911234567890"
        send_agreement_via_whatsapp(renter, "https://example.com/agreement.pdf")
        mock_send.assert_called_once()


class SmartBotAgreementServiceTest(TestCase):
    @patch("smartbot.services.agreement_service.render_to_string")
    @patch("weasyprint.HTML")
    def test_generate_agreement_pdf(self, mock_html, mock_render):
        mock_render.return_value = "<html></html>"
        mock_html_instance = MagicMock()
        mock_html.return_value = mock_html_instance
        rent_record = MagicMock()
        rent_record.id = 1
        result = generate_agreement_pdf(rent_record)
        self.assertIn(f"rent_agreement_{rent_record.id}_", result)
        self.assertTrue(result.endswith(".pdf"))


class SmartBotLeegalityServiceTest(TestCase):
    @patch("smartbot.services.leegality_service.requests")
    def test_initiate_signature(self, mock_requests):
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "success"}
        mock_requests.post.return_value = mock_response
        renter = MagicMock()
        renter.name = "Test"
        renter.email = "test@test.com"
        renter.phone = "+911234567890"
        with patch("builtins.open", MagicMock()):
            result = initiate_signature(renter, "/tmp/agreement.pdf")
            self.assertEqual(result, {"status": "success"})
