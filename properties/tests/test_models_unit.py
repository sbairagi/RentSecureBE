"""Tests for unit model edge cases and remaining uncovered lines"""
from decimal import Decimal
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from properties.models import Building, Unit, Renter, RentRecord, ExtraCharge, Caretaker

User = get_user_model()


class UnitModelEdgeCasesTest(TestCase):
    """Covers remaining unit_models.py lines"""
    def setUp(self):
        self.user = User.objects.create_user(username='um_e1', email='ume1@test.com', password='p', full_name='UME1', phone='+1')
        self.building = Building.objects.create(name='UM Bldg', address_line='Addr', city='City', state='State', country='India', postal_code='400001', owner=self.user)
        self.unit = Unit.objects.create(building=self.building, unit_number='U101', rent_amount=Decimal('10000'), security_deposit=Decimal('20000'))

    def test_unit_vacancy_status(self):
        self.assertEqual(self.unit.status, 'VACANT')
        self.assertTrue(self.unit.is_vacant)


class CaretakerModelEdgeCasesTest(TestCase):
    """Covers caretaker_models.py remaining lines"""
    def setUp(self):
        self.user = User.objects.create_user(username='cm_e1', email='cme1@test.com', password='p', full_name='CME1', phone='+1')
        self.building = Building.objects.create(name='CM Bldg', address_line='Addr', city='City', state='State', country='India', postal_code='400001', owner=self.user)
        self.unit = Unit.objects.create(building=self.building, unit_number='CM101', rent_amount=Decimal('10000'), security_deposit=Decimal('20000'))

    def test_caretaker_creation(self):
        ct = Caretaker.objects.create(unit=self.unit, name='Test Caretaker', phone='+919999999902', email='ct@test.com')
        self.assertIsNotNone(ct.id)
        self.assertIn('Test Caretaker', str(ct))

    def test_caretaker_is_active_default(self):
        ct = Caretaker.objects.create(unit=self.unit, name='Active CT', phone='+919999999903', email='act@test.com')
        self.assertTrue(ct.is_active)

    def test_caretaker_with_end_date(self):
        ct = Caretaker.objects.create(unit=self.unit, name='Past CT', phone='+919999999904', email='pct@test.com', end_date=date.today())
        self.assertTrue(ct.is_active)


class ExtraChargeModelEdgeCasesTest(TestCase):
    """Covers extra_charge_models.py remaining lines"""
    def setUp(self):
        self.user = User.objects.create_user(username='ec_e1', email='ece1@test.com', password='p', full_name='ECE1', phone='+1')
        self.building = Building.objects.create(name='EC Bldg', address_line='Addr', city='City', state='State', country='India', postal_code='400001', owner=self.user)
        self.unit = Unit.objects.create(building=self.building, unit_number='EC101', rent_amount=Decimal('10000'), security_deposit=Decimal('20000'))
        self.renter = Renter.objects.create(unit=self.unit, full_name='EC Renter', email='ecr@test.com', phone='+919999999905', rent_amount=Decimal('10000'))

    def test_extra_charge_str(self):
        charge = ExtraCharge.objects.create(renter=self.renter, name='Electricity', amount=Decimal('1500'), due_date=date.today())
        self.assertIn('Electricity', str(charge))
        self.assertIn('EC Renter', str(charge))

    def test_extra_charge_is_paid_property(self):
        charge = ExtraCharge.objects.create(renter=self.renter, name='Water', amount=Decimal('500'), due_date=date.today())
        self.assertFalse(charge.is_paid)
        charge.status = 'PAID'
        charge.save()
        self.assertTrue(charge.is_paid)

    def test_extra_charge_auto_sets_unit(self):
        charge = ExtraCharge.objects.create(renter=self.renter, name='Maintenance', amount=Decimal('2000'), due_date=date.today())
        self.assertEqual(charge.unit, self.unit)


class RenterModelEdgeCasesTest(TestCase):
    """Covers renter_models.py remaining lines"""
    def setUp(self):
        self.user = User.objects.create_user(username='rn_e1', email='rne1@test.com', password='p', full_name='RNE1', phone='+1')
        self.building = Building.objects.create(name='RN Bldg', address_line='Addr', city='City', state='State', country='India', postal_code='400001', owner=self.user)
        self.unit = Unit.objects.create(building=self.building, unit_number='RN101', rent_amount=Decimal('10000'), security_deposit=Decimal('20000'))

    def test_renter_statuses(self):
        for status in ['active', 'notice_period', 'revoked', 'deactivated']:
            renter = Renter.objects.create(unit=self.unit, full_name=f'RN {status}', email=f'rn{status}@test.com', phone=f'+9199999999{hash(status) % 100:02d}', rent_amount=Decimal('10000'), status=status)
            self.assertEqual(renter.status, status)

    def test_renter_onboarding_token_generated_on_create(self):
        renter = Renter.objects.create(unit=self.unit, full_name='RN Token', email='rntoken@test.com', phone='+919999999910', rent_amount=Decimal('10000'))
        self.assertIsNotNone(renter.onboarding_token)