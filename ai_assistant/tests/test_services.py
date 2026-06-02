"""Tests for ai_assistant services"""

from datetime import date, datetime
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from ai_assistant.services.archive_service import _serialize_value, archive_renter_data
from ai_assistant.services.finance_ai import analyze_financial_health
from ai_assistant.services.i18n_service import translate_msg
from ai_assistant.services.invoice_service import generate_final_invoice_pdf
from ai_assistant.services.unit_service import update_unit_status

User = get_user_model()


class SerializeValueTest(TestCase):
    def test_serialize_date(self):
        result = _serialize_value(date(2026, 1, 1))
        self.assertEqual(result, "2026-01-01")

    def test_serialize_datetime(self):
        result = _serialize_value(datetime(2026, 1, 1, 10, 30, 0))
        self.assertEqual(result, "2026-01-01T10:30:00")

    def test_serialize_none(self):
        self.assertIsNone(_serialize_value(None))

    def test_serialize_string(self):
        self.assertEqual(_serialize_value("hello"), "hello")

    def test_serialize_int(self):
        self.assertEqual(_serialize_value(42), 42)

    def test_serialize_dict(self):
        result = _serialize_value({"key": date(2026, 1, 1)})
        self.assertEqual(result, {"key": "2026-01-01"})

    def test_serialize_list(self):
        result = _serialize_value([date(2026, 1, 1)])
        self.assertEqual(result, ["2026-01-01"])


class ArchiveRenterDataTest(TestCase):
    @patch("ai_assistant.services.archive_service.ArchivedRenter")
    @patch("ai_assistant.services.archive_service.RentRecord")
    @patch("ai_assistant.services.archive_service.UnitImage")
    @patch("ai_assistant.services.archive_service.model_to_dict")
    def test_archive_renter_data(
        self, mock_model_to_dict, mock_unit_image, mock_rent_record, mock_archived
    ):
        mock_renter = MagicMock()
        mock_renter.renter_image = None
        mock_renter.id_proof = None
        mock_renter.rent_agreement = None
        mock_renter.rent_agreement_pdf = None
        mock_renter.police_verification_pdf = None
        mock_renter.final_invoice_path = None
        mock_model_to_dict.return_value = {"name": "Test"}
        mock_rent_record.objects.filter.return_value.values.return_value = []
        mock_unit_image.objects.filter.return_value.values_list.return_value = []
        archive_renter_data(mock_renter)
        mock_archived.objects.create.assert_called_once()


class FinanceAITest(TestCase):
    def test_analyze_financial_health_empty(self):
        result = analyze_financial_health([], [])
        self.assertEqual(result["rent_score"], 0)
        self.assertEqual(result["tax_score"], 0)
        self.assertEqual(result["overall_score"], 0)

    def test_analyze_financial_health_all_on_time(self):
        rent1 = MagicMock(is_late=False)
        rent2 = MagicMock(is_late=False)
        tax1 = MagicMock(status="PAID")
        tax2 = MagicMock(status="PAID")
        result = analyze_financial_health([rent1, rent2], [tax1, tax2])
        self.assertEqual(result["rent_score"], 100)
        self.assertEqual(result["tax_score"], 100)
        self.assertEqual(result["overall_score"], 100)

    def test_analyze_financial_health_mixed(self):
        rent1 = MagicMock(is_late=False)
        rent2 = MagicMock(is_late=True)
        tax1 = MagicMock(status="PAID")
        tax2 = MagicMock(status="UNPAID")
        result = analyze_financial_health([rent1, rent2], [tax1, tax2])
        self.assertEqual(result["rent_score"], 50)
        self.assertEqual(result["tax_score"], 50)

    def test_analyze_financial_health_low_scores(self):
        rent1 = MagicMock(is_late=True)
        rent2 = MagicMock(is_late=True)
        tax1 = MagicMock(status="UNPAID")
        result = analyze_financial_health([rent1, rent2], [tax1])
        self.assertIn("suggestions", result)
        self.assertEqual(len(result["suggestions"]), 2)


class I18nServiceTest(TestCase):
    def test_translate_msg_english(self):
        result = translate_msg("Hello", "en")
        self.assertEqual(result, "Hello")

    @patch("ai_assistant.services.i18n_service.GoogleTranslator")
    def test_translate_msg_other_language(self, mock_translator):
        mock_instance = MagicMock()
        mock_instance.translate.return_value = "नमस्ते"
        mock_translator.return_value = mock_instance
        result = translate_msg("Hello", "hi")
        self.assertEqual(result, "नमस्ते")

    @patch("ai_assistant.services.i18n_service.GoogleTranslator")
    def test_translate_msg_failure(self, mock_translator):
        mock_instance = MagicMock()
        mock_instance.translate.side_effect = Exception("API Error")
        mock_translator.return_value = mock_instance
        result = translate_msg("Hello", "hi")
        self.assertEqual(result, "Hello")  # fallback


class InvoiceServiceTest(TestCase):
    @patch("ai_assistant.services.invoice_service.render_to_string")
    @patch("ai_assistant.services.invoice_service.HTML")
    def test_generate_final_invoice_pdf(self, mock_html, mock_render):
        mock_render.return_value = "<html></html>"
        mock_html_instance = MagicMock()
        mock_html.return_value = mock_html_instance
        mock_renter = MagicMock()
        mock_renter.unit.building = MagicMock()
        mock_renter.updated_at.date.return_value = date(2026, 1, 1)
        result = generate_final_invoice_pdf(mock_renter, MagicMock())
        self.assertTrue(result.endswith(".pdf"))


class UnitServiceAITest(TestCase):
    @patch("ai_assistant.services.unit_service.Renter")
    def test_update_unit_status_occupied(self, mock_renter):
        mock_renter.objects.filter.return_value.first.return_value = MagicMock()
        mock_unit = MagicMock()
        update_unit_status(mock_unit)
        self.assertEqual(mock_unit.status, "occupied")
        mock_unit.save.assert_called_once()

    @patch("ai_assistant.services.unit_service.Renter")
    def test_update_unit_status_vacant(self, mock_renter):
        mock_renter.objects.filter.return_value.first.return_value = None
        mock_unit = MagicMock()
        update_unit_status(mock_unit)
        self.assertEqual(mock_unit.status, "vacant")
        mock_unit.save.assert_called_once()
