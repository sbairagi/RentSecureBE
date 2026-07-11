"""Tests for properties/serializers/extra_charge_serializers.py."""

from datetime import date

from django.test import TestCase

from core.models import User
from properties.models import Building, ExtraCharge, Renter, Unit
from properties.serializers.extra_charge_serializers import ExtraChargeSerializer


class ExtraChargeSerializerTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="extra_owner",
            password="p",
            full_name="ExtraOwner",
            phone="+91",
        )
        self.building = Building.objects.create(
            name="ExtraB",
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
            unit="E1",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        self.renter = Renter.objects.create(
            unit=self.unit,
            name="Extra Renter",
            phone="+911234567893",
            email="er@test.com",
            rent_amount=10000,
            start_date=date(2024, 1, 1),
        )
        self.extra = ExtraCharge.objects.create(
            renter=self.renter,
            unit=self.unit,
            name="Maintenance",
            amount=500,
            due_date=date(2024, 2, 1),
            status=ExtraCharge.Status.DUE,
        )

    def test_serialize_extra_charge(self):
        request = type("Req", (), {"user": self.owner})()
        serializer = ExtraChargeSerializer(self.extra, context={"request": request})
        data = serializer.data
        self.assertEqual(data["name"], "Maintenance")
        self.assertEqual(data["amount"], "500.00")
        self.assertEqual(data["status"], "DUE")

    def test_validate_missing_renter_and_unit(self):
        data = {
            "renter": None,
            "unit": None,
            "name": "Maintenance",
            "amount": 500,
            "due_date": "2024-02-01",
            "status": "DUE",
        }
        request = type("Req", (), {"user": self.owner})()
        serializer = ExtraChargeSerializer(data=data, context={"request": request})
        self.assertFalse(serializer.is_valid())
        self.assertIn("renter", serializer.errors)
        self.assertIn("unit", serializer.errors)

    def test_validate_renter_unit_mismatch(self):
        other_owner = User.objects.create_user(
            username="other_extra", password="p", full_name="Other", phone="+92"
        )
        other_building = Building.objects.create(
            name="OtherB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
            owner=other_owner,
        )
        other_unit = Unit.objects.create(
            owner=other_owner,
            building=other_building,
            unit="O1",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        data = {
            "renter": self.renter.id,
            "unit": other_unit.id,
            "name": "Maintenance",
            "amount": 500,
            "due_date": "2024-02-01",
            "status": "DUE",
        }
        request = type("Req", (), {"user": self.owner})()
        serializer = ExtraChargeSerializer(data=data, context={"request": request})
        self.assertFalse(serializer.is_valid())

    def test_validate_wrong_owner(self):
        attacker = User.objects.create_user(
            username="attacker", password="p", full_name="Attacker", phone="+93"
        )
        data = {
            "renter": self.renter.id,
            "unit": self.unit.id,
            "name": "Maintenance",
            "amount": 500,
            "due_date": "2024-02-01",
            "status": "DUE",
        }
        request = type("Req", (), {"user": attacker})()
        serializer = ExtraChargeSerializer(data=data, context={"request": request})
        self.assertFalse(serializer.is_valid())

    def test_validate_negative_amount(self):
        data = {
            "renter": self.renter.id,
            "unit": self.unit.id,
            "name": "Maintenance",
            "amount": -100,
            "due_date": "2024-02-01",
            "status": "DUE",
        }
        request = type("Req", (), {"user": self.owner})()
        serializer = ExtraChargeSerializer(data=data, context={"request": request})
        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)

    def test_update_extra_charge(self):
        data = {
            "name": "Electricity",
            "amount": 750,
            "due_date": "2024-02-01",
            "status": "PAID",
        }
        request = type("Req", (), {"user": self.owner})()
        serializer = ExtraChargeSerializer(
            self.extra, data=data, context={"request": request}, partial=True
        )
        self.assertTrue(serializer.is_valid())
        instance = serializer.save()
        self.assertEqual(instance.name, "Electricity")
        self.assertEqual(instance.amount, 750)
        self.assertEqual(instance.status, "PAID")
