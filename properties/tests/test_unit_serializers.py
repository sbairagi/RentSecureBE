"""Tests for properties/serializers/unit_serializers.py."""

from django.test import TestCase

from core.models import User
from properties.models import Building, Renter, Unit, UnitDocument, UnitImage
from properties.serializers.unit_serializers import (
    RentAgreementDraftSerializer,
    UnitDocumentSerializer,
    UnitImageSerializer,
    UnitSerializer,
)


class UnitSerializerValidationTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="unit_ser_owner",
            password="p",
            full_name="UnitSerializerOwner",
            phone="+91",
        )
        self.other = User.objects.create_user(
            username="unit_ser_other",
            password="p",
            full_name="OtherUser",
            phone="+92",
        )
        self.building = Building.objects.create(
            name="USB",
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
            unit="US1",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )

    def _make_request(self, user):
        return type("Req", (), {"user": user})()

    def test_validate_wrong_building_owner(self):
        data = {
            "building": self.building.id,
            "unit": "HACK",
            "unit_type": "flat",
            "rent_amount": "1000",
            "address_line": "1 St",
            "city": "C",
            "state": "S",
            "country": "CO",
            "postal_code": "1",
        }
        request = self._make_request(self.other)
        serializer = UnitSerializer(data=data, context={"request": request})
        self.assertFalse(serializer.is_valid())
        self.assertTrue(
            any(
                "building" in str(e)
                for e in serializer.errors.get("non_field_errors", [])
            )
        )

    def test_validate_latitude_out_of_range(self):
        data = {
            "building": self.building.id,
            "unit": "US2",
            "unit_type": "flat",
            "rent_amount": "1000",
            "latitude": 100,
            "address_line": "1 St",
            "city": "C",
            "state": "S",
            "country": "CO",
            "postal_code": "1",
        }
        request = self._make_request(self.owner)
        serializer = UnitSerializer(data=data, context={"request": request})
        self.assertFalse(serializer.is_valid())
        nf_errors = serializer.errors.get("non_field_errors", [])
        self.assertTrue(any("latitude" in str(e).lower() for e in nf_errors))

    def test_validate_longitude_out_of_range(self):
        data = {
            "building": self.building.id,
            "unit": "US3",
            "unit_type": "flat",
            "rent_amount": "1000",
            "longitude": 200,
            "address_line": "1 St",
            "city": "C",
            "state": "S",
            "country": "CO",
            "postal_code": "1",
        }
        request = self._make_request(self.owner)
        serializer = UnitSerializer(data=data, context={"request": request})
        self.assertFalse(serializer.is_valid())
        nf_errors = serializer.errors.get("non_field_errors", [])
        self.assertTrue(any("longitude" in str(e).lower() for e in nf_errors))

    def test_update_wrong_building_owner(self):
        other_building = Building.objects.create(
            name="OB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
            owner=self.other,
        )
        data = {"building": other_building.id}
        request = self._make_request(self.owner)
        serializer = UnitSerializer(
            self.unit, data=data, context={"request": request}, partial=True
        )
        self.assertFalse(serializer.is_valid())
        self.assertTrue(
            any(
                "building" in str(e)
                for e in serializer.errors.get("non_field_errors", [])
            )
        )


class UnitImageSerializerValidationTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="ui_owner",
            password="p",
            full_name="UIImageOwner",
            phone="+91",
        )
        self.building = Building.objects.create(
            name="UIB",
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
            unit="UI1",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        self.image = UnitImage.objects.create(unit=self.unit, image="existing.jpg")

    def _make_request(self, user):
        return type("Req", (), {"user": user})()

    def test_update_wrong_unit_owner(self):
        attacker = User.objects.create_user(
            username="ui_attacker", password="p", full_name="UIAttacker", phone="+92"
        )
        other_building = Building.objects.create(
            name="OIB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
            owner=attacker,
        )
        other_unit = Unit.objects.create(
            owner=attacker,
            building=other_building,
            unit="OUI1",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        data = {"unit": other_unit.id}
        request = self._make_request(self.owner)
        serializer = UnitImageSerializer(
            self.image, data=data, context={"request": request}, partial=True
        )
        self.assertFalse(serializer.is_valid())


class UnitDocumentSerializerValidationTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="ud_owner",
            password="p",
            full_name="UDOwner",
            phone="+91",
        )
        self.building = Building.objects.create(
            name="UDB",
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
            unit="UD1",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        self.doc = UnitDocument.objects.create(unit=self.unit, document="existing.pdf")

    def _make_request(self, user):
        return type("Req", (), {"user": user})()

    def test_update_wrong_unit_owner(self):
        attacker = User.objects.create_user(
            username="ud_attacker", password="p", full_name="UDAttacker", phone="+92"
        )
        other_building = Building.objects.create(
            name="ODB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
            owner=attacker,
        )
        other_unit = Unit.objects.create(
            owner=attacker,
            building=other_building,
            unit="OUD1",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        data = {"unit": other_unit.id}
        request = self._make_request(self.owner)
        serializer = UnitDocumentSerializer(
            self.doc, data=data, context={"request": request}, partial=True
        )
        self.assertFalse(serializer.is_valid())


class RentAgreementDraftSerializerValidationTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="rad_owner",
            password="p",
            full_name="RADOwner",
            phone="+91",
        )
        self.building = Building.objects.create(
            name="RADB",
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
            unit="RAD1",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        self.renter = Renter.objects.create(
            unit=self.unit,
            name="RADRenter",
            phone="+911234567894",
            email="radr@test.com",
            rent_amount=10000,
            start_date="2024-01-01",
        )

    def _make_request(self, user):
        return type("Req", (), {"user": user})()

    def test_validate_missing_renter_and_unit(self):
        data = {}
        request = self._make_request(self.owner)
        serializer = RentAgreementDraftSerializer(
            data=data, context={"request": request}
        )
        self.assertFalse(serializer.is_valid())

    def test_validate_wrong_unit_owner(self):
        other = User.objects.create_user(
            username="rad_other",
            password="p",
            full_name="RADOther",
            phone="+92",
        )
        data = {"renter": self.renter.id, "unit": self.unit.id}
        request = self._make_request(other)
        serializer = RentAgreementDraftSerializer(
            data=data, context={"request": request}
        )
        self.assertFalse(serializer.is_valid())

    def test_validate_renter_unit_mismatch(self):
        other_unit = Unit.objects.create(
            owner=self.owner,
            building=self.building,
            unit="RAD2",
            unit_type="flat",
            address_line="2 St",
            city="C",
            state="S",
            country="CO",
            postal_code="2",
        )
        data = {"renter": self.renter.id, "unit": other_unit.id}
        request = self._make_request(self.owner)
        serializer = RentAgreementDraftSerializer(
            data=data, context={"request": request}
        )
        self.assertFalse(serializer.is_valid())
