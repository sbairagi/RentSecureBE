from __future__ import annotations

from datetime import date
from decimal import Decimal
from unittest import mock

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from properties.models import (
    PropertyTaxRecord,
    Renter,
    Unit,
    UnitDocument,
    UnitImage,
    UnitVacancy,
)
from tests.factories import (
    BuildingFactory,
    RenterFactory,
    RentRecordPaidFactory,
    UnitFactory,
    UserFactory,
)


class UnitLegacyKwargsTest(TestCase):
    """Cover Unit.__init__ legacy kwargs handling and defaults."""

    def test_unit_number_rent_amount_security_deposit_floor(self):
        user = UserFactory()
        building = BuildingFactory(owner=user)
        unit = Unit(
            building=building,
            unit_number="101",
            rent_amount=Decimal("5000"),
            security_deposit=Decimal("10000"),
            floor=2,
        )
        self.assertEqual(unit.unit, "101")
        self.assertEqual(unit.status, "VACANT")
        self.assertEqual(unit.rent_amount, Decimal("5000"))
        self.assertEqual(unit.security_deposit, Decimal("10000"))
        self.assertEqual(unit.unit_type, "flat")

    def test_owner_and_address_propagated_from_building(self):
        user = UserFactory()
        building = BuildingFactory(owner=user)
        unit = Unit(
            building=building,
            unit_number="102",
            rent_amount=Decimal("6000"),
            security_deposit=Decimal("12000"),
        )
        self.assertEqual(unit.owner, building.owner)
        self.assertEqual(unit.address_line, building.address_line)
        self.assertEqual(unit.city, building.city)
        self.assertEqual(unit.state, building.state)
        self.assertEqual(unit.country, building.country)
        self.assertEqual(unit.postal_code, building.postal_code)

    def test_floor_kwarg_is_discarded(self):
        user = UserFactory()
        building = BuildingFactory(owner=user)
        unit = Unit(
            building=building,
            unit_number="103",
            floor=5,
        )
        self.assertEqual(unit.unit, "103")
        self.assertEqual(unit.status, "VACANT")
        self.assertFalse(hasattr(unit, "floor"))

    def test_legacy_kwargs_not_required_when_unit_provided(self):
        user = UserFactory()
        building = BuildingFactory(owner=user)
        unit = Unit(building=building, unit="104")
        self.assertEqual(unit.unit, "104")
        self.assertEqual(unit.status, Unit.VacancyStatus.VACANT)
        self.assertEqual(unit.rent_amount, Decimal("0"))
        self.assertEqual(unit.security_deposit, Decimal("0"))

    def test_unit_not_overwritten_when_provided(self):
        user = UserFactory()
        building = BuildingFactory(owner=user)
        unit = Unit(
            building=building,
            unit="custom",
            unit_number="ignored",
        )
        self.assertEqual(unit.unit, "custom")

    def test_status_not_overwritten_when_provided(self):
        user = UserFactory()
        building = BuildingFactory(owner=user)
        unit = Unit(
            building=building,
            unit="105",
            status="occupied",
            unit_number="105",
        )
        self.assertEqual(unit.status, Unit.VacancyStatus.OCCUPIED)

    def test_no_building_defaults_to_flat(self):
        unit = Unit(unit="106")
        self.assertEqual(unit.unit_type, "flat")


class UnitCleanValidationTest(TestCase):
    """Cover Unit.clean coordinate validation."""

    def test_clean_raises_for_latitude_above_90(self):
        unit = UnitFactory()
        unit.latitude = Decimal("91")
        with self.assertRaises(ValidationError) as cm:
            unit.clean()
        self.assertIn("Latitude must be between -90 and 90.", str(cm.exception))

    def test_clean_raises_for_latitude_below_negative_90(self):
        unit = UnitFactory()
        unit.latitude = Decimal("-91")
        with self.assertRaises(ValidationError) as cm:
            unit.clean()
        self.assertIn("Latitude must be between -90 and 90.", str(cm.exception))

    def test_clean_raises_for_longitude_above_180(self):
        unit = UnitFactory()
        unit.longitude = Decimal("181")
        with self.assertRaises(ValidationError) as cm:
            unit.clean()
        self.assertIn("Longitude must be between -180 and 180.", str(cm.exception))

    def test_clean_raises_for_longitude_below_negative_180(self):
        unit = UnitFactory()
        unit.longitude = Decimal("-181")
        with self.assertRaises(ValidationError) as cm:
            unit.clean()
        self.assertIn("Longitude must be between -180 and 180.", str(cm.exception))

    def test_clean_passes_within_valid_ranges(self):
        unit = UnitFactory()
        unit.latitude = Decimal("19.0760")
        unit.longitude = Decimal("72.8777")
        unit.clean()  # should not raise

    def test_clean_passes_when_coordinates_are_none(self):
        unit = UnitFactory()
        unit.latitude = None
        unit.longitude = None
        unit.clean()  # should not raise


class UnitFYMethodsTest(TestCase):
    """Cover FY parsing and income/tax methods."""

    def test_rent_income_for_fy_full_year_format(self):
        unit = UnitFactory()
        renter = RenterFactory(unit=unit)
        RentRecordPaidFactory(
            unit=unit,
            renter=renter,
            paid_on=date(2024, 6, 15),
            amount=Decimal("120000"),
            status="PAID",
        )
        income = unit.rent_income_for_fy("2024-25")
        self.assertEqual(income, Decimal("120000"))

    def test_rent_income_for_fy_two_digit_end_year_rollover(self):
        unit = UnitFactory()
        renter = RenterFactory(unit=unit)
        RentRecordPaidFactory(
            unit=unit,
            renter=renter,
            paid_on=date(2025, 1, 15),
            amount=Decimal("120000"),
            status="PAID",
        )
        income = unit.rent_income_for_fy("2024-25")
        self.assertEqual(income, Decimal("120000"))

    def test_rent_income_for_fy_short_format_two_digit(self):
        unit = UnitFactory()
        renter = RenterFactory(unit=unit)
        RentRecordPaidFactory(
            unit=unit,
            renter=renter,
            paid_on=date(2023, 10, 15),
            amount=Decimal("120000"),
            status="PAID",
        )
        income = unit.rent_income_for_fy("23-24")
        self.assertEqual(income, Decimal("120000"))

    def test_rent_income_for_fy_returns_zero_when_no_records(self):
        unit = UnitFactory()
        income = unit.rent_income_for_fy("2099-00")
        self.assertEqual(income, Decimal("0"))

    def test_tax_paid_for_fy_returns_zero_when_no_records(self):
        unit = UnitFactory()
        tax = unit.tax_paid_for_fy("2099-00")
        self.assertEqual(tax, Decimal("0"))

    def test_tax_paid_for_fy_with_paid_records(self):
        unit = UnitFactory()
        building = unit.building
        PropertyTaxRecord.objects.create(
            property=building,
            amount=Decimal("15000"),
            due_date=date(2024, 3, 31),
            paid=True,
            paid_date=date(2024, 6, 15),
        )
        tax = unit.tax_paid_for_fy("2024-25")
        self.assertEqual(tax, Decimal("15000"))

    def test_net_income_for_fy(self):
        unit = UnitFactory()
        renter = RenterFactory(unit=unit)
        RentRecordPaidFactory(
            unit=unit,
            renter=renter,
            paid_on=date(2024, 6, 15),
            amount=Decimal("120000"),
            status="PAID",
        )
        building = unit.building
        PropertyTaxRecord.objects.create(
            property=building,
            amount=Decimal("15000"),
            due_date=date(2024, 3, 31),
            paid=True,
            paid_date=date(2024, 6, 15),
        )
        net = unit.net_income_for_fy("2024-25")
        self.assertEqual(net, Decimal("105000"))


class UnitDocumentCleanTest(TestCase):
    """Cover UnitDocument.clean duplicate detection."""

    def setUp(self):
        self.unit = UnitFactory()
        self.document_file = SimpleUploadedFile(
            "doc.pdf", b"document content", content_type="application/pdf"
        )

    @mock.patch("properties.utils.utils.generate_file_hash", return_value="hash1")
    def test_clean_raises_for_duplicate_document_in_same_unit(self, mock_hash):
        UnitDocument.objects.create(
            unit=self.unit,
            document=self.document_file,
            file_hash="hash1",
        )
        duplicate = UnitDocument(unit=self.unit, document=self.document_file)
        with self.assertRaises(ValidationError) as cm:
            duplicate.clean()
        self.assertIn("already exists for this unit", str(cm.exception))

    @mock.patch("properties.utils.utils.generate_file_hash", return_value="hash2")
    def test_clean_passes_for_same_hash_different_unit(self, mock_hash):
        other_unit = UnitFactory()
        UnitDocument.objects.create(
            unit=other_unit,
            document=self.document_file,
            file_hash="hash2",
        )
        new_doc = UnitDocument(unit=self.unit, document=self.document_file)
        new_doc.clean()  # should not raise

    def test_clean_skips_when_no_document(self):
        doc = UnitDocument(unit=self.unit, document=None)
        doc.clean()  # should not raise


class UnitImageCleanTest(TestCase):
    """Cover UnitImage.clean duplicate detection."""

    def setUp(self):
        self.unit = UnitFactory()
        self.image_file = SimpleUploadedFile(
            "img.jpg", b"image content", content_type="image/jpeg"
        )

    @mock.patch("properties.utils.utils.generate_file_hash", return_value="ihash1")
    def test_clean_raises_for_duplicate_image_in_same_unit(self, mock_hash):
        UnitImage.objects.create(
            unit=self.unit,
            image=self.image_file,
            image_hash="ihash1",
        )
        duplicate = UnitImage(unit=self.unit, image=self.image_file)
        with self.assertRaises(ValidationError) as cm:
            duplicate.clean()
        self.assertIn("already exists for this unit", str(cm.exception))

    @mock.patch("properties.utils.utils.generate_file_hash", return_value="ihash2")
    def test_clean_passes_for_same_hash_different_unit(self, mock_hash):
        other_unit = UnitFactory()
        UnitImage.objects.create(
            unit=other_unit,
            image=self.image_file,
            image_hash="ihash2",
        )
        new_img = UnitImage(unit=self.unit, image=self.image_file)
        new_img.clean()  # should not raise

    def test_clean_skips_when_no_image(self):
        img = UnitImage(unit=self.unit, image=None)
        img.clean()  # should not raise


class UnitVacancyStrTest(TestCase):
    """Cover UnitVacancy.__str__."""

    def test_str(self):
        unit = UnitFactory()
        vacancy = UnitVacancy.objects.create(
            unit=unit,
            reason=UnitVacancy.Reason.RENOVATION,
        )
        expected = f"{unit} - {vacancy.get_reason_display()}"
        self.assertEqual(str(vacancy), expected)


class UnitPropertiesTest(TestCase):
    """Cover Unit properties and helpers."""

    def test_name_property_uses_building_name(self):
        unit = UnitFactory()
        self.assertEqual(unit.name, unit.building_name or unit.unit)

    def test_name_property_falls_back_to_unit(self):
        unit = UnitFactory(building_name="")
        self.assertEqual(unit.name, unit.unit)

    def test_unit_number_property(self):
        unit = UnitFactory()
        self.assertEqual(unit.unit_number, unit.unit)

    def test_unit_number_setter(self):
        unit = UnitFactory()
        unit.unit_number = "NewUnit"
        unit.save()
        self.assertEqual(unit.unit, "NewUnit")

    def test_title_property(self):
        unit = UnitFactory()
        self.assertEqual(unit.title, unit.name)

    def test_rent_amount_property_returns_legacy(self):
        user = UserFactory()
        building = BuildingFactory(owner=user)
        unit = Unit(
            building=building,
            unit="RA1",
            rent_amount=Decimal("7500"),
        )
        self.assertEqual(unit.rent_amount, Decimal("7500"))

    def test_rent_amount_property_returns_zero_when_not_set(self):
        unit = Unit(unit="RA_Zero")
        self.assertEqual(unit.rent_amount, Decimal("0"))

    def test_rent_amount_setter(self):
        unit = UnitFactory()
        unit.rent_amount = Decimal("9999")
        self.assertEqual(unit._legacy_rent_amount, Decimal("9999"))

    def test_security_deposit_property_returns_legacy(self):
        user = UserFactory()
        building = BuildingFactory(owner=user)
        unit = Unit(
            building=building,
            unit="SD1",
            security_deposit=Decimal("20000"),
        )
        self.assertEqual(unit.security_deposit, Decimal("20000"))

    def test_security_deposit_setter(self):
        unit = UnitFactory()
        unit.security_deposit = Decimal("15000")
        self.assertEqual(unit._legacy_security_deposit, Decimal("15000"))

    def test_current_renter_property(self):
        unit = UnitFactory()
        renter = RenterFactory(unit=unit, status=Renter.RenterStatus.ACTIVE)
        self.assertEqual(unit.current_renter, renter)

    def test_current_renter_property_none_when_no_active(self):
        unit = UnitFactory()
        self.assertIsNone(unit.current_renter)

    def test_total_renters_property(self):
        unit = UnitFactory()
        RenterFactory(unit=unit)
        RenterFactory(unit=unit)
        self.assertEqual(unit.total_renters, 2)


class UnitFYBranchTest(TestCase):
    """Cover FY branches where end_year >= 100 (no rollover)."""

    def test_rent_income_for_fy_no_rollover(self):
        unit = UnitFactory()
        renter = RenterFactory(unit=unit)
        RentRecordPaidFactory(
            unit=unit,
            renter=renter,
            paid_on=date(2024, 6, 15),
            amount=Decimal("50000"),
            status="PAID",
        )
        income = unit.rent_income_for_fy("2024-2025")
        self.assertEqual(income, Decimal("50000"))

    def test_tax_paid_for_fy_no_rollover(self):
        unit = UnitFactory()
        building = unit.building
        PropertyTaxRecord.objects.create(
            property=building,
            amount=Decimal("8000"),
            due_date=date(2024, 3, 31),
            paid=True,
            paid_date=date(2024, 6, 15),
        )
        tax = unit.tax_paid_for_fy("2024-2025")
        self.assertEqual(tax, Decimal("8000"))


class UnitStrTest(TestCase):
    """Cover Unit.__str__ and related __str__ methods."""

    def test_unit_str(self):
        unit = UnitFactory()
        self.assertIn(unit.unit, str(unit))
        self.assertIn(unit.city, str(unit))

    def test_unit_document_str(self):
        unit = UnitFactory()
        doc = UnitDocument.objects.create(
            unit=unit,
            document="test.pdf",
        )
        self.assertIn(unit.unit, str(doc))
        self.assertIn("test.pdf", str(doc))

    def test_unit_image_str(self):
        unit = UnitFactory()
        img = UnitImage.objects.create(
            unit=unit,
            image="test.jpg",
        )
        self.assertIn(unit.unit, str(img))
        self.assertIn("Image", str(img))
