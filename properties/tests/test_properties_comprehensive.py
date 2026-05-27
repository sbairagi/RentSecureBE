"""
Comprehensive tests for properties app covering models, serializers, views, signals, services, and utils.
"""
from decimal import Decimal
from datetime import date, timedelta
from unittest.mock import patch, MagicMock

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIRequestFactory, APIClient, force_authenticate

from core.models import SubscriptionPlan, UserSubscription, PlanFeatureLimit, AddOnPurchase, UsageLimit
from properties.models import (
    Building, Unit, Caretaker, Renter, RentRecord, ExtraCharge,
    PropertyTaxRecord, RentAgreementDraft, UnitDocument, UnitImage,
    ArchivedRenter, AgreementRevocationLog, PoliceVerification
)
from properties.feature_enforcer import FeatureEnforcer
from properties.services.unit_service import update_unit_status, get_building_analytics, get_owner_analytics
from properties.utils.onboarding_utils import (
    generate_onboarding_token, generate_onboarding_link,
    verify_onboarding_token, mark_onboarding_completed, mark_kyc_verified
)

User = get_user_model()


class BuildingModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='building_owner', email='bo@test.com',
            password='p', full_name='BO', phone='+1'
        )
        self.building = Building.objects.create(
            name='Test Building', address_line='123 Main St',
            city='Mumbai', state='Maharashtra', country='India',
            postal_code='400001', owner=self.user
        )

    def test_building_creation(self):
        self.assertEqual(self.building.name, 'Test Building')
        self.assertEqual(self.building.owner, self.user)

    def test_building_str(self):
        self.assertIn('Test Building', str(self.building))

    def test_building_defaults(self):
        self.assertFalse(self.building.is_archived)

    def test_building_units_count(self):
        self.assertEqual(self.building.units_count, 0)

    def test_building_occupied_units_count(self):
        self.assertEqual(self.building.occupied_units_count, 0)


class UnitModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='unit_owner', email='uo@test.com',
            password='p', full_name='UO', phone='+1'
        )
        self.building = Building.objects.create(
            name='B1', address_line='Addr', city='Mumbai',
            state='Maharashtra', country='India', postal_code='400001',
            owner=self.user
        )
        self.unit = Unit.objects.create(
            building=self.building, unit_number='101',
            floor=1, rent_amount=Decimal('15000'),
            security_deposit=Decimal('30000')
        )

    def test_unit_creation(self):
        self.assertEqual(self.unit.unit_number, '101')
        self.assertEqual(self.unit.rent_amount, Decimal('15000'))

    def test_unit_str(self):
        self.assertIn('101', str(self.unit))

    def test_unit_defaults(self):
        self.assertTrue(self.unit.is_vacant)
        self.assertEqual(self.unit.status, 'VACANT')


class RenterModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='renter_owner', email='ro@test.com',
            password='p', full_name='RO', phone='+1'
        )
        self.building = Building.objects.create(
            name='B2', address_line='Addr', city='Mumbai',
            state='Maharashtra', country='India', postal_code='400001',
            owner=self.user
        )
        self.unit = Unit.objects.create(
            building=self.building, unit_number='201',
            rent_amount=Decimal('20000'), security_deposit=Decimal('40000')
        )
        self.renter = Renter.objects.create(
            unit=self.unit, full_name='Test Renter',
            email='renter@test.com', phone='+919876543210',
            rent_amount=Decimal('20000')
        )

    def test_renter_creation(self):
        self.assertEqual(self.renter.full_name, 'Test Renter')
        self.assertEqual(self.renter.rent_amount, Decimal('20000'))

    def test_renter_defaults(self):
        self.assertEqual(self.renter.status, 'active')
        self.assertIsNotNone(self.renter.onboarding_token)

    def test_renter_str(self):
        self.assertIn('Test Renter', str(self.renter))


class RentRecordModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='rr_owner', email='rro@test.com',
            password='p', full_name='RRO', phone='+1'
        )
        self.building = Building.objects.create(
            name='B3', address_line='Addr', city='Mumbai',
            state='Maharashtra', country='India', postal_code='400001',
            owner=self.user
        )
        self.unit = Unit.objects.create(
            building=self.building, unit_number='301',
            rent_amount=Decimal('25000'), security_deposit=Decimal('50000')
        )
        self.renter = Renter.objects.create(
            unit=self.unit, full_name='RR Renter',
            email='rr@test.com', phone='+919876543210',
            rent_amount=Decimal('25000')
        )
        self.rent_record = RentRecord.objects.create(
            renter=self.renter, amount=Decimal('25000'),
            due_date=date.today(), month=date.today().month,
            year=date.today().year, payment_status='PENDING'
        )

    def test_rent_record_creation(self):
        self.assertEqual(self.rent_record.amount, Decimal('25000'))
        self.assertEqual(self.rent_record.payment_status, 'PENDING')

    def test_rent_record_str(self):
        self.assertIn('25000', str(self.rent_record))


class ExtraChargeModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='ec_owner', email='eco@test.com',
            password='p', full_name='ECO', phone='+1'
        )
        self.building = Building.objects.create(
            name='B4', address_line='Addr', city='Mumbai',
            state='Maharashtra', country='India', postal_code='400001',
            owner=self.user
        )
        self.unit = Unit.objects.create(
            building=self.building, unit_number='401',
            rent_amount=Decimal('10000'), security_deposit=Decimal('20000')
        )
        self.renter = Renter.objects.create(
            unit=self.unit, full_name='EC Renter',
            email='ec@test.com', phone='+919876543210',
            rent_amount=Decimal('10000')
        )
        self.charge = ExtraCharge.objects.create(
            renter=self.renter, name='Water Bill',
            amount=Decimal('500'), due_date=date.today() + timedelta(days=7)
        )

    def test_extra_charge_creation(self):
        self.assertEqual(self.charge.name, 'Water Bill')
        self.assertEqual(self.charge.amount, Decimal('500'))
        self.assertEqual(self.charge.status, 'DUE')


class PropertyTaxRecordModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='tax_owner', email='taxo@test.com',
            password='p', full_name='TaxO', phone='+1'
        )
        self.building = Building.objects.create(
            name='TaxB', address_line='Addr', city='Mumbai',
            state='Maharashtra', country='India', postal_code='400001',
            owner=self.user
        )

    def test_create_tax_record(self):
        tax = PropertyTaxRecord.objects.create(
            property=self.building, amount=Decimal('5000'),
            due_date=date.today() + timedelta(days=30)
        )
        self.assertEqual(tax.amount, Decimal('5000'))
        self.assertFalse(tax.paid)

    def test_tax_record_paid(self):
        tax = PropertyTaxRecord.objects.create(
            property=self.building, amount=Decimal('3000'),
            due_date=date.today(), paid=True, paid_date=date.today()
        )
        self.assertTrue(tax.paid)
        self.assertEqual(tax.paid_date, date.today())

    def test_tax_record_str(self):
        PropertyTaxRecord.objects.create(
            property=self.building, amount=Decimal('1000'),
            due_date=date.today()
        )
        self.assertIn('TaxB', str(PropertyTaxRecord.objects.first()))


class FeatureEnforcerComprehensiveTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='fe_comp', email='fec@test.com',
            password='p', full_name='FEC', phone='+1'
        )
        self.free_plan = SubscriptionPlan.objects.create(
            name='free', monthly_price=Decimal('0'), yearly_price=Decimal('0'),
            features='Free plan', is_active=True
        )
        self.pro_plan = SubscriptionPlan.objects.create(
            name='pro', monthly_price=Decimal('499'), yearly_price=Decimal('4999'),
            features='Pro plan', is_active=True
        )
        PlanFeatureLimit.objects.create(plan=self.free_plan, feature_key='max_buildings', value='2')
        PlanFeatureLimit.objects.create(plan=self.free_plan, feature_key='max_units', value='unlimited')
        PlanFeatureLimit.objects.create(plan=self.pro_plan, feature_key='max_buildings', value='20')

    def test_free_plan_limits(self):
        enforcer = FeatureEnforcer(self.user)
        self.assertEqual(enforcer.get_plan_name(), 'free')
        self.assertFalse(enforcer.is_expired())
        self.assertTrue(enforcer.can_create('max_buildings'))

    def test_pro_plan_limits(self):
        UserSubscription.objects.create(user=self.user, plan=self.pro_plan)
        enforcer = FeatureEnforcer(self.user)
        self.assertEqual(enforcer.get_plan_name(), 'pro')
        self.assertEqual(enforcer.get_active_limit('max_buildings'), 20)

    def test_expired_subscription_within_grace(self):
        UserSubscription.objects.create(
            user=self.user, plan=self.pro_plan,
            end_date=timezone.now() - timedelta(days=1)
        )
        enforcer = FeatureEnforcer(self.user)
        self.assertTrue(enforcer.is_expired())
        self.assertFalse(enforcer.is_past_grace_period())
        self.assertEqual(enforcer.get_active_limit('max_buildings'), 20)

    def test_expired_subscription_past_grace(self):
        UserSubscription.objects.create(
            user=self.user, plan=self.pro_plan,
            end_date=timezone.now() - timedelta(days=10)
        )
        enforcer = FeatureEnforcer(self.user)
        self.assertTrue(enforcer.is_expired())
        self.assertTrue(enforcer.is_past_grace_period())
        self.assertEqual(enforcer.get_active_limit('max_buildings'), 2)

    def test_increment_and_decrement_usage(self):
        enforcer = FeatureEnforcer(self.user)
        enforcer.increment('max_buildings')
        self.assertEqual(UsageLimit.objects.get(user=self.user, feature_key='max_buildings').usage_count, 1)
        enforcer.decrement('max_buildings')
        self.assertEqual(UsageLimit.objects.get(user=self.user, feature_key='max_buildings').usage_count, 0)

    def test_addon_extends_limit(self):
        UserSubscription.objects.create(user=self.user, plan=self.pro_plan)
        AddOnPurchase.objects.create(user=self.user, name='max_buildings', amount=Decimal('5'))
        enforcer = FeatureEnforcer(self.user)
        self.assertEqual(enforcer.get_active_limit('max_buildings'), 25)


class PropertySignalsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='sig_owner', email='so@test.com',
            password='p', full_name='SO', phone='+1'
        )
        self.building = Building.objects.create(
            name='SigB', address_line='Addr', city='Mumbai',
            state='Maharashtra', country='India', postal_code='400001',
            owner=self.user
        )
        self.unit = Unit.objects.create(
            building=self.building, unit_number='S1',
            rent_amount=Decimal('10000'), security_deposit=Decimal('20000')
        )

    def test_renter_creation_triggers_onboarding_token(self):
        renter = Renter.objects.create(
            unit=self.unit, full_name='Signal Renter',
            email='sig@test.com', phone='+919876543210',
            rent_amount=Decimal('10000')
        )
        self.assertIsNotNone(renter.onboarding_token)

    def test_renter_creation_updates_unit_status_to_occupied(self):
        self.assertTrue(self.unit.is_vacant)
        renter = Renter.objects.create(
            unit=self.unit, full_name='Sig Renter 2',
            email='sig2@test.com', phone='+919876543211',
            rent_amount=Decimal('10000')
        )
        self.unit.refresh_from_db()
        self.assertFalse(self.unit.is_vacant)

    def test_renter_deactivation_updates_unit_status(self):
        renter = Renter.objects.create(
            unit=self.unit, full_name='Sig Renter 3',
            email='sig3@test.com', phone='+919876543212',
            rent_amount=Decimal('10000')
        )
        self.unit.refresh_from_db()
        self.assertFalse(self.unit.is_vacant)
        renter.status = 'deactivated'
        renter.save()
        self.unit.refresh_from_db()
        self.assertTrue(self.unit.is_vacant)


class UnitServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='us_owner', email='uso@test.com',
            password='p', full_name='USO', phone='+1'
        )
        self.building = Building.objects.create(
            name='USB', address_line='Addr', city='Mumbai',
            state='Maharashtra', country='India', postal_code='400001',
            owner=self.user
        )
        self.unit = Unit.objects.create(
            building=self.building, unit_number='US1',
            rent_amount=Decimal('10000'), security_deposit=Decimal('20000')
        )

    def test_update_unit_status_no_change(self):
        update_unit_status(self.unit)
        self.unit.refresh_from_db()
        self.assertTrue(self.unit.is_vacant)

    def test_get_building_analytics_empty(self):
        result = get_building_analytics(self.building)
        self.assertEqual(result['total_units'], 1)
        self.assertEqual(result['occupied_units'], 0)
        self.assertEqual(result['vacant_units'], 1)

    def test_get_building_analytics_with_units(self):
        Unit.objects.create(
            building=self.building, unit_number='US2',
            rent_amount=Decimal('15000'), security_deposit=Decimal('30000'),
            status='OCCUPIED', is_vacant=False
        )
        result = get_building_analytics(self.building)
        self.assertEqual(result['total_units'], 2)
        self.assertEqual(result['occupied_units'], 1)
        self.assertEqual(result['vacant_units'], 1)

    def test_get_owner_analytics_empty(self):
        result = get_owner_analytics(self.user)
        self.assertEqual(result['total_buildings'], 1)
        self.assertEqual(result['aggregate']['total_units'], 1)

    def test_get_owner_analytics_with_data(self):
        Unit.objects.create(
            building=self.building, unit_number='US3',
            rent_amount=Decimal('12000'), security_deposit=Decimal('24000'),
            status='OCCUPIED', is_vacant=False
        )
        result = get_owner_analytics(self.user)
        self.assertEqual(result['aggregate']['total_units'], 2)
        self.assertEqual(result['aggregate']['occupied_units'], 1)

    def test_update_unit_status_with_active_renter(self):
        Renter.objects.create(
            unit=self.unit, full_name='US Renter',
            email='usrenter@test.com', phone='+919876543210',
            rent_amount=Decimal('10000'), status='active'
        )
        update_unit_status(self.unit)
        self.unit.refresh_from_db()
        self.assertFalse(self.unit.is_vacant)

    def test_update_unit_status_with_inactive_renter(self):
        Renter.objects.create(
            unit=self.unit, full_name='US Renter 2',
            email='usrenter2@test.com', phone='+919876543211',
            rent_amount=Decimal('10000'), status='deactivated'
        )
        update_unit_status(self.unit)
        self.unit.refresh_from_db()
        self.assertTrue(self.unit.is_vacant)


class OnboardingUtilsComprehensiveTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='onb_owner', email='onbo@test.com',
            password='p', full_name='OnbO', phone='+1'
        )
        self.building = Building.objects.create(
            name='OnbB', address_line='Addr', city='Mumbai',
            state='Maharashtra', country='India', postal_code='400001',
            owner=self.user
        )
        self.unit = Unit.objects.create(
            building=self.building, unit_number='Onb1',
            rent_amount=Decimal('10000'), security_deposit=Decimal('20000')
        )
        self.renter = Renter.objects.create(
            unit=self.unit, full_name='Onb Renter',
            email='onb@test.com', phone='+919876543210',
            rent_amount=Decimal('10000')
        )

    def test_generate_onboarding_token_sets_values(self):
        token = generate_onboarding_token(self.renter)
        self.assertIsNotNone(token)
        self.assertEqual(self.renter.onboarding_token, token)

    def test_generate_onboarding_link_uses_token(self):
        self.renter.onboarding_token = 'test_token_123'
        link = generate_onboarding_link(self.renter)
        self.assertIn('test_token_123', link)

    def test_verify_valid_token(self):
        token = generate_onboarding_token(self.renter)
        result = verify_onboarding_token(token)
        self.assertEqual(result, self.renter)

    def test_verify_expired_token(self):
        self.renter.onboarding_token = 'expired'
        self.renter.onboarding_link_sent_at = timezone.now() - timedelta(days=100)
        self.renter.save()
        result = verify_onboarding_token('expired')
        self.assertIsNone(result)

    def test_verify_invalid_token(self):
        result = verify_onboarding_token('nonexistent')
        self.assertIsNone(result)

    def test_mark_onboarding_completed(self):
        mark_onboarding_completed(self.renter)
        self.renter.refresh_from_db()
        self.assertEqual(self.renter.onboarding_status, 'COMPLETED')

    def test_mark_kyc_verified(self):
        mark_kyc_verified(self.renter)
        self.renter.refresh_from_db()
        self.assertEqual(self.renter.kyc_status, 'VERIFIED')