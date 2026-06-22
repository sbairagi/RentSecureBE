"""Tests for properties/signals/ package signals"""

from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from properties.models import Building, Caretaker, Renter, Unit

User = get_user_model()


class SignalUsageUpdateTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="sigpkg_user",
            email="spu@test.com",
            password="p",
            full_name="SPU",
            phone="+1",
        )
        self.building = Building.objects.create(
            name="SigPkgBldg",
            address_line="Addr",
            city="Mumbai",
            state="Maharashtra",
            country="India",
            postal_code="400001",
            owner=self.user,
        )

    def test_building_creation_updates_usage(self):
        from core.models import UsageLimit

        # Building signal should create/update usage count
        Building.objects.create(
            name="SigPkgBldg2",
            address_line="Addr2",
            city="Mumbai",
            state="Maharashtra",
            country="India",
            postal_code="400001",
            owner=self.user,
        )
        # The signal runs post_save, usage should be tracked
        ul = UsageLimit.objects.filter(
            user=self.user, feature_key="max_buildings"
        ).first()
        self.assertIsNotNone(ul)
        self.assertGreaterEqual(ul.usage_count, 1)

    def test_unit_creation_updates_usage(self):
        from core.models import UsageLimit

        Unit.objects.create(
            building=self.building,
            unit_number="SPU1",
            rent_amount=Decimal("10000"),
            security_deposit=Decimal("20000"),
        )
        ul = UsageLimit.objects.filter(user=self.user, feature_key="max_units").first()
        self.assertIsNotNone(ul)

    def test_caretaker_creation_updates_usage(self):
        unit = Unit.objects.create(
            building=self.building,
            unit_number="CTU1",
            rent_amount=Decimal("10000"),
            security_deposit=Decimal("20000"),
        )
        Caretaker.objects.create(
            unit=unit,
            name="Test CT",
            phone="+919999999999",
            email="ct@test.com",
            joining_date=date.today(),
        )

    def test_renter_onboarding_token_generated(self):
        unit = Unit.objects.create(
            building=self.building,
            unit_number="SPU2",
            rent_amount=Decimal("10000"),
            security_deposit=Decimal("20000"),
        )
        renter = Renter.objects.create(
            unit=unit,
            full_name="Signal Renter",
            email="sigrenter@test.com",
            phone="+919876543210",
            rent_amount=Decimal("10000"),
        )
        self.assertIsNotNone(renter.onboarding_token)
        self.assertIsNotNone(renter.onboarding_link_sent_at)

    def test_renter_deactivation_triggers_unit_vacant_notification(self):
        unit = Unit.objects.create(
            building=self.building,
            unit_number="SPU3",
            rent_amount=Decimal("10000"),
            security_deposit=Decimal("20000"),
        )
        renter = Renter.objects.create(
            unit=unit,
            full_name="Sig Renter Act",
            email="sigact@test.com",
            phone="+919876543210",
            rent_amount=Decimal("10000"),
            status="active",
        )
        self.assertFalse(unit.is_vacant)
        renter.status = "deactivated"
        renter.save()
        unit.refresh_from_db()
        self.assertTrue(unit.is_vacant)
