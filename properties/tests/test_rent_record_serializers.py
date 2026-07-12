"""Comprehensive tests for RentRecordSerializer uncovered branches."""

from datetime import date
from unittest.mock import patch

from django.test import TestCase

from core.models import User
from properties.models import Building, Renter, RentRecord, Unit
from properties.serializers.rent_record_serializers import RentRecordSerializer


class RentRecordSerializerCoverageTests(TestCase):
    """Cover all uncovered branches of RentRecordSerializer."""

    def setUp(self):
        self.owner = User.objects.create_user(
            username="rr_serializer_coverage_owner",
            password="testpass123",
            full_name="Coverage Owner",
            phone="+911",
        )
        self.building = Building.objects.create(
            owner=self.owner,
            name="COB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        self.unit = Unit.objects.create(
            owner=self.owner,
            building=self.building,
            unit="CO101",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        self.renter = Renter.objects.create(
            unit=self.unit,
            name="Coverage Renter",
            phone="+912345678901",
            email="cr@test.com",
            rent_amount=10000,
            start_date=date(2025, 1, 1),
        )
        self.rent_record = RentRecord.objects.create(
            renter=self.renter,
            unit=self.unit,
            due_date=date(2025, 1, 1),
            amount=10000,
            payment_method="upi",
            status=RentRecord.Status.PENDING,
            paid_on=date(2025, 1, 5),
        )
        self.rent_record_no_renter = RentRecord.objects.create(
            renter=None,
            unit=self.unit,
            due_date=date(2025, 2, 1),
            amount=10000,
            payment_method="upi",
            status=RentRecord.Status.PENDING,
        )

        other_building = Building.objects.create(
            owner=self.owner,
            name="OB2",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        self.other_unit = Unit.objects.create(
            owner=self.owner,
            building=other_building,
            unit="OB201",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        self.mismatch_unit = Unit.objects.create(
            owner=self.owner,
            building=other_building,
            unit="OB202",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        self.other_renter = Renter.objects.create(
            unit=self.other_unit,
            name="Other Renter",
            phone="+912345678902",
            rent_amount=5000,
            start_date=date(2025, 1, 1),
        )

    def _make_request(self, user):
        return type("Req", (), {"user": user})()

    def test_create_rent_record_valid(self):
        serializer = RentRecordSerializer(
            data={
                "unit": self.unit.id,
                "renter": self.renter.id,
                "amount": 10000,
                "payment_method": "upi",
                "status": "pending",
                "due_date": "2025-03-01",
            },
            context={"request": self._make_request(self.owner)},
        )
        self.assertTrue(serializer.is_valid())

    def test_validate_update_fields_forbids_disallowed_fields(self):
        serializer = RentRecordSerializer(
            self.rent_record,
            data={"notes": "updated", "status": "paid"},
            context={"request": self._make_request(self.owner)},
            partial=True,
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("error", serializer.errors)

    def test_validate_renter_unit_assignment_mismatch(self):
        allowed_fields = {
            "unit",
            "renter",
            "notes",
            "adjustment_reason",
            "late_fee",
            "discount",
        }
        with patch.object(
            RentRecordSerializer, "ALLOWED_UPDATE_FIELDS", allowed_fields
        ):
            serializer = RentRecordSerializer(
                self.rent_record,
                data={"unit": self.mismatch_unit.id, "renter": self.other_renter.id},
                context={"request": self._make_request(self.owner)},
                partial=True,
            )
            self.assertFalse(serializer.is_valid())
            self.assertIn("non_field_errors", serializer.errors)

    def test_validate_amount_paid_negative(self):
        allowed_fields = {
            "amount_paid",
            "notes",
            "adjustment_reason",
            "late_fee",
            "discount",
        }
        with patch.object(
            RentRecordSerializer, "ALLOWED_UPDATE_FIELDS", allowed_fields
        ):
            serializer = RentRecordSerializer(
                self.rent_record,
                data={"amount_paid": -100},
                context={"request": self._make_request(self.owner)},
                partial=True,
            )
            from rest_framework import serializers as drf_serializers

            serializer.fields["amount_paid"] = drf_serializers.DecimalField(
                max_digits=10, decimal_places=2, required=False, allow_null=True
            )
            self.assertFalse(serializer.is_valid())
            self.assertIn("non_field_errors", serializer.errors)

    def test_validate_renter_ownership_wrong_owner(self):
        other = User.objects.create_user(
            username="rr_intruder",
            password="p",
            full_name="Intruder",
            phone="+92",
        )
        other_building = Building.objects.create(
            owner=other,
            name="IOB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        other_unit = Unit.objects.create(
            owner=other,
            building=other_building,
            unit="IOB1",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        other_renter = Renter.objects.create(
            unit=other_unit,
            name="Intruder Renter",
            phone="+912345678903",
            rent_amount=5000,
            start_date=date(2025, 1, 1),
        )
        allowed_fields = {
            "renter",
            "notes",
            "adjustment_reason",
            "late_fee",
            "discount",
        }
        with patch.object(
            RentRecordSerializer, "ALLOWED_UPDATE_FIELDS", allowed_fields
        ):
            serializer = RentRecordSerializer(
                self.rent_record,
                data={"renter": other_renter.id},
                context={"request": self._make_request(self.owner)},
                partial=True,
            )
            self.assertFalse(serializer.is_valid())
            self.assertIn("non_field_errors", serializer.errors)

    def test_validate_renter_ownership_no_renter(self):
        allowed_fields = {
            "renter",
            "notes",
            "adjustment_reason",
            "late_fee",
            "discount",
        }
        with patch.object(
            RentRecordSerializer, "ALLOWED_UPDATE_FIELDS", allowed_fields
        ):
            serializer = RentRecordSerializer(
                self.rent_record_no_renter,
                data={"renter": None},
                context={"request": self._make_request(self.owner)},
                partial=True,
            )
            self.assertFalse(serializer.is_valid())
            self.assertIn("non_field_errors", serializer.errors)

    def test_validate_rent_month_and_date_paid_earlier(self):
        allowed_fields = {
            "rent_month",
            "date_paid",
            "notes",
            "adjustment_reason",
            "late_fee",
            "discount",
        }
        with patch.object(
            RentRecordSerializer, "ALLOWED_UPDATE_FIELDS", allowed_fields
        ):
            serializer = RentRecordSerializer(
                self.rent_record,
                data={
                    "rent_month": date(2025, 3, 1).isoformat(),
                    "date_paid": date(2025, 2, 1).isoformat(),
                },
                context={"request": self._make_request(self.owner)},
                partial=True,
            )
            from rest_framework import serializers as drf_serializers

            serializer.fields["rent_month"] = drf_serializers.DateField(
                required=False, allow_null=True
            )
            serializer.fields["date_paid"] = drf_serializers.DateField(
                required=False, allow_null=True
            )
            self.assertFalse(serializer.is_valid())
            self.assertIn("non_field_errors", serializer.errors)

    def test_get_invoice_url_paid_with_invoice(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        pdf_file = SimpleUploadedFile(
            "invoice.pdf", b"%PDF-1.4 fake", content_type="application/pdf"
        )
        self.rent_record.invoice_pdf.save("invoice.pdf", pdf_file, save=True)
        serializer = RentRecordSerializer(
            self.rent_record, context={"request": self._make_request(self.owner)}
        )
        with patch.object(self.rent_record, "status", "PAID"):
            result = serializer.get_invoice_url(self.rent_record)
        self.assertEqual(result, self.rent_record.invoice_pdf.url)

    def test_get_invoice_url_paid_no_invoice(self):
        serializer = RentRecordSerializer(
            self.rent_record, context={"request": self._make_request(self.owner)}
        )
        with patch.object(self.rent_record, "status", "PAID"):
            result = serializer.get_invoice_url(self.rent_record)
        self.assertEqual(result, "")

    def test_get_invoice_url_pending_status(self):
        serializer = RentRecordSerializer(
            self.rent_record, context={"request": self._make_request(self.owner)}
        )
        self.assertEqual(serializer.get_invoice_url(self.rent_record), "")

    def test_update_with_allowed_fields(self):
        serializer = RentRecordSerializer(
            self.rent_record,
            data={"notes": "Late fee waived", "late_fee": 500},
            context={"request": self._make_request(self.owner)},
            partial=True,
        )
        self.assertTrue(serializer.is_valid())
        updated = serializer.save()
        self.assertEqual(updated.notes, "Late fee waived")
        self.assertEqual(updated.late_fee, 500)
