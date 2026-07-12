"""Comprehensive tests for smartbot/actions.py to raise coverage to at least 95%."""

from __future__ import annotations

import os
import tempfile
from unittest.mock import MagicMock, patch

from django.test import TestCase

from conftest import RenterFactory, RentRecordFactory  # noqa: E402
from smartbot.actions import (
    retry_payout,
    send_agreement_for_signature,
    send_rent_agreement,
    send_rent_reminder,
)


class SendRentReminderTests(TestCase):
    """Tests covering send_rent_reminder success and failure branches."""

    def setUp(self):
        self.renter = RenterFactory()

    def test_sends_reminder_and_returns_success(self):
        with patch("smartbot.actions.send_whatsapp_message") as mock_whatsapp:
            result = send_rent_reminder(self.renter.name)
        mock_whatsapp.assert_called_once()
        self.assertIn("✅", result)
        self.assertIn(self.renter.name, result)

    def test_renter_not_found_returns_error(self):
        result = send_rent_reminder("nonexistent person 12345zzz")
        self.assertEqual(result, "❌ Renter not found.")


class RetryPayoutTests(TestCase):
    """Tests covering retry_payout success and failure branches."""

    def setUp(self):
        self.rent_record = RentRecordFactory(status="pending")

    @patch("smartbot.actions.process_rent_payout")
    def test_retry_payout_success(self, mock_process):
        mock_process.return_value = {"status": "SUCCESS"}
        result = retry_payout(self.rent_record.renter.name)
        mock_process.assert_called_once_with(self.rent_record)
        self.assertIn("✅", result)
        self.assertIn("SUCCESS", result)

    def test_retry_payout_renter_not_found_returns_error(self):
        result = retry_payout("nonexistent person 12345zzz")
        self.assertEqual(result, "❌ Could not retry payout.")


class SendRentAgreementTests(TestCase):
    """Tests covering send_rent_agreement success and OSError branches."""

    def setUp(self):
        self.renter = RenterFactory()
        self.rent_record = RentRecordFactory(renter=self.renter)

    @patch("smartbot.actions.send_agreement_via_whatsapp")
    def test_sends_agreement_and_returns_success(self, mock_whatsapp):
        with patch("smartbot.actions.generate_agreement_pdf") as mock_gen_pdf:
            tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
            tmp.close()
            mock_gen_pdf.return_value = tmp.name

            _default_storage = __import__(
                "django.core.files.storage", fromlist=["default_storage"]
            ).default_storage

            with (
                patch.object(_default_storage.__class__, "save", return_value=None),
                patch.object(
                    _default_storage.__class__,
                    "url",
                    return_value="https://stor.test/a.pdf",
                ),
            ):
                result = send_rent_agreement(self.renter.name)

            os.unlink(tmp.name)

        mock_gen_pdf.assert_called_once_with(self.rent_record)
        mock_whatsapp.assert_called_once()
        self.assertIn("✅", result)
        self.assertIn(self.renter.name, result)

    def test_renter_not_found_returns_error(self):
        result = send_rent_agreement("nonexistent person 12345zzz")
        self.assertIn("❌", result)
        self.assertIn("Failed to send agreement", result)

    @patch("smartbot.actions.generate_agreement_pdf", side_effect=OSError("disk error"))
    def test_disk_io_error_returns_failure(self, mock_gen_pdf):
        result = send_rent_agreement(self.renter.name)
        self.assertIn("❌", result)
        self.assertIn("Failed to send agreement", result)

    def test_agreement_with_no_records_returns_error(self):
        new_renter = RenterFactory()
        result = send_rent_agreement(new_renter.name)
        self.assertIn("❌", result)
        self.assertIn("Failed to send agreement", result)


class SendAgreementForSignatureTests(TestCase):
    """Tests covering all uncovered branches in send_agreement_for_signature.

    actions.py does:
        from .services.leegality_service import initiate_signature
    So the patch target for initiate_signature MUST be `smartbot.actions.initiate_signature`.

    Uncovered branches:
      - lines 77-81 (cover line 80 inner if): draft is not None, document_id not None
      - line 83: result.get("status") != "success"
    Additional branches we also cover:
      - draft is not None, document_id is None  (save block skipped)
      - draft is None                           (filter branch)
    """

    def setUp(self):
        self.renter = RenterFactory()
        self.rent_record = RentRecordFactory(renter=self.renter)

    # ------------------------------------------------------------------
    # draft is not None AND document_id is not None → lines 77-81
    # ------------------------------------------------------------------
    @patch("smartbot.actions.initiate_signature")
    def test_success_draft_exists_saves_document_id(self, mock_init_sig):
        with patch("smartbot.actions.generate_agreement_pdf") as mock_gen_pdf:
            tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
            tmp.close()
            mock_gen_pdf.return_value = tmp.name

            _rent_agreement_draft = __import__(
                "properties.models", fromlist=["RentAgreementDraft"]
            ).RentAgreementDraft

            mock_draft_obj = MagicMock(spec=_rent_agreement_draft)
            mock_draft_obj.leegality_document_id = ""

            with patch(
                "properties.models.RentAgreementDraft",
                autospec=True,
            ) as mock_draft_cls:
                mock_draft_cls.objects.filter.return_value.first.return_value = (
                    mock_draft_obj
                )
                mock_init_sig.return_value = {
                    "status": "success",
                    "documentId": "lee-doc-123",
                }

                result = send_agreement_for_signature(self.renter.name)

            mock_gen_pdf.assert_called_once_with(self.rent_record)
            mock_init_sig.assert_called_once()
            self.assertEqual(mock_draft_obj.leegality_document_id, "lee-doc-123")
            mock_draft_obj.save.assert_called_once_with(
                update_fields=["leegality_document_id"]
            )

        self.assertIn("📨 Signature request sent", result)
        self.assertIn(self.renter.name, result)

        os.unlink(tmp.name)

    # ------------------------------------------------------------------
    # draft is None → line 77 false branch
    # ------------------------------------------------------------------
    @patch("smartbot.actions.initiate_signature")
    def test_success_no_draft_returns_message(self, mock_init_sig):
        with patch("smartbot.actions.generate_agreement_pdf") as mock_gen_pdf:
            tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
            tmp.close()
            mock_gen_pdf.return_value = tmp.name

            with patch(
                "properties.models.RentAgreementDraft",
                autospec=True,
            ) as mock_draft_cls:
                mock_draft_cls.objects.filter.return_value.first.return_value = None
                mock_init_sig.return_value = {"status": "success"}

                result = send_agreement_for_signature(self.renter.name)

            mock_draft_cls.objects.filter.assert_called_once_with(renter=self.renter)

        mock_gen_pdf.assert_called_once_with(self.rent_record)
        self.assertIn("📨 Signature request sent", result)
        self.assertIn(self.renter.name, result)

        os.unlink(tmp.name)

    # ------------------------------------------------------------------
    # draft is not None but result has no documentId → line 79 false branch
    # ------------------------------------------------------------------
    @patch("smartbot.actions.initiate_signature")
    def test_success_draft_exists_but_no_document_id_no_save(self, mock_init_sig):
        with patch("smartbot.actions.generate_agreement_pdf") as mock_gen_pdf:
            tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
            tmp.close()
            mock_gen_pdf.return_value = tmp.name

            _rent_agreement_draft = __import__(
                "properties.models", fromlist=["RentAgreementDraft"]
            ).RentAgreementDraft

            mock_draft_obj = MagicMock(spec=_rent_agreement_draft)
            mock_draft_obj.leegality_document_id = ""

            with patch(
                "properties.models.RentAgreementDraft",
                autospec=True,
            ) as mock_draft_cls:
                mock_draft_cls.objects.filter.return_value.first.return_value = (
                    mock_draft_obj
                )
                mock_init_sig.return_value = {"status": "success"}  # no documentId

                result = send_agreement_for_signature(self.renter.name)

            mock_gen_pdf.assert_called_once_with(self.rent_record)
            mock_init_sig.assert_called_once()
            mock_draft_obj.save.assert_not_called()

        self.assertIn("📨 Signature request sent", result)
        self.assertIn(self.renter.name, result)

        os.unlink(tmp.name)

    # ------------------------------------------------------------------
    # result.get("status") != "success" → line 83 uncovered branch
    # ------------------------------------------------------------------
    @patch("smartbot.actions.generate_agreement_pdf")
    def test_non_success_status_returns_error_message(self, mock_gen_pdf):
        tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        tmp.close()
        mock_gen_pdf.return_value = tmp.name

        with patch(
            "smartbot.actions.initiate_signature",
            return_value={"status": "FAILED", "error": "provider down"},
        ):
            result = send_agreement_for_signature(self.renter.name)

        self.assertIn("❌ Error:", result)
        self.assertIn("FAILED", result)

        os.unlink(tmp.name)

    # ------------------------------------------------------------------
    # Failure branch: Renter.DoesNotExist at line 59
    # ------------------------------------------------------------------
    def test_renter_not_found_returns_signature_error(self):
        from properties.models import Renter

        with patch(
            "smartbot.actions.Renter.objects.get",
            side_effect=Renter.DoesNotExist("not found"),
        ):
            result = send_agreement_for_signature("nonexistent person 12345zzz")
        self.assertIn("❌ Signature flow failed", result)

    # ------------------------------------------------------------------
    # Failure branch: OSError from generate_agreement_pdf
    # ------------------------------------------------------------------
    @patch("smartbot.actions.generate_agreement_pdf", side_effect=OSError("IO fail"))
    def test_generate_pdf_oserror_returns_failure(self, mock_gen_pdf):
        result = send_agreement_for_signature(self.renter.name)
        self.assertIn("❌ Signature flow failed", result)
        self.assertIn("IO fail", result)

    # ------------------------------------------------------------------
    # Failure branch: ValueError from initiate_signature
    # ------------------------------------------------------------------
    @patch("smartbot.actions.generate_agreement_pdf")
    def test_initiate_signature_valueerror_returns_failure(self, mock_gen_pdf):
        tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        tmp.close()
        mock_gen_pdf.return_value = tmp.name

        with patch(
            "smartbot.actions.initiate_signature",
            side_effect=ValueError("bad payload"),
        ):
            result = send_agreement_for_signature(self.renter.name)

        self.assertIn("❌ Signature flow failed", result)
        self.assertIn("bad payload", result)

        os.unlink(tmp.name)
