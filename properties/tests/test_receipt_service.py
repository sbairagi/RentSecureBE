"""Comprehensive pytest tests for properties/services/receipt_service.py."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from faker import Faker

from conftest import (
    RenterFactory,
    RentRecordFactory,
    RentRecordPaidFactory,
    UnitFactory,
)
from properties.services import receipt_service

fake = Faker()


# ===========================================================================
# generate_rent_receipt_pdf tests
# ===========================================================================


class TestGenerateRentReceiptPdf:
    """Covers the generate_rent_receipt_pdf happy path and exception path."""

    def test_generate_returns_pdf_bytes(self, db):
        rent_record = RentRecordFactory()
        html_mock = MagicMock()
        html_mock.write_pdf.return_value = b"%PDF-1.4 mock"

        with (
            patch(
                "properties.services.receipt_service.render_to_string",
                return_value="<html>receipt</html>",
            ),
            patch(
                "properties.services.receipt_service.HTML", return_value=html_mock
            ) as html_cls,
        ):
            result = receipt_service.generate_rent_receipt_pdf(rent_record)

        assert isinstance(result, bytes)
        assert result == b"%PDF-1.4 mock"
        html_cls.assert_called_once_with(string="<html>receipt</html>")
        html_mock.write_pdf.assert_called_once()

    def test_generate_re_raises_on_render_exception(self, db):
        rent_record = RentRecordFactory()
        exc = RuntimeError("weasyprint boom")

        with (
            patch(
                "properties.services.receipt_service.render_to_string",
                side_effect=exc,
            ),
            patch("properties.services.receipt_service.logger") as mock_logger,
        ):
            with pytest.raises(RuntimeError, match="weasyprint boom"):
                receipt_service.generate_rent_receipt_pdf(rent_record)

        mock_logger.exception.assert_called_once()
        call_args = mock_logger.exception.call_args
        assert "Failed to generate rent receipt PDF" in call_args[0][0]
        assert call_args[0][2] is exc

    def test_generate_re_raises_on_write_pdf_exception(self, db):
        rent_record = RentRecordFactory()
        exc = OSError("GTK missing")

        with (
            patch(
                "properties.services.receipt_service.render_to_string",
                return_value="<html>receipt</html>",
            ),
            patch("properties.services.receipt_service.HTML") as html_cls,
        ):
            html_cls.return_value.write_pdf.side_effect = exc
            with patch("properties.services.receipt_service.logger") as mock_logger:
                with pytest.raises(OSError, match="GTK missing"):
                    receipt_service.generate_rent_receipt_pdf(rent_record)

        mock_logger.exception.assert_called_once()


# ===========================================================================
# send_rent_receipt_email tests
# ===========================================================================


class TestSendRentReceiptEmail:
    """Covers the early-return branches and full happy/exception paths."""

    def test_returns_false_when_renter_is_none(self, db):
        unit = UnitFactory()

        rent_record = RentRecordFactory(
            unit=unit,
            renter=None,
            status="paid",
            payment_method="upi",
            amount=Decimal("5000"),
        )

        with patch("properties.services.receipt_service.logger") as mock_logger:
            result = receipt_service.send_rent_receipt_email(rent_record)

        assert result is False
        mock_logger.warning.assert_called_once()
        assert "Renter is None" in mock_logger.warning.call_args[0][0]

    def test_returns_false_when_renter_has_no_email(self, db):
        unit = UnitFactory()
        renter = RenterFactory(unit=unit, email="")

        rent_record = RentRecordFactory(
            unit=unit,
            renter=renter,
            status="paid",
            payment_method="upi",
            amount=Decimal("5000"),
        )

        with patch("properties.services.receipt_service.logger") as mock_logger:
            result = receipt_service.send_rent_receipt_email(rent_record)

        assert result is False
        mock_logger.warning.assert_called_once()
        assert "has no email" in mock_logger.warning.call_args[0][0]

    def test_returns_true_on_success(self, db):
        unit = UnitFactory()
        renter = RenterFactory(unit=unit)

        rent_record = RentRecordFactory(
            unit=unit,
            renter=renter,
            status="paid",
            payment_method="upi",
            amount=Decimal("15000"),
            due_date=date(2026, 6, 5),
            paid_on=date(2026, 6, 5),
        )

        pdf_bytes = b"%PDF-1.4 receipt"
        mock_email_instance = MagicMock()

        with (
            patch(
                "properties.services.receipt_service.generate_rent_receipt_pdf",
                return_value=pdf_bytes,
            ),
            patch(
                "properties.services.receipt_service.EmailMessage",
                return_value=mock_email_instance,
            ) as email_cls,
            patch("properties.services.receipt_service.logger") as mock_logger,
        ):
            result = receipt_service.send_rent_receipt_email(rent_record)

        assert result is True
        email_cls.assert_called_once()
        mock_email_instance.attach.assert_called_once()
        attach_call = mock_email_instance.attach.call_args
        assert attach_call[0][0].startswith("rent_receipt_")
        assert attach_call[0][1] == pdf_bytes
        assert attach_call[0][2] == "application/pdf"
        mock_email_instance.send.assert_called_once_with(fail_silently=False)
        mock_logger.info.assert_called_once()
        assert "Rent receipt email sent to" in mock_logger.info.call_args[0][0]

    def test_returns_false_on_send_exception(self, db):
        unit = UnitFactory()
        renter = RenterFactory(unit=unit)

        rent_record = RentRecordFactory(
            unit=unit,
            renter=renter,
            status="paid",
            payment_method="upi",
            amount=Decimal("15000"),
            due_date=date(2026, 6, 5),
            paid_on=date(2026, 6, 5),
        )

        pdf_bytes = b"%PDF-1.4 receipt"
        mock_email_instance = MagicMock()
        mock_email_instance.send.side_effect = Exception("SMTP down")

        with (
            patch(
                "properties.services.receipt_service.generate_rent_receipt_pdf",
                return_value=pdf_bytes,
            ),
            patch(
                "properties.services.receipt_service.EmailMessage",
                return_value=mock_email_instance,
            ),
            patch("properties.services.receipt_service.logger") as mock_logger,
        ):
            result = receipt_service.send_rent_receipt_email(rent_record)

        assert result is False
        mock_email_instance.send.assert_called_once_with(fail_silently=False)
        mock_logger.exception.assert_called_once()
        assert (
            "Failed to send rent receipt email" in mock_logger.exception.call_args[0][0]
        )

    def test_email_body_contains_expected_fields(self, db):
        unit = UnitFactory()
        renter = RenterFactory(unit=unit)

        rent_record = RentRecordFactory(
            unit=unit,
            renter=renter,
            status="paid",
            payment_method="upi",
            amount=Decimal("15000"),
            due_date=date(2026, 6, 5),
            paid_on=date(2026, 6, 5),
        )

        pdf_bytes = b"%PDF-1.4 receipt"
        mock_email_instance = MagicMock()
        captured_call = {}

        def fake_email_init(*args, **kwargs):
            captured_call["args"] = args
            captured_call["kwargs"] = kwargs
            return mock_email_instance

        with (
            patch(
                "properties.services.receipt_service.generate_rent_receipt_pdf",
                return_value=pdf_bytes,
            ),
            patch(
                "properties.services.receipt_service.EmailMessage",
                side_effect=fake_email_init,
            ),
        ):
            receipt_service.send_rent_receipt_email(rent_record)

        subject = captured_call["kwargs"]["subject"]
        assert "Rent Receipt" in subject
        assert "June 2026" in subject
        assert "₹15000" in subject
        body = captured_call["kwargs"]["body"]
        assert renter.name in body
        assert "Property:" in body
        assert "Amount: ₹15000" in body
        assert "Date Paid:" in body
        assert "Payment Status:" in body


# ===========================================================================
# send_rent_receipt_on_payment tests
# ===========================================================================


class TestSendRentReceiptOnPayment:
    """Covers the non-paid branch and the delegation to send_rent_receipt_email."""

    def test_returns_false_when_not_paid(self, db):
        unit = UnitFactory()
        renter = RenterFactory(unit=unit)

        rent_record = RentRecordFactory(
            unit=unit,
            renter=renter,
            status="pending",
            payment_method="upi",
            amount=Decimal("5000"),
        )

        with (
            patch("properties.services.receipt_service.logger") as mock_logger,
            patch(
                "properties.services.receipt_service.send_rent_receipt_email"
            ) as mock_send,
        ):
            result = receipt_service.send_rent_receipt_on_payment(rent_record)

        assert result is False
        mock_send.assert_not_called()
        mock_logger.debug.assert_called_once()
        assert "not marked as PAID" in mock_logger.debug.call_args[0][0]

    def test_returns_true_delegates_to_email_when_paid(self, db):
        unit = UnitFactory()
        renter = RenterFactory(unit=unit)

        rent_record = RentRecordPaidFactory(
            unit=unit,
            renter=renter,
            amount=Decimal("5000"),
        )

        with patch(
            "properties.services.receipt_service.send_rent_receipt_email",
            return_value=True,
        ) as mock_send:
            result = receipt_service.send_rent_receipt_on_payment(rent_record)

        assert result is True
        mock_send.assert_called_once_with(rent_record)

    def test_returns_false_delegates_to_email_when_email_fails(self, db):
        unit = UnitFactory()
        renter = RenterFactory(unit=unit)

        rent_record = RentRecordPaidFactory(
            unit=unit,
            renter=renter,
            amount=Decimal("5000"),
        )

        with patch(
            "properties.services.receipt_service.send_rent_receipt_email",
            return_value=False,
        ) as mock_send:
            result = receipt_service.send_rent_receipt_on_payment(rent_record)

        assert result is False
        mock_send.assert_called_once_with(rent_record)

    def test_overdue_status_skips_email(self, db):
        unit = UnitFactory()
        renter = RenterFactory(unit=unit)

        rent_record = RentRecordFactory(
            unit=unit,
            renter=renter,
            status="overdue",
            payment_method="upi",
            amount=Decimal("5000"),
        )

        with (
            patch("properties.services.receipt_service.logger") as mock_logger,
            patch(
                "properties.services.receipt_service.send_rent_receipt_email"
            ) as mock_send,
        ):
            result = receipt_service.send_rent_receipt_on_payment(rent_record)

        assert result is False
        mock_send.assert_not_called()
        mock_logger.debug.assert_called_once()
