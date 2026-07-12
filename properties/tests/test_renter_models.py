"""
Comprehensive pytest tests for properties/models/renter_models.py.

Targets 95%+ statement/branch coverage for the Renter model.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from unittest import mock

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.test import TestCase

from properties.models import Renter
from tests.factories import BuildingFactory, RenterFactory, UnitFactory, UserFactory


class RenterInitTest(TestCase):
    """Cover Renter.__init__ logic branches."""

    def test_init_with_full_name_kwarg(self):
        unit = UnitFactory()
        renter = Renter(unit=unit, full_name="Full Name Renter")
        self.assertEqual(renter.name, "Full Name Renter")

    def test_init_without_args_uses_defaults(self):
        unit = UnitFactory()
        renter = Renter(unit=unit)
        self.assertEqual(renter.id_proof, "id_proof.pdf")
        self.assertEqual(renter.rent_agreement, "rent_agreement.pdf")
        self.assertEqual(renter.start_date, date.today())

    def test_init_name_not_overridden_when_already_set(self):
        unit = UnitFactory()
        renter = Renter(unit=unit, name="Original Name", full_name="Ignored Full")
        self.assertEqual(renter.name, "Original Name")

    def test_init_full_name_ignored_when_none(self):
        unit = UnitFactory()
        renter = Renter(unit=unit, full_name=None)
        self.assertEqual(renter.name, "")

    def test_init_defaults_set_only_when_not_in_kwargs(self):
        unit = UnitFactory()
        renter = Renter(
            unit=unit,
            id_proof="custom_id.pdf",
            rent_agreement="custom_agreement.pdf",
            start_date=date(2020, 1, 1),
        )
        self.assertEqual(renter.id_proof, "custom_id.pdf")
        self.assertEqual(renter.rent_agreement, "custom_agreement.pdf")
        self.assertEqual(renter.start_date, date(2020, 1, 1))

    def test_init_full_name_none_does_not_override_explicit_name(self):
        unit = UnitFactory()
        renter = Renter(unit=unit, name="Explicit Name", full_name=None)
        self.assertEqual(renter.name, "Explicit Name")


class RenterStrTest(TestCase):
    """Cover Renter.__str__."""

    def test_str_returns_name(self):
        renter = RenterFactory()
        self.assertEqual(str(renter), renter.name)

    def test_str_returns_empty_string_when_name_blank(self):
        renter = RenterFactory(name="")
        self.assertEqual(str(renter), "")


class RenterPropertyTest(TestCase):
    """Cover Renter property aliases."""

    def test_property_alias_returns_unit(self):
        renter = RenterFactory()
        self.assertEqual(renter.property, renter.unit)

    def test_full_name_property_returns_name(self):
        renter = RenterFactory()
        self.assertEqual(renter.full_name, renter.name)

    def test_full_name_setter_sets_name(self):
        renter = RenterFactory()
        renter.full_name = "New Name"
        self.assertEqual(renter.name, "New Name")

    def test_rent_agreement_pdf_returns_file(self):
        renter = RenterFactory()
        self.assertEqual(renter.rent_agreement_pdf, renter.rent_agreement)


class RenterPoliceVerificationPdfTest(TestCase):
    """Cover police_verification_pdf branches."""

    def setUp(self):
        self.unit = UnitFactory()
        self.renter = RenterFactory(unit=self.unit)

    def test_police_verification_pdf_returns_none_when_no_related(self):
        self.assertIsNone(self.renter.police_verification_pdf)

    def test_police_verification_pdf_returns_none_when_attr_is_none(self):
        with mock.patch.object(
            Renter, "policeverification", new_callable=mock.PropertyMock
        ) as mock_prop:
            mock_prop.return_value = None
            self.assertIsNone(self.renter.police_verification_pdf)

    def test_police_verification_pdf_returns_file_when_attr_set(self):
        pdf_data = b"%PDF-1.4 fake pdf"
        pdf_file = SimpleUploadedFile(
            "police.pdf", pdf_data, content_type="application/pdf"
        )
        fake_pv = mock.MagicMock()
        fake_pv.file = pdf_file
        with mock.patch.object(
            Renter, "policeverification", new_callable=mock.PropertyMock
        ) as mock_prop:
            mock_prop.return_value = fake_pv
            result = self.renter.police_verification_pdf
            self.assertEqual(result, pdf_file)


class RenterCleanValidationTest(TestCase):
    """Cover Renter.clean validation branches."""

    def setUp(self):
        self.unit = UnitFactory()

    def _make_renter(self, **kwargs):
        defaults = {
            "unit": self.unit,
            "name": "Clean Renter",
            "phone": "+919876543210",
            "rent_amount": Decimal("10000"),
            "start_date": date(2024, 1, 1),
        }
        defaults.update(kwargs)
        return Renter(**defaults)

    def test_clean_raises_when_end_date_before_start_date(self):
        renter = self._make_renter(
            start_date=date(2024, 6, 1),
            end_date=date(2024, 5, 1),
        )
        with self.assertRaises(ValidationError) as cm:
            renter.clean()
        self.assertIn("End date cannot be earlier than start date", str(cm.exception))

    def test_clean_passes_when_end_date_after_start_date(self):
        renter = self._make_renter(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
        )
        renter.clean()  # should not raise

    def test_clean_passes_when_end_date_is_none(self):
        renter = self._make_renter(start_date=date(2024, 1, 1), end_date=None)
        renter.clean()  # should not raise

    def test_clean_passes_when_status_deactivated(self):
        renter = self._make_renter(status=Renter.RenterStatus.DEACTIVATED)
        self.unit.status = "vacant"
        self.unit.save()
        renter.clean()  # should not raise since status is deactivated

    def test_clean_raises_when_active_renter_exists_same_unit(self):
        Renter.objects.create(
            unit=self.unit,
            name="First Active Renter",
            phone="+911111111111",
            rent_amount=Decimal("10000"),
            start_date=date(2024, 1, 1),
            status=Renter.RenterStatus.ACTIVE,
        )
        second = self._make_renter(status=Renter.RenterStatus.ACTIVE)
        with self.assertRaises(ValidationError) as cm:
            second.clean()
        self.assertIn(
            "already has an active or notice-period renter", str(cm.exception)
        )

    def test_clean_raises_when_notice_period_renter_exists_same_unit(self):
        Renter.objects.create(
            unit=self.unit,
            name="Notice Period Renter",
            phone="+912222222222",
            rent_amount=Decimal("10000"),
            start_date=date(2024, 1, 1),
            status=Renter.RenterStatus.NOTICE_PERIOD,
        )
        second = self._make_renter(status=Renter.RenterStatus.NOTICE_PERIOD)
        with self.assertRaises(ValidationError) as cm:
            second.clean()
        self.assertIn(
            "already has an active or notice-period renter", str(cm.exception)
        )

    def test_clean_passes_when_revoked_renter_exists_same_unit(self):
        Renter.objects.create(
            unit=self.unit,
            name="Revoked Renter",
            phone="+913333333333",
            rent_amount=Decimal("10000"),
            start_date=date(2024, 1, 1),
            status=Renter.RenterStatus.REVOKED,
        )
        second = self._make_renter(status=Renter.RenterStatus.ACTIVE)
        second.clean()  # should not raise since existing is revoked

    def test_clean_passes_when_existing_renter_is_deactivated(self):
        Renter.objects.create(
            unit=self.unit,
            name="Deactivated Renter",
            phone="+914444444444",
            rent_amount=Decimal("10000"),
            start_date=date(2024, 1, 1),
            status=Renter.RenterStatus.DEACTIVATED,
        )
        second = self._make_renter(status=Renter.RenterStatus.ACTIVE)
        second.clean()  # should not raise since existing is deactivated

    def test_clean_excludes_self_when_update_existing(self):
        renter = Renter.objects.create(
            unit=self.unit,
            name="Existing Active Renter",
            phone="+915555555555",
            rent_amount=Decimal("10000"),
            start_date=date(2024, 1, 1),
            status=Renter.RenterStatus.ACTIVE,
        )
        renter.name = "Updated Name"
        renter.clean()  # should not raise since it excludes pk=self.pk


class RenterStatusChoicesTest(TestCase):
    """Cover RenterStatus TextChoices."""

    def test_renter_status_values(self):
        self.assertEqual(Renter.RenterStatus.ACTIVE, "active")
        self.assertEqual(Renter.RenterStatus.NOTICE_PERIOD, "notice_period")
        self.assertEqual(Renter.RenterStatus.REVOKED, "revoked")
        self.assertEqual(Renter.RenterStatus.DEACTIVATED, "deactivated")

    def test_renter_status_labels(self):
        self.assertEqual(Renter.RenterStatus.ACTIVE.label, "Active")
        self.assertEqual(Renter.RenterStatus.NOTICE_PERIOD.label, "Notice Period")
        self.assertEqual(Renter.RenterStatus.REVOKED.label, "Revoked")
        self.assertEqual(Renter.RenterStatus.DEACTIVATED.label, "Deactivated")


class RenterOnboardingStatusChoicesTest(TestCase):
    """Cover OnboardingStatus and KYCStatus TextChoices."""

    def test_onboarding_status_values(self):
        self.assertEqual(Renter.OnboardingStatus.PENDING, "pending")
        self.assertEqual(Renter.OnboardingStatus.LINK_SENT, "link_sent")
        self.assertEqual(Renter.OnboardingStatus.COMPLETED, "completed")

    def test_kyc_status_values(self):
        self.assertEqual(Renter.KYCStatus.NOT_STARTED, "not_started")
        self.assertEqual(Renter.KYCStatus.IN_PROGRESS, "in_progress")
        self.assertEqual(Renter.KYCStatus.VERIFIED, "verified")
        self.assertEqual(Renter.KYCStatus.REJECTED, "rejected")


class RenterMetaTest(TestCase):
    """Cover Renter Meta options."""

    def test_unique_together_unit_phone(self):
        unit = UnitFactory()
        Renter.objects.create(
            unit=unit,
            name="Renter1",
            phone="+919876543210",
            rent_amount=Decimal("10000"),
            start_date=date(2024, 1, 1),
        )
        with self.assertRaises(IntegrityError):
            Renter.objects.create(
                unit=unit,
                name="Renter2",
                phone="+919876543210",
                rent_amount=Decimal("10000"),
                start_date=date(2024, 1, 1),
            )

    def test_ordering_by_start_date_desc(self):
        unit = UnitFactory()
        older = Renter.objects.create(
            unit=unit,
            name="Older",
            phone="+919876543211",
            rent_amount=Decimal("10000"),
            start_date=date(2024, 1, 1),
            status=Renter.RenterStatus.REVOKED,
        )
        newer = Renter.objects.create(
            unit=unit,
            name="Newer",
            phone="+919876543212",
            rent_amount=Decimal("10000"),
            start_date=date(2025, 1, 1),
            status=Renter.RenterStatus.ACTIVE,
        )
        renters = list(Renter.objects.all())
        self.assertEqual(renters[0], newer)
        self.assertEqual(renters[1], older)


class RenterDefaultValuesTest(TestCase):
    """Cover all default values set via __init__ and model defaults."""

    def test_default_id_proof_from_init(self):
        unit = UnitFactory()
        renter = Renter(unit=unit)
        self.assertEqual(renter.id_proof, "id_proof.pdf")

    def test_default_rent_agreement_from_init(self):
        unit = UnitFactory()
        renter = Renter(unit=unit)
        self.assertEqual(renter.rent_agreement, "rent_agreement.pdf")

    def test_default_start_date_is_today(self):
        unit = UnitFactory()
        renter = Renter(unit=unit)
        self.assertEqual(renter.start_date, date.today())

    def test_default_status_is_active(self):
        renter = RenterFactory()
        self.assertEqual(renter.status, Renter.RenterStatus.ACTIVE)

    def test_default_onboarding_status_is_pending(self):
        renter = RenterFactory()
        self.assertEqual(renter.onboarding_status, Renter.OnboardingStatus.PENDING)

    def test_default_kyc_status_is_not_started(self):
        renter = RenterFactory()
        self.assertEqual(renter.kyc_status, Renter.KYCStatus.NOT_STARTED)

    def test_default_is_active_is_true(self):
        renter = RenterFactory()
        self.assertTrue(renter.is_active)

    def test_default_late_payment_count_is_zero(self):
        renter = RenterFactory()
        self.assertEqual(renter.late_payment_count, 0)

    def test_default_missed_rents_is_zero(self):
        renter = RenterFactory()
        self.assertEqual(renter.missed_rents, 0)

    def test_default_is_flagged_is_false(self):
        renter = RenterFactory()
        self.assertFalse(renter.is_flagged)

    def test_default_flagged_reason_is_blank(self):
        renter = RenterFactory()
        self.assertEqual(renter.flagged_reason, "")


class RentAgreementDraftCleanTest(TestCase):
    """Cover RentAgreementDraft.clean validation branches."""

    def test_clean_raises_when_renter_unit_mismatch(self):
        owner = UserFactory()
        building = BuildingFactory(owner=owner)
        correct_unit = UnitFactory(owner=owner, building=building)
        wrong_unit = UnitFactory(owner=owner, building=building)
        renter = RenterFactory(
            unit=correct_unit, name="Draft Renter", phone="+919999999999"
        )

        from properties.models import RentAgreementDraft

        draft = RentAgreementDraft(
            user=owner,
            renter=renter,
            unit=wrong_unit,
            file=None,
        )
        with self.assertRaises(ValidationError):
            draft.clean()

    def test_clean_passes_when_renter_unit_matches(self):
        owner = UserFactory()
        building = BuildingFactory(owner=owner)
        unit = UnitFactory(owner=owner, building=building)
        renter = RenterFactory(unit=unit, name="Draft Renter2", phone="+919999999998")

        from properties.models import RentAgreementDraft

        draft = RentAgreementDraft(
            user=owner,
            renter=renter,
            unit=unit,
            file=None,
        )
        draft.clean()  # should not raise


class PoliceVerificationCleanTest(TestCase):
    """Cover PoliceVerification.clean validation branches."""

    def test_clean_raises_when_renter_unit_mismatch(self):
        owner = UserFactory()
        building = BuildingFactory(owner=owner)
        correct_unit = UnitFactory(owner=owner, building=building)
        wrong_unit = UnitFactory(owner=owner, building=building)
        renter = RenterFactory(
            unit=correct_unit, name="PV Renter", phone="+919999999997"
        )

        from properties.models import PoliceVerification

        pv = PoliceVerification(
            user=owner,
            renter=renter,
            unit=wrong_unit,
            file=None,
        )
        with self.assertRaises(ValidationError):
            pv.clean()

    def test_clean_passes_when_renter_unit_matches(self):
        owner = UserFactory()
        building = BuildingFactory(owner=owner)
        unit = UnitFactory(owner=owner, building=building)
        renter = RenterFactory(unit=unit, name="PV Renter2", phone="+919999999996")

        from properties.models import PoliceVerification

        pv = PoliceVerification(
            user=owner,
            renter=renter,
            unit=unit,
            file=None,
        )
        pv.clean()  # should not raise
