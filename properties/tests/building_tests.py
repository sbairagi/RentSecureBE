"""Tests for building viewset"""
from decimal import Decimal
from datetime import date
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from core.models import SubscriptionPlan, UserSubscription, PlanFeatureLimit, UsageLimit
from properties.models import Building

User = get_user_model()

class BuildingViewSetTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner = User.objects.create_user(username='bo@t.com', email='bo@t.com', password='p', full_name='BO', phone='+1')
        cls.other = User.objects.create_user(username='bot@t.com', email='bot@t.com', password='p', full_name='BT', phone='+2')
        cls.free, _ = SubscriptionPlan.objects.get_or_create(name='b_free', defaults={'monthly_price': Decimal('0'), 'yearly_price': Decimal('0'), 'features': 'Free'})
        cls.pro, _ = SubscriptionPlan.objects.get_or_create(name='b_pro', defaults={'monthly_price': Decimal('29.99'), 'yearly_price': Decimal('299.99'), 'features': 'Pro'})

    def setUp(self):
        PlanFeatureLimit.objects.get_or_create(plan=self.free, feature_key='max_buildings', defaults={'value': '2'})
        PlanFeatureLimit.objects.get_or_create(plan=self.pro, feature_key='max_buildings', defaults={'value': '10'})
        UserSubscription.objects.get_or_create(user=self.owner, defaults={'plan': self.pro, 'is_active': True})
        self.b1, _ = Building.objects.get_or_create(owner=self.owner, name='B1', defaults={
            'address_line': '1 St', 'city': 'C', 'state': 'S', 'country': 'CO', 'postal_code': '1'})
        self.b2, _ = Building.objects.get_or_create(owner=self.owner, name='B2', defaults={
            'address_line': '2 St', 'city': 'C', 'state': 'S', 'country': 'CO', 'postal_code': '2'})
        self.ob, _ = Building.objects.get_or_create(owner=self.other, name='OB', defaults={
            'address_line': '3 St', 'city': 'C', 'state': 'S', 'country': 'CO', 'postal_code': '3'})

    def _auth(self, u): c = APIClient(); c.credentials(HTTP_AUTHORIZATION=f'Bearer {RefreshToken.for_user(u).access_token}'); return c

    def test_unauth_list(self): self.assertEqual(self.client.get('/properties/buildings/').status_code, 401)
    def test_unauth_create(self): self.assertEqual(self.client.post('/properties/buildings/', {}).status_code, 401)
    def test_list_own(self):
        r = self._auth(self.owner).get('/properties/buildings/')
        self.assertEqual(r.status_code, 200); self.assertEqual(len(r.data), 2)
    def test_no_see_other(self):
        r = self._auth(self.other).get('/properties/buildings/')
        self.assertEqual(r.status_code, 200); self.assertEqual(len(r.data), 1)
    def test_retrieve_own(self):
        r = self._auth(self.owner).get(f'/properties/buildings/{self.b1.id}/'); self.assertEqual(r.status_code, 200)
    def test_no_retrieve_other(self):
        r = self._auth(self.other).get(f'/properties/buildings/{self.b1.id}/'); self.assertEqual(r.status_code, 404)
    def test_create(self):
        r = self._auth(self.owner).post('/properties/buildings/', {
            'name': 'NB', 'address_line': '4 St', 'city': 'C', 'state': 'S', 'country': 'CO', 'postal_code': '4'})
        self.assertEqual(r.status_code, 201)
    def test_limit(self):
        UsageLimit.objects.get_or_create(user=self.owner, feature_key='max_buildings', defaults={'usage_count': 10})
        r = self._auth(self.owner).post('/properties/buildings/', {
            'name': 'LB', 'address_line': '5 St', 'city': 'C', 'state': 'S', 'country': 'CO', 'postal_code': '5'})
        self.assertEqual(r.status_code, 403)
    def test_update_own(self):
        r = self._auth(self.owner).patch(f'/properties/buildings/{self.b1.id}/', {'name': 'UB1', 'address_line': '1 St', 'city': 'C', 'state': 'S', 'country': 'CO', 'postal_code': '1'})
        self.assertEqual(r.status_code, 200)
    def test_no_update_other(self):
        r = self._auth(self.other).patch(f'/properties/buildings/{self.b1.id}/', {'name': 'Hack'}); self.assertEqual(r.status_code, 404)
    def test_delete_own(self):
        r = self._auth(self.owner).delete(f'/properties/buildings/{self.b1.id}/'); self.assertEqual(r.status_code, 204)
    def test_no_delete_other(self):
        r = self._auth(self.other).delete(f'/properties/buildings/{self.b1.id}/'); self.assertEqual(r.status_code, 404)