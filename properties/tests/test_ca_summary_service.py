"""Tests for properties/services/ca_summary_service.py."""

from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from core.models import User
from properties.models import Building, PropertyTaxRecord, Renter, RentRecord, Unit
from properties.services.ca_summary_service import (
    _build_rows,
    _get_rents,
    _get_taxes,
    generate_ca_summary_csv,
    generate_ca_summary_json,
)


class CaSummaryServiceTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="ca_owner",
            password="p",
            full_name="CAOwner",
            phone="+1",
        )
        self.building = Building.objects.create(
            owner=self.owner,
            name="CABuilding",
            address_line="1 Main St",
            city="City",
            state="ST",
            country="CO",
            postal_code="1",
        )
        self.unit = Unit.objects.create(
            owner=self.owner,
            building=self.building,
            unit="CA1",
            unit_type="flat",
            address_line="1 Main St",
            city="City",
            state="ST",
            country="CO",
            postal_code="1",
        )
        self.renter = Renter.objects.create(
            unit=self.unit,
            name="CARenter",
            phone="+911234567890",
            email="ca@test.com",
            rent_amount=Decimal("10000"),
            start_date=timezone.now().date(),
        )
        self.start_date = "2025-01-01"
        self.end_date = "2025-03-31"

    def test_get_rents_returns_owner_rents_in_range(self):
        RentRecord.objects.create(
            unit=self.unit,
            renter=self.renter,
            amount=Decimal("10000"),
            due_date="2025-01-01",
            paid_on="2025-01-05",
            status=RentRecord.Status.PAID,
            payout_status="SUCCESS",
        )
        rents = _get_rents(self.owner, self.start_date, self.end_date)
        self.assertEqual(rents.count(), 1)

    def test_get_taxes_returns_owner_taxes_in_range(self):
        PropertyTaxRecord.objects.create(
            property=self.building,
            amount=Decimal("5000"),
            due_date="2025-03-31",
            paid=True,
            paid_date="2025-03-15",
        )
        taxes = _get_taxes(self.owner, self.start_date, self.end_date)
        self.assertEqual(taxes.count(), 1)

    def test_build_rows_returns_expected_shape(self):
        RentRecord.objects.create(
            unit=self.unit,
            renter=self.renter,
            amount=Decimal("10000"),
            due_date="2025-01-01",
            paid_on="2025-01-05",
            status=RentRecord.Status.PAID,
            payout_status="SUCCESS",
        )
        PropertyTaxRecord.objects.create(
            property=self.building,
            amount=Decimal("5000"),
            due_date="2025-03-31",
            paid=True,
            paid_date="2025-03-15",
        )
        rows = _build_rows(self.owner, self.start_date, self.end_date)
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["renter"], "CARenter")
        self.assertEqual(row["rent_amount"], 10000.0)
        self.assertEqual(row["tax_amount"], 5000.0)

    def test_generate_ca_summary_csv_returns_bytes(self):
        RentRecord.objects.create(
            unit=self.unit,
            renter=self.renter,
            amount=Decimal("10000"),
            due_date="2025-01-01",
            paid_on="2025-01-05",
            status=RentRecord.Status.PAID,
            payout_status="SUCCESS",
        )
        csv_bytes = generate_ca_summary_csv(self.owner, self.start_date, self.end_date)
        self.assertIsInstance(csv_bytes, bytes)
        self.assertIn(b"CARenter", csv_bytes)

    def test_generate_ca_summary_json_returns_bytes(self):
        RentRecord.objects.create(
            unit=self.unit,
            renter=self.renter,
            amount=Decimal("10000"),
            due_date="2025-01-01",
            paid_on="2025-01-05",
            status=RentRecord.Status.PAID,
            payout_status="SUCCESS",
        )
        json_bytes = generate_ca_summary_json(
            self.owner, self.start_date, self.end_date
        )
        self.assertIsInstance(json_bytes, bytes)
        self.assertIn(b"CARenter", json_bytes)
        self.assertIn(b"records", json_bytes)
