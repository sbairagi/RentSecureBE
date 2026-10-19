"""Tests for the shared rent receipt presentation model."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from conftest import (
    RenterFactory,
    RentRecordFactory,
    RentRecordPaidFactory,
    UnitFactory,
)
from documents.receipt import (
    build_receipt,
    format_date,
    format_inr,
    format_period,
    group_indian,
    receipt_filename,
)

pytestmark = pytest.mark.django_db


class TestFormatting:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (0, "0"),
            (999, "999"),
            (28000, "28,000"),
            (100000, "1,00,000"),
            (123456, "1,23,456"),
            (12345678, "1,23,45,678"),
        ],
    )
    def test_group_indian(self, value: int, expected: str) -> None:
        assert group_indian(value) == expected

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (Decimal("28000"), "₹28,000"),
            (Decimal("28000.75"), "₹28,001"),
            (None, "₹0"),
        ],
    )
    def test_format_inr(self, value: Decimal | None, expected: str) -> None:
        assert format_inr(value) == expected

    def test_format_date(self) -> None:
        assert format_date(date(2026, 10, 4)) == "04 Oct 2026"
        assert format_date(None) == "—"

    def test_format_period(self) -> None:
        assert format_period(date(2026, 10, 4)) == "October 2026"
        assert format_period(None) == "—"


class TestReceiptFilename:
    def test_uses_record_id_and_due_month(self, unit: UnitFactory) -> None:
        rent_record = RentRecordPaidFactory(unit=unit, due_date=date(2026, 10, 4))
        assert receipt_filename(rent_record) == (
            f"rent_receipt_{rent_record.id}_202610.pdf"
        )


class TestBuildReceipt:
    def test_paid_record(self, unit: UnitFactory) -> None:
        renter = RenterFactory(unit=unit, name="Riya Kapoor")
        rent_record = RentRecordPaidFactory(
            unit=unit,
            renter=renter,
            amount=Decimal("28000"),
            due_date=date(2026, 10, 4),
            paid_on=date(2026, 10, 3),
            payment_method="online",
        )

        receipt = build_receipt(rent_record)

        assert receipt.payee == "Riya Kapoor"
        assert receipt.property == " · ".join(
            part for part in (unit.building_name, unit.unit) if part
        )
        assert receipt.period == "October 2026"
        assert receipt.due_date == "04 Oct 2026"
        assert receipt.paid_on == "03 Oct 2026"
        assert receipt.payment_method == "Online payment"
        assert receipt.dues_amount == "₹28,000"
        assert receipt.paid_amount == "₹28,000"
        assert receipt.net_balance == "—"
        assert receipt.total_amount == "₹28,000"
        assert receipt.status_label == "Paid"
        assert receipt.status_tone == "paid"
        assert receipt.filename == f"rent_receipt_{rent_record.id}_202610.pdf"
        assert receipt.receipt_no == receipt.filename

    def test_property_joins_building_and_unit(self, unit: UnitFactory) -> None:
        unit.building_name = "Lakeview Residency"
        unit.save(update_fields=["building_name"])
        rent_record = RentRecordPaidFactory(unit=unit)

        receipt = build_receipt(rent_record)

        assert receipt.property == f"Lakeview Residency · {unit.unit}"

    def test_pending_record_shows_outstanding_balance(self, unit: UnitFactory) -> None:
        rent_record = RentRecordFactory(
            unit=unit,
            amount=Decimal("28000"),
            status="pending",
            paid_on=None,
        )

        receipt = build_receipt(rent_record)

        assert receipt.paid_amount == "₹0"
        assert receipt.total_amount == "₹0"
        assert receipt.net_balance == "₹28,000"
        assert receipt.status_label == "Pending"
        assert receipt.status_tone == "pending"

    def test_late_fee_and_discount_are_included_in_dues(
        self, unit: UnitFactory
    ) -> None:
        rent_record = RentRecordPaidFactory(
            unit=unit,
            amount=Decimal("28000"),
            late_fee=Decimal("500"),
            discount=Decimal("1000"),
        )

        receipt = build_receipt(rent_record)

        assert receipt.dues_amount == "₹27,500"
        assert receipt.paid_amount == "₹28,000"
        assert receipt.net_balance == "—"

    def test_unknown_payment_method_falls_back_to_dash(self, unit: UnitFactory) -> None:
        rent_record = RentRecordPaidFactory(unit=unit)
        rent_record.payment_method = "unknown_mode"
        rent_record.save(update_fields=["payment_method"])

        receipt = build_receipt(rent_record)

        assert receipt.payment_method == "—"
