"""Tests for properties/serializers/renter_serializers.py."""

from datetime import date

from rest_framework.exceptions import PermissionDenied

from django.test import TestCase

from core.models import User
from properties.models import Building, Renter, RentRecord, Unit
from properties.serializers.renter_serializers import (
    RenterRentRecordSerializer,
    RenterSerializer,
)


class RenterSerializerValidationTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="rs_owner",
            password="p",
            full_name="RSOwner",
            phone="+91",
        )
        self.other = User.objects.create_user(
            username="rs_other",
            password="p",
            full_name="RSOther",
            phone="+92",
        )
        self.building = Building.objects.create(
            name="RSB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
            owner=self.owner,
        )
        self.unit = Unit.objects.create(
            owner=self.owner,
            building=self.building,
            unit="RS1",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        self.renter = Renter.objects.create(
            unit=self.unit,
            name="RS Renter",
            phone="+911234567895",
            email="rsr@test.com",
            rent_amount=10000,
            start_date=date(2024, 1, 1),
        )

    def _make_request(self, user):
        return type("Req", (), {"user": user})()

    def test_validate_wrong_unit_owner(self):
        data = {
            "unit": self.unit.id,
            "name": "Test Renter",
            "phone": "+9111111111",
            "rent_amount": "1000",
            "start_date": str(date.today()),
        }
        request = self._make_request(self.other)
        serializer = RenterSerializer(data=data, context={"request": request})
        with self.assertRaises(PermissionDenied):
            serializer.is_valid()

    def test_update_renter_with_wrong_unit_owner(self):
        other_building = Building.objects.create(
            name="ORSB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
            owner=self.other,
        )
        other_unit = Unit.objects.create(
            owner=self.other,
            building=other_building,
            unit="ORS1",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        request = self._make_request(self.owner)
        serializer = RenterSerializer(
            self.renter, context={"request": request}, partial=True
        )
        validated_data = {"unit": other_unit}
        from rest_framework.exceptions import ValidationError

        with self.assertRaises(ValidationError):
            serializer.update(self.renter, validated_data)


class RenterRentRecordSerializerTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="rr_owner",
            password="p",
            full_name="RROwner",
            phone="+91",
        )
        self.building = Building.objects.create(
            name="RRB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
            owner=self.owner,
        )
        self.unit = Unit.objects.create(
            owner=self.owner,
            building=self.building,
            unit="RR1",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        self.renter = Renter.objects.create(
            unit=self.unit,
            name="RR Renter",
            phone="+911234567896",
            email="rrr@test.com",
            rent_amount=10000,
            start_date=date(2024, 1, 1),
        )
        self.rent = RentRecord.objects.create(
            unit=self.unit,
            renter=self.renter,
            amount=15000,
            payment_method="upi",
            status=RentRecord.Status.PAID,
            paid_on=date(2024, 1, 5),
            due_date=date(2024, 1, 5),
        )

    def test_get_invoice_url_when_paid(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        pdf_content = b"%PDF-1.4 fake pdf"
        pdf_file = SimpleUploadedFile(
            "invoice.pdf", pdf_content, content_type="application/pdf"
        )
        self.rent.invoice_pdf.save("invoice.pdf", pdf_file, save=True)
        serializer = RenterRentRecordSerializer(self.rent)
        data = serializer.data
        self.assertIn("invoice_url", data)

    def test_get_invoice_url_when_pending(self):
        rent = RentRecord.objects.create(
            unit=self.unit,
            renter=self.renter,
            amount=10000,
            payment_method="upi",
            status=RentRecord.Status.PENDING,
            paid_on=date(2024, 1, 10),
            due_date=date(2024, 2, 5),
        )
        serializer = RenterRentRecordSerializer(rent)
        data = serializer.data
        self.assertEqual(data["invoice_url"], "")
