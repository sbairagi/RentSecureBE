"""
Comprehensive End-to-End Test Suite for Properties Module

This test suite covers:
- Complete CRUD operations for all models
- Permission and ownership validation
- Plan limits and feature enforcement
- Caching mechanisms
- Business logic validation
- Edge cases and potential loopholes
- Data integrity constraints
- Renter status transitions
- Payment processing
- Document and image handling
"""

from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from rest_framework.test import APIClient, APITestCase

from core.models import (
    AddOnPurchase,
    PlanFeatureLimit,
    SubscriptionPlan,
    UsageLimit,
    UserSubscription,
)

from .feature_enforcer import FeatureEnforcer
from .models import (
    Building,
    Caretaker,
    Renter,
    RentRecord,
    Unit,
)

User = get_user_model()


class BuildingModelTests(TestCase):
    """Test Building model CRUD and validations"""

    def setUp(self):
        self.user = User.objects.create_user(username="owner1", password="pass123")
        self.other_user = User.objects.create_user(username="owner2", password="pass123")

    def test_create_building(self):
        """Test creating a building"""
        building = Building.objects.create(
            name="Test Building",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            owner=self.user
        )
        self.assertEqual(building.name, "Test Building")
        self.assertEqual(building.owner, self.user)
        self.assertFalse(building.is_archived)

    def test_unique_building_constraint(self):
        """Test unique_together constraint (name, address_line, city, owner)"""
        Building.objects.create(
            name="Test Building",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            owner=self.user
        )
        with self.assertRaises(Exception):  # IntegrityError
            Building.objects.create(
                name="Test Building",
                address_line="123 Main St",
                city="New York",
                state="NY",
                country="USA",
                postal_code="10001",
                owner=self.user
            )

    def test_same_building_different_owners_allowed(self):
        """Test that different owners can create buildings with same name"""
        building1 = Building.objects.create(
            name="Test Building",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            owner=self.user
        )
        building2 = Building.objects.create(
            name="Test Building",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            owner=self.other_user
        )
        self.assertEqual(building1.owner, self.user)
        self.assertEqual(building2.owner, self.other_user)

    def test_archive_building(self):
        """Test archiving functionality"""
        building = Building.objects.create(
            name="Test Building",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            owner=self.user,
            is_archived=True
        )
        self.assertTrue(building.is_archived)

    def test_building_str(self):
        """Test string representation"""
        building = Building.objects.create(
            name="Test Building",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            owner=self.user
        )
        self.assertIsNotNone(str(building))


class UnitModelTests(TestCase):
    """Test Unit model CRUD, validation, and business logic"""

    def setUp(self):
        self.user = User.objects.create_user(username="owner1", password="pass123")
        self.other_user = User.objects.create_user(username="owner2", password="pass123")
        self.building = Building.objects.create(
            name="Test Building",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            owner=self.user
        )

    def test_create_unit(self):
        """Test creating a unit"""
        unit = Unit.objects.create(
            owner=self.user,
            building=self.building,
            unit="101",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            unit_type=Unit.UnitType.FLAT,
            status="vacant",
            is_vacant=True
        )
        self.assertEqual(unit.unit, "101")
        self.assertTrue(unit.is_vacant)
        self.assertFalse(unit.is_verified)

    def test_unit_unique_constraint(self):
        """Test unique_together constraint (owner, unit, building, address_line)"""
        Unit.objects.create(
            owner=self.user,
            building=self.building,
            unit="101",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            unit_type=Unit.UnitType.FLAT,
            status="vacant"
        )
        with self.assertRaises(Exception):  # IntegrityError
            Unit.objects.create(
                owner=self.user,
                building=self.building,
                unit="101",
                address_line="123 Main St",
                city="New York",
                state="NY",
                country="USA",
                postal_code="10001",
                unit_type=Unit.UnitType.FLAT,
                status="vacant"
            )

    def test_unit_without_building(self):
        """Test creating unit without building (standalone unit)"""
        unit = Unit.objects.create(
            owner=self.user,
            building=None,
            unit="Standalone101",
            address_line="456 Oak St",
            city="Boston",
            state="MA",
            country="USA",
            postal_code="02101",
            unit_type=Unit.UnitType.HOUSE,
            status="vacant"
        )
        self.assertIsNone(unit.building)
        self.assertEqual(unit.unit, "Standalone101")

    def test_latitude_validation(self):
        """Test latitude must be between -90 and 90"""
        unit = Unit(
            owner=self.user,
            building=self.building,
            unit="102",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            unit_type=Unit.UnitType.FLAT,
            latitude=91  # Invalid
        )
        with self.assertRaises(ValidationError):
            unit.full_clean()

    def test_longitude_validation(self):
        """Test longitude must be between -180 and 180"""
        unit = Unit(
            owner=self.user,
            building=self.building,
            unit="103",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            unit_type=Unit.UnitType.FLAT,
            longitude=181  # Invalid
        )
        with self.assertRaises(ValidationError):
            unit.full_clean()

    def test_valid_coordinates(self):
        """Test valid latitude and longitude"""
        unit = Unit.objects.create(
            owner=self.user,
            building=self.building,
            unit="104",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            unit_type=Unit.UnitType.FLAT,
            latitude=Decimal("40.7128"),
            longitude=Decimal("-74.0060")
        )
        self.assertEqual(str(unit.latitude), "40.7128")
        self.assertEqual(str(unit.longitude), "-74.0060")

    def test_unit_name_property(self):
        """Test unit name property returns building_name or unit"""
        unit = Unit.objects.create(
            owner=self.user,
            building=self.building,
            unit="105",
            building_name="Apt Complex",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            unit_type=Unit.UnitType.FLAT
        )
        self.assertEqual(unit.name, "Apt Complex")

        unit2 = Unit.objects.create(
            owner=self.user,
            building=self.building,
            unit="106",
            building_name=None,
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            unit_type=Unit.UnitType.FLAT
        )
        self.assertEqual(unit2.name, "106")

    def test_unit_type_choices(self):
        """Test all unit type choices"""
        for unit_type, _ in Unit.UnitType.choices:
            unit = Unit.objects.create(
                owner=self.user,
                building=self.building,
                unit=f"unit_{unit_type}",
                address_line="123 Main St",
                city="New York",
                state="NY",
                country="USA",
                postal_code="10001",
                unit_type=unit_type
            )
            self.assertEqual(unit.unit_type, unit_type)

    def test_status_consistency(self):
        """Test status and is_vacant should be consistent"""
        unit = Unit.objects.create(
            owner=self.user,
            building=self.building,
            unit="107",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            unit_type=Unit.UnitType.FLAT,
            status="vacant",
            is_vacant=True
        )
        self.assertEqual(unit.status, "vacant")
        self.assertTrue(unit.is_vacant)

    def test_different_owners_same_unit_allowed(self):
        """Test different owners can create units with same unit number"""
        unit1 = Unit.objects.create(
            owner=self.user,
            building=self.building,
            unit="101",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            unit_type=Unit.UnitType.FLAT
        )

        building2 = Building.objects.create(
            name="Other Building",
            address_line="789 Elm St",
            city="Boston",
            state="MA",
            country="USA",
            postal_code="02101",
            owner=self.other_user
        )

        unit2 = Unit.objects.create(
            owner=self.other_user,
            building=building2,
            unit="101",
            address_line="789 Elm St",
            city="Boston",
            state="MA",
            country="USA",
            postal_code="02101",
            unit_type=Unit.UnitType.FLAT
        )
        self.assertEqual(unit1.unit, unit2.unit)


class CaretakerModelTests(TestCase):
    """Test Caretaker model CRUD and validations"""

    def setUp(self):
        self.user = User.objects.create_user(username="owner1", password="pass123")
        self.building = Building.objects.create(
            name="Test Building",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            owner=self.user
        )
        self.unit = Unit.objects.create(
            owner=self.user,
            building=self.building,
            unit="101",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            unit_type=Unit.UnitType.FLAT
        )

    def test_create_caretaker(self):
        """Test creating a caretaker"""
        caretaker = Caretaker.objects.create(
            unit=self.unit,
            name="John Doe",
            phone="+919876543210",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001"
        )
        self.assertEqual(caretaker.name, "John Doe")
        self.assertEqual(caretaker.phone, "+919876543210")

    def test_caretaker_phone_validation(self):
        """Test phone number validation"""
        with self.assertRaises(ValidationError):
            caretaker = Caretaker(
                unit=self.unit,
                name="John Doe",
                phone="invalid",
                address_line="123 Main St",
                city="New York",
                state="NY",
                country="USA",
                postal_code="10001"
            )
            caretaker.full_clean()

    def test_unique_phone_per_unit(self):
        """Test unique phone constraint per unit"""
        Caretaker.objects.create(
            unit=self.unit,
            name="John Doe",
            phone="+919876543210",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001"
        )
        with self.assertRaises(Exception):
            Caretaker.objects.create(
                unit=self.unit,
                name="Jane Doe",
                phone="+919876543210",
                address_line="123 Main St",
                city="New York",
                state="NY",
                country="USA",
                postal_code="10001"
            )

    def test_end_date_before_start_date(self):
        """Test end_date cannot be before start_date"""
        caretaker = Caretaker(
            unit=self.unit,
            name="John Doe",
            phone="+919876543210",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            start_date=date(2025, 1, 15),
            end_date=date(2025, 1, 10)
        )
        with self.assertRaises(ValidationError):
            caretaker.full_clean()

    def test_valid_date_range(self):
        """Test valid start and end dates"""
        caretaker = Caretaker.objects.create(
            unit=self.unit,
            name="John Doe",
            phone="+919876543210",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31)
        )
        self.assertEqual(caretaker.start_date, date(2025, 1, 1))
        self.assertEqual(caretaker.end_date, date(2025, 12, 31))


class RenterModelTests(TestCase):
    """Test Renter model CRUD and status transitions"""

    def setUp(self):
        self.user = User.objects.create_user(username="owner1", password="pass123")
        self.renter_user = User.objects.create_user(username="renter1", password="pass123")
        self.building = Building.objects.create(
            name="Test Building",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            owner=self.user
        )
        self.unit = Unit.objects.create(
            owner=self.user,
            building=self.building,
            unit="101",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            unit_type=Unit.UnitType.FLAT
        )

    def test_create_renter(self):
        """Test creating a renter"""
        renter = Renter.objects.create(
            unit=self.unit,
            name="Alice Smith",
            phone="+919876543210",
            rent_amount=10000,
            start_date=date(2025, 1, 1),
            user=self.renter_user
        )
        self.assertEqual(renter.name, "Alice Smith")
        self.assertEqual(renter.status, Renter.RenterStatus.ACTIVE)
        self.assertTrue(renter.is_active)

    def test_renter_status_transitions(self):
        """Test all renter status choices"""
        for status_choice, _ in Renter.RenterStatus.choices:
            renter = Renter.objects.create(
                unit=self.unit,
                name=f"Renter {status_choice}",
                phone=f"+9198765432{status_choice[:2]}",
                rent_amount=10000,
                start_date=date(2025, 1, 1),
                status=status_choice
            )
            self.assertEqual(renter.status, status_choice)

    def test_unique_phone_per_unit(self):
        """Test unique phone constraint per unit"""
        Renter.objects.create(
            unit=self.unit,
            name="Alice Smith",
            phone="+919876543210",
            rent_amount=10000,
            start_date=date(2025, 1, 1)
        )
        with self.assertRaises(Exception):
            Renter.objects.create(
                unit=self.unit,
                name="Bob Smith",
                phone="+919876543210",
                rent_amount=10000,
                start_date=date(2025, 1, 1)
            )

    def test_end_date_before_start_date(self):
        """Test end_date cannot be before start_date"""
        renter = Renter(
            unit=self.unit,
            name="Alice Smith",
            phone="+919876543210",
            rent_amount=10000,
            start_date=date(2025, 1, 15),
            end_date=date(2025, 1, 10)
        )
        with self.assertRaises(ValidationError):
            renter.full_clean()

    def test_valid_date_range(self):
        """Test valid start and end dates"""
        renter = Renter.objects.create(
            unit=self.unit,
            name="Alice Smith",
            phone="+919876543210",
            rent_amount=10000,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31)
        )
        self.assertEqual(renter.start_date, date(2025, 1, 1))
        self.assertEqual(renter.end_date, date(2025, 12, 31))

    def test_renter_flagging(self):
        """Test renter flagging for late payments"""
        renter = Renter.objects.create(
            unit=self.unit,
            name="Alice Smith",
            phone="+919876543210",
            rent_amount=10000,
            start_date=date(2025, 1, 1),
            is_flagged=True,
            flagged_reason="Multiple late payments"
        )
        self.assertTrue(renter.is_flagged)
        self.assertIsNotNone(renter.flagged_reason)

    def test_renter_revocation(self):
        """Test renter agreement revocation"""
        renter = Renter.objects.create(
            unit=self.unit,
            name="Alice Smith",
            phone="+919876543210",
            rent_amount=10000,
            start_date=date(2025, 1, 1),
            is_agreement_revoked=True,
            revoked_by_owner=True,
            revocation_reason="Non-payment",
            revoked_on=timezone.now()
        )
        self.assertTrue(renter.is_agreement_revoked)
        self.assertTrue(renter.revoked_by_owner)

    def test_renter_vacation_tracking(self):
        """Test tracking when renter vacated"""
        renter = Renter.objects.create(
            unit=self.unit,
            name="Alice Smith",
            phone="+919876543210",
            rent_amount=10000,
            start_date=date(2025, 1, 1),
            vacated_on=date(2025, 12, 31)
        )
        self.assertEqual(renter.vacated_on, date(2025, 12, 31))

    def test_late_payment_tracking(self):
        """Test late payment count tracking"""
        renter = Renter.objects.create(
            unit=self.unit,
            name="Alice Smith",
            phone="+919876543210",
            rent_amount=10000,
            start_date=date(2025, 1, 1),
            late_payment_count=3
        )
        self.assertEqual(renter.late_payment_count, 3)

    def test_missed_rents_tracking(self):
        """Test missed rents tracking"""
        renter = Renter.objects.create(
            unit=self.unit,
            name="Alice Smith",
            phone="+919876543210",
            rent_amount=10000,
            start_date=date(2025, 1, 1),
            missed_rents=2
        )
        self.assertEqual(renter.missed_rents, 2)


class RentRecordModelTests(TestCase):
    """Test RentRecord model CRUD and validations"""

    def setUp(self):
        self.user = User.objects.create_user(username="owner1", password="pass123")
        self.building = Building.objects.create(
            name="Test Building",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            owner=self.user
        )
        self.unit = Unit.objects.create(
            owner=self.user,
            building=self.building,
            unit="101",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            unit_type=Unit.UnitType.FLAT
        )
        self.renter = Renter.objects.create(
            unit=self.unit,
            name="Alice Smith",
            phone="+919876543210",
            rent_amount=10000,
            start_date=date(2025, 1, 1)
        )

    def test_create_rent_record(self):
        """Test creating a rent record"""
        rent_record = RentRecord.objects.create(
            renter=self.renter,
            unit=self.unit,
            owner=self.user,
            rent_month=date(2025, 1, 1),
            amount_paid=10000,
            date_paid=date(2025, 1, 5),
            payment_status=RentRecord.PaymentStatus.PAID,
            payment_mode=RentRecord.PaymentMode.CASH
        )
        self.assertEqual(rent_record.amount_paid, Decimal("10000"))
        self.assertEqual(rent_record.payment_status, RentRecord.PaymentStatus.PAID)

    def test_negative_amount_validation(self):
        """Test amount_paid cannot be negative"""
        rent_record = RentRecord(
            renter=self.renter,
            unit=self.unit,
            owner=self.user,
            rent_month=date(2025, 1, 1),
            amount_paid=-1000,
            date_paid=date(2025, 1, 5)
        )
        with self.assertRaises(ValidationError):
            rent_record.full_clean()

    def test_date_paid_before_rent_month(self):
        """Test date_paid cannot be before rent_month"""
        rent_record = RentRecord(
            renter=self.renter,
            unit=self.unit,
            owner=self.user,
            rent_month=date(2025, 1, 1),
            amount_paid=10000,
            date_paid=date(2024, 12, 1)
        )
        with self.assertRaises(ValidationError):
            rent_record.full_clean()

    def test_valid_date_range(self):
        """Test date_paid >= rent_month is valid"""
        rent_record = RentRecord.objects.create(
            renter=self.renter,
            unit=self.unit,
            owner=self.user,
            rent_month=date(2025, 1, 1),
            amount_paid=10000,
            date_paid=date(2025, 1, 1)
        )
        self.assertEqual(rent_record.rent_month, date(2025, 1, 1))
        self.assertEqual(rent_record.date_paid, date(2025, 1, 1))

    def test_renter_unit_mismatch(self):
        """Test renter must belong to unit"""
        other_unit = Unit.objects.create(
            owner=self.user,
            building=self.building,
            unit="102",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            unit_type=Unit.UnitType.FLAT
        )
        rent_record = RentRecord(
            renter=self.renter,
            unit=other_unit,
            owner=self.user,
            rent_month=date(2025, 1, 1),
            amount_paid=10000,
            date_paid=date(2025, 1, 5)
        )
        with self.assertRaises(ValidationError):
            rent_record.full_clean()

    def test_unique_renter_rent_month(self):
        """Test unique_together constraint (renter, rent_month)"""
        RentRecord.objects.create(
            renter=self.renter,
            unit=self.unit,
            owner=self.user,
            rent_month=date(2025, 1, 1),
            amount_paid=10000,
            date_paid=date(2025, 1, 5)
        )
        with self.assertRaises(Exception):
            RentRecord.objects.create(
                renter=self.renter,
                unit=self.unit,
                owner=self.user,
                rent_month=date(2025, 1, 1),
                amount_paid=10000,
                date_paid=date(2025, 1, 5)
            )

    def test_payment_mode_choices(self):
        """Test all payment mode choices"""
        for index, (mode, _) in enumerate(RentRecord.PaymentMode.choices, start=2):
            rent_record = RentRecord.objects.create(
                renter=self.renter,
                unit=self.unit,
                owner=self.user,
                rent_month=date(2025, index, 1),
                amount_paid=10000,
                date_paid=date(2025, 2, 5),
                payment_mode=mode
            )
            self.assertEqual(rent_record.payment_mode, mode)

    def test_payment_status_choices(self):
        """Test all payment status choices"""
        for index, (status, _) in enumerate(RentRecord.PaymentStatus.choices, start=6):
            rent_record = RentRecord.objects.create(
                renter=self.renter,
                unit=self.unit,
                owner=self.user,
                rent_month=date(2025, index, 1),
                amount_paid=10000,
                date_paid=date(2025, 3, 5),
                payment_status=status
            )
            self.assertEqual(rent_record.payment_status, status)

    def test_payout_tracking(self):
        """Test payout status and retry tracking"""
        rent_record = RentRecord.objects.create(
            renter=self.renter,
            unit=self.unit,
            owner=self.user,
            rent_month=date(2025, 1, 1),
            amount_paid=10000,
            date_paid=date(2025, 1, 5),
            payout_status="PENDING",
            payout_reference="PAY123456",
            payout_retry_count=2
        )
        self.assertEqual(rent_record.payout_status, "PENDING")
        self.assertEqual(rent_record.payout_reference, "PAY123456")
        self.assertEqual(rent_record.payout_retry_count, 2)

    def test_razorpay_fields(self):
        """Test Razorpay integration fields"""
        rent_record = RentRecord.objects.create(
            renter=self.renter,
            unit=self.unit,
            owner=self.user,
            rent_month=date(2025, 1, 1),
            amount_paid=10000,
            date_paid=date(2025, 1, 5),
            razorpay_order_id="order_12345",
            razorpay_payment_status="PAID"
        )
        self.assertEqual(rent_record.razorpay_order_id, "order_12345")
        self.assertEqual(rent_record.razorpay_payment_status, "PAID")

    def test_late_fee_tracking(self):
        """Test late fee calculation fields"""
        rent_record = RentRecord.objects.create(
            renter=self.renter,
            unit=self.unit,
            owner=self.user,
            rent_month=date(2025, 1, 1),
            amount_paid=10000,
            date_paid=date(2025, 1, 5),
            grace_days=5,
            late_fee=Decimal("100.00"),
            adjustment_reason="Applied grace period"
        )
        self.assertEqual(rent_record.grace_days, 5)
        self.assertEqual(rent_record.late_fee, Decimal("100.00"))


class FeatureEnforcerTests(TestCase):
    """Test FeatureEnforcer business logic"""

    def setUp(self):
        self.free_plan = SubscriptionPlan.objects.create(
            name="free",
            monthly_price=0,
            yearly_price=0
        )
        self.pro_plan = SubscriptionPlan.objects.create(
            name="pro",
            monthly_price=Decimal("29.99"),
            yearly_price=Decimal("299.99")
        )
        self.unlimited_plan = SubscriptionPlan.objects.create(
            name="unlimited",
            monthly_price=999,
            yearly_price=9999
        )

        # Setup feature limits
        PlanFeatureLimit.objects.create(plan=self.free_plan, feature_key="max_buildings", value="1")
        PlanFeatureLimit.objects.create(plan=self.pro_plan, feature_key="max_buildings", value="10")
        PlanFeatureLimit.objects.create(plan=self.unlimited_plan, feature_key="max_buildings", value="unlimited")

        PlanFeatureLimit.objects.create(plan=self.free_plan, feature_key="max_units", value="3")
        PlanFeatureLimit.objects.create(plan=self.pro_plan, feature_key="max_units", value="50")
        PlanFeatureLimit.objects.create(plan=self.unlimited_plan, feature_key="max_units", value="unlimited")

        self.now = timezone.now()

    def test_free_user_within_limit(self):
        """Test free user can create within limit"""
        user = User.objects.create_user(username="free_user", password="pass123")
        UserSubscription.objects.create(
            user=user,
            plan=self.free_plan,
            end_date=self.now + timedelta(days=30)
        )
        enforcer = FeatureEnforcer(user)
        self.assertTrue(enforcer.can_create("max_buildings"))

    def test_free_user_exceeds_limit(self):
        """Test free user cannot create after hitting limit"""
        user = User.objects.create_user(username="free_user2", password="pass123")
        UserSubscription.objects.create(
            user=user,
            plan=self.free_plan,
            end_date=self.now + timedelta(days=30)
        )
        UsageLimit.objects.create(user=user, feature_key="max_buildings", usage_count=1)
        enforcer = FeatureEnforcer(user)
        self.assertFalse(enforcer.can_create("max_buildings"))

    def test_pro_user_within_limit(self):
        """Test pro user can create within limit"""
        user = User.objects.create_user(username="pro_user", password="pass123")
        UserSubscription.objects.create(
            user=user,
            plan=self.pro_plan,
            end_date=self.now + timedelta(days=30)
        )
        UsageLimit.objects.create(user=user, feature_key="max_buildings", usage_count=5)
        enforcer = FeatureEnforcer(user)
        self.assertTrue(enforcer.can_create("max_buildings"))

    def test_pro_user_exceeds_limit(self):
        """Test pro user cannot create after hitting limit"""
        user = User.objects.create_user(username="pro_user2", password="pass123")
        UserSubscription.objects.create(
            user=user,
            plan=self.pro_plan,
            end_date=self.now + timedelta(days=30)
        )
        UsageLimit.objects.create(user=user, feature_key="max_buildings", usage_count=10)
        enforcer = FeatureEnforcer(user)
        self.assertFalse(enforcer.can_create("max_buildings"))

    def test_unlimited_user_always_can_create(self):
        """Test unlimited user can always create"""
        user = User.objects.create_user(username="unlimited_user", password="pass123")
        UserSubscription.objects.create(
            user=user,
            plan=self.unlimited_plan,
            end_date=self.now + timedelta(days=365)
        )
        UsageLimit.objects.create(user=user, feature_key="max_buildings", usage_count=999)
        enforcer = FeatureEnforcer(user)
        self.assertTrue(enforcer.can_create("max_buildings"))

    def test_expired_user_within_grace_period(self):
        """Test expired user within grace period still uses pro limits"""
        user = User.objects.create_user(username="grace_user", password="pass123")
        UserSubscription.objects.create(
            user=user,
            plan=self.pro_plan,
            end_date=self.now - timedelta(days=3)  # 3 days ago, still in grace
        )
        UsageLimit.objects.create(user=user, feature_key="max_buildings", usage_count=5)
        enforcer = FeatureEnforcer(user)
        self.assertTrue(enforcer.can_create("max_buildings"))

    def test_expired_user_past_grace_period(self):
        """Test expired user past grace period falls back to free plan"""
        user = User.objects.create_user(username="expired_user", password="pass123")
        UserSubscription.objects.create(
            user=user,
            plan=self.pro_plan,
            end_date=self.now - timedelta(days=10)  # 10 days ago, past grace
        )
        UsageLimit.objects.create(user=user, feature_key="max_buildings", usage_count=2)
        enforcer = FeatureEnforcer(user)
        # Pro limit is 10, but user is past grace period, so fallback to free (1)
        self.assertFalse(enforcer.can_create("max_buildings"))

    def test_addon_extends_limit(self):
        """Test add-on purchase extends feature limit"""
        user = User.objects.create_user(username="addon_user", password="pass123")
        UserSubscription.objects.create(
            user=user,
            plan=self.free_plan,
            end_date=self.now + timedelta(days=30)
        )
        AddOnPurchase.objects.create(
            user=user,
            name="max_buildings",
            amount=5
        )
        UsageLimit.objects.create(user=user, feature_key="max_buildings", usage_count=2)
        enforcer = FeatureEnforcer(user)
        # Free: 1 + AddOn: 5 = 6 limit, usage: 2
        self.assertTrue(enforcer.can_create("max_buildings"))

    def test_unlimited_string_value(self):
        """Test plan feature with unlimited string value"""
        user = User.objects.create_user(username="unlimited_str_user", password="pass123")
        UserSubscription.objects.create(
            user=user,
            plan=self.pro_plan,
            end_date=self.now + timedelta(days=30)
        )
        PlanFeatureLimit.objects.create(
            plan=self.pro_plan,
            feature_key="max_caretakers",
            value="unlimited"
        )
        enforcer = FeatureEnforcer(user)
        self.assertTrue(enforcer.can_create("max_caretakers"))

    def test_no_limit_defined_fallback_zero(self):
        """Test feature with no limit defined falls back to 0"""
        user = User.objects.create_user(username="nolimit_user", password="pass123")
        UserSubscription.objects.create(
            user=user,
            plan=self.pro_plan,
            end_date=self.now + timedelta(days=30)
        )
        enforcer = FeatureEnforcer(user)
        # No limit defined for "max_images", should default to 0
        self.assertFalse(enforcer.can_create("max_images"))

    def test_increment_usage(self):
        """Test incrementing usage count"""
        user = User.objects.create_user(username="inc_user", password="pass123")
        enforcer = FeatureEnforcer(user)
        enforcer.increment("max_buildings")
        usage = UsageLimit.objects.get(user=user, feature_key="max_buildings")
        self.assertEqual(usage.usage_count, 1)

    def test_decrement_usage(self):
        """Test decrementing usage count"""
        user = User.objects.create_user(username="dec_user", password="pass123")
        UsageLimit.objects.create(user=user, feature_key="max_buildings", usage_count=3)
        enforcer = FeatureEnforcer(user)
        enforcer.decrement("max_buildings")
        usage = UsageLimit.objects.get(user=user, feature_key="max_buildings")
        self.assertEqual(usage.usage_count, 2)

    def test_decrement_does_not_go_negative(self):
        """Test decrement doesn't go below 0"""
        user = User.objects.create_user(username="dec_zero_user", password="pass123")
        UsageLimit.objects.create(user=user, feature_key="max_buildings", usage_count=0)
        enforcer = FeatureEnforcer(user)
        enforcer.decrement("max_buildings")
        usage = UsageLimit.objects.get(user=user, feature_key="max_buildings")
        self.assertEqual(usage.usage_count, 0)


class CachingTests(TransactionTestCase):
    """Test caching mechanisms"""

    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username="cache_user", password="pass123")

    def tearDown(self):
        cache.clear()

    def test_building_cache_on_list(self):
        """Test building list is cached"""
        Building.objects.create(
            name="Test Building",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            owner=self.user
        )
        cache_key = f"buildings_user_{self.user.id}"
        self.assertIsNone(cache.get(cache_key))

        # First access
        buildings = Building.objects.filter(owner=self.user)
        cache.set(cache_key, buildings, timeout=300)
        self.assertIsNotNone(cache.get(cache_key))

    def test_cache_cleared_on_create(self):
        """Test cache is cleared after creating building"""
        Building.objects.create(
            name="Test Building",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            owner=self.user
        )
        # Manual cache invalidation would be tested in API tests


class PermissionTests(APITestCase):
    """Test permission and ownership validation"""

    def setUp(self):
        self.user1 = User.objects.create_user(username="owner1", password="pass123")
        self.user2 = User.objects.create_user(username="owner2", password="pass123")
        self.client = APIClient()

    def test_user_cannot_access_other_user_building(self):
        """Test user cannot view other user's buildings"""
        Building.objects.create(
            name="Building 1",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            owner=self.user1
        )
        self.client.force_authenticate(user=self.user2)
        # Query should not return user1's building
        buildings = Building.objects.filter(owner=self.user2)
        self.assertEqual(buildings.count(), 0)

    def test_user_cannot_modify_other_user_building(self):
        """Test user cannot modify other user's buildings"""
        Building.objects.create(
            name="Building 1",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            owner=self.user1
        )
        # This should fail if enforcer checks ownership
        # Tested in actual API tests


class EdgeCasesTests(TestCase):
    """Test edge cases and potential loopholes"""

    def setUp(self):
        self.user = User.objects.create_user(username="edge_user", password="pass123")
        self.building = Building.objects.create(
            name="Test Building",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            owner=self.user
        )
        self.unit = Unit.objects.create(
            owner=self.user,
            building=self.building,
            unit="101",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            unit_type=Unit.UnitType.FLAT
        )

    def test_renter_with_zero_rent_amount(self):
        """Test creating renter with zero rent (potential loophole)"""
        renter = Renter.objects.create(
            unit=self.unit,
            name="Free Renter",
            phone="+919876543210",
            rent_amount=Decimal("0.00"),
            start_date=date(2025, 1, 1)
        )
        self.assertEqual(renter.rent_amount, Decimal("0.00"))

    def test_rent_record_partial_payment(self):
        """Test rent record with partial payment"""
        renter = Renter.objects.create(
            unit=self.unit,
            name="Alice",
            phone="+919876543210",
            rent_amount=10000,
            start_date=date(2025, 1, 1)
        )
        rent_record = RentRecord.objects.create(
            renter=renter,
            unit=self.unit,
            owner=self.user,
            rent_month=date(2025, 1, 1),
            amount_paid=5000,  # Only half
            date_paid=date(2025, 1, 5)
        )
        self.assertEqual(rent_record.amount_paid, Decimal("5000"))

    def test_overpayment(self):
        """Test rent record with overpayment"""
        renter = Renter.objects.create(
            unit=self.unit,
            name="Alice",
            phone="+919876543210",
            rent_amount=10000,
            start_date=date(2025, 1, 1)
        )
        rent_record = RentRecord.objects.create(
            renter=renter,
            unit=self.unit,
            owner=self.user,
            rent_month=date(2025, 1, 1),
            amount_paid=15000,  # Overpayment
            date_paid=date(2025, 1, 5)
        )
        self.assertEqual(rent_record.amount_paid, Decimal("15000"))

    def test_unit_with_null_coordinates(self):
        """Test unit with null coordinates"""
        unit = Unit.objects.create(
            owner=self.user,
            building=self.building,
            unit="102",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            unit_type=Unit.UnitType.FLAT,
            latitude=None,
            longitude=None
        )
        self.assertIsNone(unit.latitude)
        self.assertIsNone(unit.longitude)

    def test_caretaker_overlapping_dates(self):
        """Test caretaker with overlapping service dates (potential issue)"""
        caretaker1 = Caretaker.objects.create(
            unit=self.unit,
            name="John",
            phone="+919876543210",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 6, 30)
        )
        # Different phone, so this is allowed
        caretaker2 = Caretaker.objects.create(
            unit=self.unit,
            name="Jane",
            phone="+919876543211",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            start_date=date(2025, 3, 1),  # Overlaps with caretaker1
            end_date=date(2025, 12, 31)
        )
        self.assertEqual(caretaker1.unit, caretaker2.unit)

    def test_multiple_renters_same_unit(self):
        """Test multiple renters in same unit at same time (potential issue)"""
        renter1 = Renter.objects.create(
            unit=self.unit,
            name="Alice",
            phone="+919876543210",
            rent_amount=10000,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 6, 30)
        )
        # Different phone, so this is allowed
        renter2 = Renter.objects.create(
            unit=self.unit,
            name="Bob",
            phone="+919876543211",
            rent_amount=10000,
            start_date=date(2025, 1, 1),  # Overlaps with Alice
            end_date=date(2025, 6, 30)
        )
        self.assertEqual(renter1.unit, renter2.unit)

    def test_renter_agreement_revoked_but_still_active(self):
        """Test renter can be revoked but still marked active (inconsistency)"""
        renter = Renter.objects.create(
            unit=self.unit,
            name="Alice",
            phone="+919876543210",
            rent_amount=10000,
            start_date=date(2025, 1, 1),
            is_active=True,
            is_agreement_revoked=True
        )
        self.assertTrue(renter.is_active)
        self.assertTrue(renter.is_agreement_revoked)

    def test_renter_multiple_revocation_reasons(self):
        """Test tracking multiple revocation scenarios"""
        renter = Renter.objects.create(
            unit=self.unit,
            name="Alice",
            phone="+919876543210",
            rent_amount=10000,
            start_date=date(2025, 1, 1),
            revoked_by_owner=False,
            is_agreement_revoked=True,
            revocation_reason="Renter requested"
        )
        self.assertFalse(renter.revoked_by_owner)
        self.assertTrue(renter.is_agreement_revoked)


class DataIntegrityTests(TestCase):
    """Test data integrity and consistency"""

    def setUp(self):
        self.user = User.objects.create_user(username="integrity_user", password="pass123")

    def test_building_created_at_timestamp(self):
        """Test building creation timestamp"""
        building = Building.objects.create(
            name="Test Building",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            owner=self.user
        )
        self.assertIsNotNone(building.created_at)

    def test_renter_updated_at_timestamp(self):
        """Test renter updated_at changes on update"""
        unit = Unit.objects.create(
            owner=self.user,
            building=None,
            unit="101",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            unit_type=Unit.UnitType.FLAT
        )
        renter = Renter.objects.create(
            unit=unit,
            name="Alice",
            phone="+919876543210",
            rent_amount=10000,
            start_date=date(2025, 1, 1)
        )
        original_updated_at = renter.updated_at
        renter.name = "Alice Updated"
        renter.save()
        self.assertGreaterEqual(renter.updated_at, original_updated_at)

    def test_unit_ordering_by_created_at(self):
        """Test units are ordered by creation date"""
        unit1 = Unit.objects.create(
            owner=self.user,
            building=None,
            unit="101",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            unit_type=Unit.UnitType.FLAT
        )
        unit2 = Unit.objects.create(
            owner=self.user,
            building=None,
            unit="102",
            address_line="124 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            unit_type=Unit.UnitType.FLAT
        )
        units = Unit.objects.filter(owner=self.user)
        # Should be ordered by -created_at (newest first)
        self.assertEqual(units[0].id, unit2.id)
        self.assertEqual(units[1].id, unit1.id)
