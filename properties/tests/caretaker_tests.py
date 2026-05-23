"""Tests for caretaker viewset"""
from decimal import Decimal
from datetime import timedelta, date
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from core.models import SubscriptionPlan, UserSubscription, PlanFeatureLimit
from properties.models import Building, Unit, Caretaker

User = get_user_model()

class CaretakerViewSetTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.o = User.objects.create_user(username='co@t.com', email='co@t.com', password='p', full_name='CO', phone='+1')
        cls.fp, _ = SubscriptionPlan.objects.get_or_create(name='c_free', defaults={'monthly_price': Decimal('0'), 'yearly_price': Decimal('0'), 'features': 'Free'})
        cls.pp, _ = SubscriptionPlan.objects.get_or_create(name='c_pro', defaults={'monthly_price': Decimal('29.99'), 'yearly_price': Decimal('299.99'), 'features': 'Pro'})

    def setUp(self):
        PlanFeatureLimit.objects.get_or_create(plan=self.fp, feature_key='max_caretakers', defaults={'value': '2'})
        PlanFeatureLimit.objects.get_or_create(plan=self.pp, feature_key='max_caretakers', defaults={'value': '10'})
        UserSubscription.objects.get_or_create(user=self.o, defaults={
            'plan': self.pp, 'is_active': True})
        b, _ = Building.objects.get_or_create(owner=self.o, name='CB', defaults={'address_line': '1 St', 'city': 'C', 'state': 'S', 'country': 'CO', 'postal_code': '1'})
        self.u, _ = Unit.objects.get_or_create(owner=self.o, building=b, unit='C101', defaults={
            'unit_type': 'flat', 'address_line': '1 St', 'city': 'C', 'state': 'S', 'country': 'CO', 'postal_code': '1'})

    def _auth(self):
        c = APIClient(); c.credentials(HTTP_AUTHORIZATION=f'Bearer {RefreshToken.for_user(self.o).access_token}'); return c

    def test_unauth_list(self): self.assertEqual(self.client.get('/properties/caretakers/').status_code, 401)
    def test_list(self): self.assertEqual(self._auth().get('/properties/caretakers/').status_code, 200)
    def test_create_bad(self): self.assertEqual(self._auth().post('/properties/caretakers/', {}).status_code, 400)
    def test_retrieve(self):
        c = Caretaker.objects.create(unit=self.u, name='TC', phone='+1333333333', start_date=date.today())
        self.assertEqual(self._auth().get(f'/properties/caretakers/{c.id}/').status_code, 200)
    def test_delete(self):
        c = Caretaker.objects.create(unit=self.u, name='TC2', phone='+1444444444', start_date=date.today())
        self.assertEqual(self._auth().delete(f'/properties/caretakers/{c.id}/').status_code, 204)