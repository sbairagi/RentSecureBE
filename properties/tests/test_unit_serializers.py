"""Tests for properties/serializers/unit_serializers.py."""

import io

import pytest
from PIL import Image as PILImage
from rest_framework import serializers
from rest_framework.test import APIClient

from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory

from conftest import BuildingFactory, RenterFactory, UnitFactory, UserFactory
from properties.models import UnitDocument, UnitImage
from properties.serializers.unit_serializers import (
    RentAgreementDraftSerializer,
    UnitDocumentSerializer,
    UnitImageSerializer,
    UnitSerializer,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_request(user):
    factory = RequestFactory()
    request = factory.get("/")
    request.user = user
    return request


@pytest.fixture
def api_client():
    return APIClient()


def _make_image_file(name="test.jpg"):
    img = PILImage.new("RGB", (100, 100), color="red")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    return ContentFile(buf.read(), name=name)


def _make_doc_file(name="test.pdf"):
    return SimpleUploadedFile(name, b"fake-doc", content_type="application/pdf")


# ---------------------------------------------------------------------------
# UnitSerializer
# ---------------------------------------------------------------------------


class TestUnitSerializer:
    def test_validate_wrong_building_owner(self, owner, building):
        other = UserFactory(username="us_other", phone="+92")
        data = {
            "building": building.id,
            "unit": "HACK",
            "unit_type": "flat",
            "rent_amount": 1000,
            "address_line": "1 St",
            "city": "C",
            "state": "S",
            "country": "CO",
            "postal_code": "1",
        }
        request = _make_request(other)
        serializer = UnitSerializer(data=data, context={"request": request})
        assert not serializer.is_valid()

    def test_validate_latitude_out_of_range(self, owner, building):
        data = {
            "building": building.id,
            "unit": "US2",
            "unit_type": "flat",
            "rent_amount": 1000,
            "latitude": 100,
            "address_line": "1 St",
            "city": "C",
            "state": "S",
            "country": "CO",
            "postal_code": "1",
        }
        request = _make_request(owner)
        serializer = UnitSerializer(data=data, context={"request": request})
        assert not serializer.is_valid()

    def test_validate_longitude_out_of_range(self, owner, building):
        data = {
            "building": building.id,
            "unit": "US3",
            "unit_type": "flat",
            "rent_amount": 1000,
            "longitude": 200,
            "address_line": "1 St",
            "city": "C",
            "state": "S",
            "country": "CO",
            "postal_code": "1",
        }
        request = _make_request(owner)
        serializer = UnitSerializer(data=data, context={"request": request})
        assert not serializer.is_valid()

    def test_validate_valid_data(self, owner, building):
        UnitFactory(owner=owner, building=building)
        data = {
            "building": building.id,
            "unit": "VU1",
            "unit_type": "flat",
            "rent_amount": 1000,
            "address_line": "1 St",
            "city": "C",
            "state": "S",
            "country": "CO",
            "postal_code": "1",
        }
        request = _make_request(owner)
        serializer = UnitSerializer(data=data, context={"request": request})
        assert serializer.is_valid(), serializer.errors

    def test_validate_building_from_instance(self, owner, building):
        unit = UnitFactory(owner=owner, building=building)
        data = {
            "unit": "VU2",
            "unit_type": "flat",
            "rent_amount": 1000,
            "address_line": "1 St",
            "city": "C",
            "state": "S",
            "country": "CO",
            "postal_code": "1",
        }
        request = _make_request(owner)
        serializer = UnitSerializer(
            unit, data=data, context={"request": request}, partial=True
        )
        assert serializer.is_valid(), serializer.errors

    def test_validate_valid_latitude_longitude(self, owner, building):
        data = {
            "building": building.id,
            "unit": "VU3",
            "unit_type": "flat",
            "rent_amount": 1000,
            "latitude": 45.5,
            "longitude": -73.5,
            "address_line": "1 St",
            "city": "C",
            "state": "S",
            "country": "CO",
            "postal_code": "1",
        }
        request = _make_request(owner)
        serializer = UnitSerializer(data=data, context={"request": request})
        assert serializer.is_valid(), serializer.errors

    def test_validate_latitude_boundary_valid(self, owner, building):
        data = {
            "building": building.id,
            "unit": "VU4",
            "unit_type": "flat",
            "rent_amount": 1000,
            "latitude": -90,
            "address_line": "1 St",
            "city": "C",
            "state": "S",
            "country": "CO",
            "postal_code": "1",
        }
        request = _make_request(owner)
        serializer = UnitSerializer(data=data, context={"request": request})
        assert serializer.is_valid(), serializer.errors

    def test_validate_longitude_boundary_valid(self, owner, building):
        data = {
            "building": building.id,
            "unit": "VU5",
            "unit_type": "flat",
            "rent_amount": 1000,
            "longitude": -180,
            "address_line": "1 St",
            "city": "C",
            "state": "S",
            "country": "CO",
            "postal_code": "1",
        }
        request = _make_request(owner)
        serializer = UnitSerializer(data=data, context={"request": request})
        assert serializer.is_valid(), serializer.errors

    def test_create_sets_owner(self, owner, building):
        data = {
            "building": building.id,
            "unit": "NEW1",
            "unit_type": "flat",
            "rent_amount": 1000,
            "address_line": "1 St",
            "city": "C",
            "state": "S",
            "country": "CO",
            "postal_code": "1",
        }
        request = _make_request(owner)
        serializer = UnitSerializer(data=data, context={"request": request})
        assert serializer.is_valid(), serializer.errors
        unit = serializer.save()
        assert unit.owner == owner

    def test_update_wrong_building_owner(self, owner, building):
        other = UserFactory(username="us_other2", phone="+92")
        other_building = BuildingFactory(owner=other, name="OB")
        unit = UnitFactory(owner=owner, building=building)
        data = {"building": other_building.id}
        request = _make_request(owner)
        serializer = UnitSerializer(
            unit, data=data, context={"request": request}, partial=True
        )
        assert not serializer.is_valid()

    def test_update_valid_building(self, owner, building):
        unit = UnitFactory(owner=owner, building=building)
        data = {"unit": "UPD1"}
        request = _make_request(owner)
        serializer = UnitSerializer(
            unit, data=data, context={"request": request}, partial=True
        )
        assert serializer.is_valid(), serializer.errors
        updated = serializer.save()
        assert updated.unit == "UPD1"

    def test_update_method_rejects_wrong_building(self, owner, building):
        other = UserFactory(username="us_direct", phone="+92")
        other_building = BuildingFactory(owner=other)
        unit = UnitFactory(owner=owner, building=building)
        request = _make_request(owner)
        serializer = UnitSerializer(context={"request": request})
        with pytest.raises(serializers.ValidationError):
            serializer.update(unit, {"building": other_building})

    def test_api_create_unit(self, owner, building, api_client):
        api_client.force_authenticate(user=owner)
        payload = {
            "building": building.id,
            "unit": "API1",
            "unit_type": "flat",
            "rent_amount": 1000,
            "address_line": "1 St",
            "city": "C",
            "state": "S",
            "country": "CO",
            "postal_code": "1",
        }
        response = api_client.post("/properties/units/", payload, format="json")
        assert response.status_code == 201, response.data
        assert response.data["owner"] == owner.id


# ---------------------------------------------------------------------------
# UnitImageSerializer
# ---------------------------------------------------------------------------


class TestUnitImageSerializer:
    def test_validate_valid_data(self, owner, unit):
        image_file = _make_image_file("valid.jpg")
        data = {"unit": unit.id, "image": image_file}
        request = _make_request(owner)
        serializer = UnitImageSerializer(data=data, context={"request": request})
        assert serializer.is_valid(), serializer.errors

    def test_validate_unit_from_instance(self, owner, unit):
        existing = UnitImage.objects.create(unit=unit, image="existing.jpg")
        data = {}
        request = _make_request(owner)
        serializer = UnitImageSerializer(
            existing, data=data, context={"request": request}, partial=True
        )
        assert serializer.is_valid(), serializer.errors

    def test_update_valid_unit(self, owner, unit):
        existing = UnitImage.objects.create(unit=unit, image="existing.jpg")
        new_unit = UnitFactory(owner=owner, building=unit.building)
        data = {"unit": new_unit.id}
        request = _make_request(owner)
        serializer = UnitImageSerializer(
            existing, data=data, context={"request": request}, partial=True
        )
        assert serializer.is_valid(), serializer.errors
        updated = serializer.save()
        assert updated.unit_id == new_unit.id

    def test_update_method_rejects_wrong_unit(self, owner, unit):
        attacker = UserFactory(username="ui_direct", phone="+92")
        other_building = BuildingFactory(owner=attacker)
        other_unit = UnitFactory(owner=attacker, building=other_building)
        existing = UnitImage.objects.create(unit=unit, image="existing.jpg")
        request = _make_request(owner)
        serializer = UnitImageSerializer(context={"request": request})
        with pytest.raises(serializers.ValidationError):
            serializer.update(existing, {"unit": other_unit})

    def test_validate_wrong_unit_owner(self, owner, unit):
        attacker = UserFactory(username="ui_attacker", phone="+92")
        other_building = BuildingFactory(owner=attacker)
        other_unit = UnitFactory(owner=attacker, building=other_building)
        image_file = _make_image_file("bad.jpg")
        data = {"unit": other_unit.id, "image": image_file}
        request = _make_request(owner)
        serializer = UnitImageSerializer(data=data, context={"request": request})
        assert not serializer.is_valid()

    def test_update_wrong_unit_owner(self, owner, unit):
        attacker = UserFactory(username="ui_attacker2", phone="+92")
        other_building = BuildingFactory(owner=attacker)
        other_unit = UnitFactory(owner=attacker, building=other_building)
        existing = UnitImage.objects.create(unit=unit, image="existing.jpg")
        data = {"unit": other_unit.id}
        request = _make_request(owner)
        serializer = UnitImageSerializer(
            existing, data=data, context={"request": request}, partial=True
        )
        assert not serializer.is_valid()

    def test_api_upload_image(self, owner, unit, api_client):
        api_client.force_authenticate(user=owner)
        image_file = _make_image_file("api.jpg")
        payload = {"unit": unit.id, "image": image_file}
        response = api_client.post(
            "/properties/unit-images/", payload, format="multipart"
        )
        assert response.status_code == 201, response.data


# ---------------------------------------------------------------------------
# UnitDocumentSerializer
# ---------------------------------------------------------------------------


class TestUnitDocumentSerializer:
    def test_validate_valid_data(self, owner, unit):
        doc_file = _make_doc_file("valid.pdf")
        data = {"unit": unit.id, "document": doc_file}
        request = _make_request(owner)
        serializer = UnitDocumentSerializer(data=data, context={"request": request})
        assert serializer.is_valid(), serializer.errors

    def test_validate_unit_from_instance(self, owner, unit):
        existing = UnitDocument.objects.create(unit=unit, document="existing.pdf")
        data = {}
        request = _make_request(owner)
        serializer = UnitDocumentSerializer(
            existing, data=data, context={"request": request}, partial=True
        )
        assert serializer.is_valid(), serializer.errors

    def test_update_valid_unit(self, owner, unit):
        existing = UnitDocument.objects.create(unit=unit, document="existing.pdf")
        new_unit = UnitFactory(owner=owner, building=unit.building)
        data = {"unit": new_unit.id}
        request = _make_request(owner)
        serializer = UnitDocumentSerializer(
            existing, data=data, context={"request": request}, partial=True
        )
        assert serializer.is_valid(), serializer.errors
        updated = serializer.save()
        assert updated.unit_id == new_unit.id

    def test_update_method_rejects_wrong_unit(self, owner, unit):
        attacker = UserFactory(username="ud_direct", phone="+92")
        other_building = BuildingFactory(owner=attacker)
        other_unit = UnitFactory(owner=attacker, building=other_building)
        existing = UnitDocument.objects.create(unit=unit, document="existing.pdf")
        request = _make_request(owner)
        serializer = UnitDocumentSerializer(context={"request": request})
        with pytest.raises(serializers.ValidationError):
            serializer.update(existing, {"unit": other_unit})

    def test_validate_wrong_unit_owner(self, owner, unit):
        attacker = UserFactory(username="ud_attacker", phone="+92")
        other_building = BuildingFactory(owner=attacker)
        other_unit = UnitFactory(owner=attacker, building=other_building)
        doc_file = _make_doc_file("bad.pdf")
        data = {"unit": other_unit.id, "document": doc_file}
        request = _make_request(owner)
        serializer = UnitDocumentSerializer(data=data, context={"request": request})
        assert not serializer.is_valid()

    def test_update_wrong_unit_owner(self, owner, unit):
        attacker = UserFactory(username="ud_attacker2", phone="+92")
        other_building = BuildingFactory(owner=attacker)
        other_unit = UnitFactory(owner=attacker, building=other_building)
        existing = UnitDocument.objects.create(unit=unit, document="existing.pdf")
        data = {"unit": other_unit.id}
        request = _make_request(owner)
        serializer = UnitDocumentSerializer(
            existing, data=data, context={"request": request}, partial=True
        )
        assert not serializer.is_valid()

    def test_api_upload_document(self, owner, unit, api_client):
        api_client.force_authenticate(user=owner)
        doc_file = _make_doc_file("api.pdf")
        payload = {"unit": unit.id, "document": doc_file}
        response = api_client.post(
            "/properties/unit-all-documents/", payload, format="multipart"
        )
        assert response.status_code == 201, response.data


# ---------------------------------------------------------------------------
# RentAgreementDraftSerializer
# ---------------------------------------------------------------------------


class TestRentAgreementDraftSerializer:
    def test_validate_valid_data(self, owner, unit):
        renter = RenterFactory(unit=unit)
        draft_file = _make_doc_file("draft.pdf")
        data = {"renter": renter.id, "unit": unit.id, "file": draft_file}
        request = _make_request(owner)
        serializer = RentAgreementDraftSerializer(
            data=data, context={"request": request}
        )
        assert serializer.is_valid(), serializer.errors

    def test_validate_missing_renter(self, owner, unit):
        draft_file = _make_doc_file("draft2.pdf")
        data = {"unit": unit.id, "file": draft_file}
        request = _make_request(owner)
        serializer = RentAgreementDraftSerializer(
            data=data, context={"request": request}
        )
        assert not serializer.is_valid()

    def test_validate_method_requires_renter_and_unit(self, owner, unit):
        request = _make_request(owner)
        serializer = RentAgreementDraftSerializer(context={"request": request})
        with pytest.raises(serializers.ValidationError):
            serializer.validate({})

    def test_validate_missing_unit(self, owner, unit):
        renter = RenterFactory(unit=unit)
        draft_file = _make_doc_file("draft3.pdf")
        data = {"renter": renter.id, "file": draft_file}
        request = _make_request(owner)
        serializer = RentAgreementDraftSerializer(
            data=data, context={"request": request}
        )
        assert not serializer.is_valid()

    def test_validate_wrong_unit_owner(self, owner, unit):
        renter = RenterFactory(unit=unit)
        other = UserFactory(username="rad_other", phone="+92")
        draft_file = _make_doc_file("draft4.pdf")
        data = {"renter": renter.id, "unit": unit.id, "file": draft_file}
        request = _make_request(other)
        serializer = RentAgreementDraftSerializer(
            data=data, context={"request": request}
        )
        assert not serializer.is_valid()

    def test_validate_renter_unit_mismatch(self, owner, unit):
        renter = RenterFactory(unit=unit)
        other_unit = UnitFactory(owner=owner, building=unit.building)
        draft_file = _make_doc_file("draft5.pdf")
        data = {"renter": renter.id, "unit": other_unit.id, "file": draft_file}
        request = _make_request(owner)
        serializer = RentAgreementDraftSerializer(
            data=data, context={"request": request}
        )
        assert not serializer.is_valid()

    def test_api_create_draft(self, owner, unit, api_client):
        renter = RenterFactory(unit=unit)
        draft_file = _make_doc_file("api_draft.pdf")
        api_client.force_authenticate(user=owner)
        payload = {"renter": renter.id, "unit": unit.id, "file": draft_file}
        response = api_client.post(
            "/properties/rent-agreement-drafts/", payload, format="multipart"
        )
        assert response.status_code == 201, response.data
