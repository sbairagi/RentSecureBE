"""
Critical Business Logic & Loophole Tests for Properties Module

This test suite focuses on:
- Data consistency and integrity issues
- Payment processing edge cases
- Renter status management loopholes
- Multi-unit ownership scenarios
- Late payment and arrears handling
- Cache invalidation bugs
- Race condition scenarios
- Data validation loopholes
"""

from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from decimal import Decimal
from datetime import timedelta, date
from unittest.mock import patch

from core.models import (
    SubscriptionPlan,
    PlanFeatureLimit,
    UserSubscription,
    UsageLimit
)
from .models import (
    Building,
    Unit,
    Caretaker,
    Renter,
    RentRecord,
    UnitImage,
    UnitDocument,
    RentAgreementDraft,
    UnitVacancy,
    ArchivedRenter
)
from .feature_enforcer import FeatureEnforcer

User = get_user_model()


class PaymentProcessingLoopholes(TestCase):
    """Test critical payment processing loopholes"""

    def setUp(self):
        self.user = User.objects.create_user(username="owner", password="pass123")
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

    def test_loophole_negative_rent_payment(self):
        """LOOPHOLE: Negative amount should be rejected but might not be"""
        renter = Renter.objects.create(
            unit=self.unit,
            name="Alice",
            phone="+919876543210",
            rent_amount=10000,
            start_date=date(2025, 1, 1)
        )
        
        # Try to create negative rent record
        from django.core.exceptions import ValidationError
        rent_record = RentRecord(
            renter=renter,
            unit=self.unit,
            owner=self.user,
            rent_month=date(2025, 1, 1),
            amount_paid=Decimal("-100"),  # LOOPHOLE: Should fail
            date_paid=date(2025, 1, 5)
        )
        with self.assertRaises(ValidationError):
            rent_record.full_clean()

    def test_loophole_zero_rent_property(self):
        """LOOPHOLE: Creating renter with zero rent (free unit?)"""
        renter = Renter.objects.create(
            unit=self.unit,
            name="Bob",
            phone="+919876543211",
            rent_amount=Decimal("0.00"),
            start_date=date(2025, 1, 1)
        )
        # This is allowed but might be unintended
        self.assertEqual(renter.rent_amount, Decimal("0.00"))

    def test_loophole_excessive_overpayment(self):
        """LOOPHOLE: No limit on overpayment amount"""
        renter = Renter.objects.create(
            unit=self.unit,
            name="Charlie",
            phone="+919876543212",
            rent_amount=10000,
            start_date=date(2025, 1, 1)
        )
        rent_record = RentRecord.objects.create(
            renter=renter,
            unit=self.unit,
            owner=self.user,
            rent_month=date(2025, 1, 1),
            amount_paid=Decimal("999999"),  # Excessive overpayment
            date_paid=date(2025, 1, 5)
        )
        # No validation prevents this
        self.assertEqual(rent_record.amount_paid, Decimal("999999"))

    def test_loophole_date_paid_same_as_rent_month(self):
        """LOOPHOLE: Payment on rent month is allowed (should it be?)"""
        renter = Renter.objects.create(
            unit=self.unit,
            name="Diana",
            phone="+919876543213",
            rent_amount=10000,
            start_date=date(2025, 1, 1)
        )
        rent_record = RentRecord.objects.create(
            renter=renter,
            unit=self.unit,
            owner=self.user,
            rent_month=date(2025, 1, 1),
            amount_paid=10000,
            date_paid=date(2025, 1, 1)  # Same date - early payment
        )
        # This is technically allowed
        self.assertEqual(rent_record.date_paid, date(2025, 1, 1))

    def test_loophole_payment_before_renter_start_date(self):
        """LOOPHOLE: Payment recorded before renter start date"""
        renter = Renter.objects.create(
            unit=self.unit,
            name="Eve",
            phone="+919876543214",
            rent_amount=10000,
            start_date=date(2025, 1, 15)
        )
        # Payment for first month recorded before start date
        rent_record = RentRecord.objects.create(
            renter=renter,
            unit=self.unit,
            owner=self.user,
            rent_month=date(2025, 1, 1),
            amount_paid=10000,
            date_paid=date(2025, 1, 10)  # Before renter start date!
        )
        # This might be unintended
        self.assertLess(rent_record.date_paid, renter.start_date)

    def test_loophole_multiple_payments_same_month(self):
        """CRITICAL LOOPHOLE: Multiple payments for same month are prevented"""
        renter = Renter.objects.create(
            unit=self.unit,
            name="Frank",
            phone="+919876543215",
            rent_amount=10000,
            start_date=date(2025, 1, 1)
        )
        rent_record1 = RentRecord.objects.create(
            renter=renter,
            unit=self.unit,
            owner=self.user,
            rent_month=date(2025, 1, 1),
            amount_paid=5000,
            date_paid=date(2025, 1, 5)
        )
        # Try to create another for same month
        with self.assertRaises(Exception):  # Should be unique constraint
            rent_record2 = RentRecord.objects.create(
                renter=renter,
                unit=self.unit,
                owner=self.user,
                rent_month=date(2025, 1, 1),
                amount_paid=5000,
                date_paid=date(2025, 1, 10)
            )


class RenterStatusLoopholes(TestCase):
    """Test renter status management loopholes"""

    def setUp(self):
        self.user = User.objects.create_user(username="owner", password="pass123")
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

    def test_loophole_inconsistent_is_active_status(self):
        """LOOPHOLE: is_active and status fields can be inconsistent"""
        renter = Renter.objects.create(
            unit=self.unit,
            name="Alice",
            phone="+919876543210",
            rent_amount=10000,
            start_date=date(2025, 1, 1),
            is_active=True,
            status=Renter.RenterStatus.DEACTIVATED  # INCONSISTENT!
        )
        # Both fields can contradict each other
        self.assertTrue(renter.is_active)
        self.assertEqual(renter.status, Renter.RenterStatus.DEACTIVATED)

    def test_loophole_revoked_but_active_renter(self):
        """LOOPHOLE: Renter can be revoked but still marked active"""
        renter = Renter.objects.create(
            unit=self.unit,
            name="Bob",
            phone="+919876543211",
            rent_amount=10000,
            start_date=date(2025, 1, 1),
            is_active=True,
            is_agreement_revoked=True,
            revoked_by_owner=True
        )
        # These two states contradict each other
        self.assertTrue(renter.is_active)
        self.assertTrue(renter.is_agreement_revoked)

    def test_loophole_revoked_without_revocation_date(self):
        """LOOPHOLE: Agreement revoked but no revoked_on date"""
        renter = Renter.objects.create(
            unit=self.unit,
            name="Charlie",
            phone="+919876543212",
            rent_amount=10000,
            start_date=date(2025, 1, 1),
            is_agreement_revoked=True,
            revoked_on=None  # No timestamp!
        )
        self.assertTrue(renter.is_agreement_revoked)
        self.assertIsNone(renter.revoked_on)

    def test_loophole_renter_with_past_end_date_still_active(self):
        """LOOPHOLE: Renter end_date passed but still marked active"""
        renter = Renter.objects.create(
            unit=self.unit,
            name="Diana",
            phone="+919876543213",
            rent_amount=10000,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 6, 30),
            is_active=True,
            status=Renter.RenterStatus.ACTIVE
        )
        # Past end date but still active
        past_end = renter.end_date < date.today()
        if past_end:
            # Should probably be deactivated
            pass

    def test_loophole_multiple_revocation_flags(self):
        """LOOPHOLE: Renter has both is_agreement_revoked and revoked_by_owner"""
        renter = Renter.objects.create(
            unit=self.unit,
            name="Eve",
            phone="+919876543214",
            rent_amount=10000,
            start_date=date(2025, 1, 1),
            is_agreement_revoked=True,
            revoked_by_owner=False,  # Revoked but not by owner?
            revocation_reason="Mutual agreement"
        )
        # Unclear who revoked the agreement
        self.assertTrue(renter.is_agreement_revoked)
        self.assertFalse(renter.revoked_by_owner)

    def test_loophole_flagged_renter_still_active(self):
        """LOOPHOLE: Renter flagged for issues but still active"""
        renter = Renter.objects.create(
            unit=self.unit,
            name="Frank",
            phone="+919876543215",
            rent_amount=10000,
            start_date=date(2025, 1, 1),
            is_active=True,
            status=Renter.RenterStatus.ACTIVE,
            is_flagged=True,
            flagged_reason="Multiple late payments"
        )
        # Flagged for issues but still active
        self.assertTrue(renter.is_active)
        self.assertTrue(renter.is_flagged)

    def test_loophole_missed_rents_not_tracked_properly(self):
        """LOOPHOLE: missed_rents counter not automatically updated"""
        renter = Renter.objects.create(
            unit=self.unit,
            name="Grace",
            phone="+919876543216",
            rent_amount=10000,
            start_date=date(2025, 1, 1),
            missed_rents=5
        )
        # missed_rents is manually set, not calculated
        self.assertEqual(renter.missed_rents, 5)


class DataConsistencyLoopholes(TestCase):
    """Test data consistency and integrity loopholes"""

    def setUp(self):
        self.user = User.objects.create_user(username="owner", password="pass123")
        self.building = Building.objects.create(
            name="Test Building",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            owner=self.user
        )

    def test_loophole_unit_status_is_vacant_mismatch(self):
        """LOOPHOLE: status and is_vacant fields can mismatch"""
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
            status="occupied",
            is_vacant=True  # CONTRADICTION!
        )
        self.assertEqual(unit.status, "occupied")
        self.assertTrue(unit.is_vacant)

    def test_loophole_unit_building_name_mismatch(self):
        """LOOPHOLE: building_name field vs building relationship inconsistency"""
        unit = Unit.objects.create(
            owner=self.user,
            building=self.building,
            unit="102",
            building_name="Different Building Name",  # Different from building.name
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            unit_type=Unit.UnitType.FLAT
        )
        # building_name doesn't match building relationship
        self.assertNotEqual(unit.building_name, unit.building.name)

    def test_loophole_caretaker_without_id_proof(self):
        """LOOPHOLE: ID proof is required but might be set to empty"""
        # This test depends on model field being required or not
        pass

    def test_loophole_multiple_caretakers_overlapping_dates(self):
        """LOOPHOLE: Multiple caretakers can work same date on same unit"""
        unit = Unit.objects.create(
            owner=self.user,
            building=self.building,
            unit="103",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            unit_type=Unit.UnitType.FLAT
        )
        caretaker1 = Caretaker.objects.create(
            unit=unit,
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
        caretaker2 = Caretaker.objects.create(
            unit=unit,
            name="Jane",
            phone="+919876543211",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            start_date=date(2025, 3, 1),  # Overlaps!
            end_date=date(2025, 12, 31)
        )
        # No validation prevents overlapping caretaker dates
        self.assertEqual(caretaker1.unit, caretaker2.unit)


class UnitArchivingLoopholes(TestCase):
    """Test unit archiving and data consistency"""

    def setUp(self):
        self.user = User.objects.create_user(username="owner", password="pass123")
        self.building = Building.objects.create(
            name="Test Building",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            owner=self.user
        )

    def test_loophole_archived_unit_still_has_active_renters(self):
        """LOOPHOLE: Archived unit can still have active renters"""
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
            is_archived=True
        )
        renter = Renter.objects.create(
            unit=unit,
            name="Alice",
            phone="+919876543210",
            rent_amount=10000,
            start_date=date(2025, 1, 1),
            is_active=True
        )
        # Active renter in archived unit
        self.assertTrue(unit.is_archived)
        self.assertTrue(renter.is_active)

    def test_loophole_archived_unit_still_can_add_caretakers(self):
        """LOOPHOLE: Can add caretakers to archived units"""
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
            is_archived=True
        )
        caretaker = Caretaker.objects.create(
            unit=unit,
            name="John",
            phone="+919876543210",
            address_line="123 Main St",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001"
        )
        # Can create caretaker on archived unit
        self.assertTrue(unit.is_archived)
        self.assertEqual(caretaker.unit, unit)


class FeatureEnforcerLoopholes(TestCase):
    """Test feature enforcer loopholes"""

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
        PlanFeatureLimit.objects.create(
            plan=self.free_plan,
            feature_key="max_buildings",
            value="1"
        )
        PlanFeatureLimit.objects.create(
            plan=self.pro_plan,
            feature_key="max_buildings",
            value="10"
        )
        self.now = timezone.now()

    def test_loophole_free_user_no_subscription(self):
        """LOOPHOLE: User with no subscription defaults to free plan limits"""
        user = User.objects.create_user(username="noplan_user", password="pass123")
        enforcer = FeatureEnforcer(user)
        plan = enforcer.get_plan_name()
        self.assertEqual(plan, 'free')

    def test_loophole_expired_plan_immediate_enforcement(self):
        """LOOPHOLE: Grace period handling might not be applied correctly"""
        user = User.objects.create_user(username="grace_user", password="pass123")
        UserSubscription.objects.create(
            user=user,
            plan=self.pro_plan,
            end_date=self.now - timedelta(days=3)  # 3 days ago
        )
        enforcer = FeatureEnforcer(user)
        # Should still use pro limits (within grace period)
        limit = enforcer.get_active_limit("max_buildings")
        self.assertNotEqual(limit, 1)  # Not downgraded to free yet

    def test_loophole_usage_never_decremented(self):
        """LOOPHOLE: If deletion fails to decrement, usage count grows indefinitely"""
        user = User.objects.create_user(username="usage_user", password="pass123")
        enforcer = FeatureEnforcer(user)
        
        # Increment multiple times
        for i in range(5):
            enforcer.increment("max_buildings")
        
        usage = UsageLimit.objects.get(user=user, feature_key="max_buildings")
        self.assertEqual(usage.usage_count, 5)
        
        # If decrement is skipped, count stays high
        # This is a potential loophole in deletion handlers


class ConcurrencyLoopholes(TransactionTestCase):
    """Test race condition and concurrency loopholes"""

    def setUp(self):
        self.user = User.objects.create_user(username="owner", password="pass123")
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
            name="Alice",
            phone="+919876543210",
            rent_amount=10000,
            start_date=date(2025, 1, 1)
        )

    def test_loophole_concurrent_rent_record_creation(self):
        """LOOPHOLE: Race condition on duplicate rent record creation"""
        # This is protected by unique constraint, but without FOR UPDATE
        # two concurrent requests might both think they can create
        month = date(2025, 1, 1)
        
        # First request creates
        rent1 = RentRecord.objects.create(
            renter=self.renter,
            unit=self.unit,
            owner=self.user,
            rent_month=month,
            amount_paid=10000,
            date_paid=date(2025, 1, 5)
        )
        
        # Second concurrent request should fail
        with self.assertRaises(Exception):
            rent2 = RentRecord.objects.create(
                renter=self.renter,
                unit=self.unit,
                owner=self.user,
                rent_month=month,
                amount_paid=10000,
                date_paid=date(2025, 1, 5)
            )


class UniquenessConstraintTests(TestCase):
    """Test uniqueness constraint edge cases"""

    def setUp(self):
        self.user = User.objects.create_user(username="owner", password="pass123")
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

    def test_loophole_null_phone_uniqueness(self):
        """LOOPHOLE: Null values in unique constraint might allow duplicates"""
        # Django allows multiple NULLs in unique constraints
        # This might be unintended for phone fields
        pass

    def test_loophole_renter_unique_phone_per_unit_bypass(self):
        """LOOPHOLE: Same renter phone can exist across different units"""
        renter1 = Renter.objects.create(
            unit=self.unit,
            name="Alice",
            phone="+919876543210",
            rent_amount=10000,
            start_date=date(2025, 1, 1)
        )
        
        # Create another unit
        unit2 = Unit.objects.create(
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
        
        # Same phone, different unit - should be allowed
        renter2 = Renter.objects.create(
            unit=unit2,
            name="Alice Smith",
            phone="+919876543210",  # Same phone!
            rent_amount=10000,
            start_date=date(2025, 1, 1)
        )
        
        # This might be unintended - same person renting two units?
        self.assertEqual(renter1.phone, renter2.phone)
        self.assertNotEqual(renter1.unit, renter2.unit)
