"""Tests for core app models"""
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from core.models import (SubscriptionPlan, PlanFeatureLimit, UsageLimit, OTP, OwnerBankDetails)

User = get_user_model()

class UserModelTest(TestCase):
    def setUp(self): self.u = User.objects.create_user(username='um@t.com', email='um@t.com', password='p', full_name='Test User', phone='+1')
    def test_created(self): self.assertTrue(User.objects.filter(email='um@t.com').exists())
    def test_str(self): self.assertEqual(str(self.u), 'Test User')

class PlanFeatureLimitTest(TestCase):
    def setUp(self): self.p = SubscriptionPlan.objects.create(name='pfp', monthly_price=Decimal('10'), yearly_price=Decimal('100'))
    def test_create(self): self.assertEqual(PlanFeatureLimit.objects.create(plan=self.p, feature_key='x', value='5').value, '5')

class UsageLimitTest(TestCase):
    def setUp(self): self.u = User.objects.create_user(username='ul@t.com', email='ul@t.com', password='p', full_name='U', phone='+1')
    def test_create(self): self.assertEqual(UsageLimit.objects.create(user=self.u, feature_key='x', usage_count=3).usage_count, 3)

class OTPTest(TestCase):
    def test_create(self):
        o = OTP.objects.create(phone_number='+911234567890', code='123456')
        self.assertEqual(o.code, '123456')

class OwnerBankDetailsTest(TestCase):
    def setUp(self): self.u = User.objects.create_user(username='bd@t.com', email='bd@t.com', password='p', full_name='B', phone='+4')
    def test_create(self):
        b = OwnerBankDetails.objects.create(owner=self.u, bank_account_number='1234567890', ifsc_code='HDFC0001234')
        self.assertTrue(OwnerBankDetails.objects.filter(owner=self.u).exists())