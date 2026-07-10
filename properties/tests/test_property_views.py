"""Tests for properties/views/property_views.py — property rent and analytics views."""

import json
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase

from core.models import SubscriptionPlan, UserSubscription
from properties.models import Building, Renter, RentRecord, Unit
from properties.views.property_views import (
    my_rent_records,
    revoke_rent_agreement,
    unit_analytics,
    update_late_fee_policy,
)

User = get_user_model()


def _jwt_request(user, method="GET", data=None, path="/test"):
    from rest_framework_simplejwt.tokens import RefreshToken

    from django.test import RequestFactory

    factory = RequestFactory()
    token = RefreshToken.for_user(user).access_token
    if data and method in ("POST", "PATCH", "PUT"):
        req = getattr(factory, method.lower())(
            path,
            data=json.dumps(data),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
    else:
        req = getattr(factory, method.lower())(
            path, HTTP_AUTHORIZATION=f"Bearer {token}"
        )
    return req


def _anon_request(method="GET", data=None, path="/test"):
    from django.test import RequestFactory

    factory = RequestFactory()
    if data and method in ("POST", "PATCH", "PUT"):
        req = getattr(factory, method.lower())(
            path,
            data=json.dumps(data),
            content_type="application/json",
        )
    else:
        req = getattr(factory, method.lower())(path)
    req.user = AnonymousUser()
    return req


class MyRentRecordsTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="myrr_owner", password="p", full_name="MyRROwner", phone="+1"
        )
        self.renter_user = User.objects.create_user(
            username="myrr_renter", password="p", full_name="MyRRRenter", phone="+2"
        )
        self.plan = SubscriptionPlan.objects.create(
            name="myrr_pro",
            monthly_price=Decimal("29.99"),
            yearly_price=Decimal("299.99"),
        )
        UserSubscription.objects.create(user=self.owner, plan=self.plan, is_active=True)
        self.building = Building.objects.create(
            owner=self.owner,
            name="MRRB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        self.unit = Unit.objects.create(
            owner=self.owner,
            building=self.building,
            unit="MRR101",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        self.renter = Renter.objects.create(
            unit=self.unit,
            name="MRR Renter",
            phone="+911234567890",
            email="mrr@test.com",
            rent_amount=Decimal("10000"),
            start_date=date.today(),
            user=self.renter_user,
        )
        self.rent = RentRecord.objects.create(
            unit=self.unit,
            renter=self.renter,
            amount=Decimal("10000"),
            payment_method="upi",
            status="PENDING",
            due_date=date.today() + timedelta(days=7),
        )

    def test_renter_gets_empty_for_non_owner(self):
        response = my_rent_records(_jwt_request(self.renter_user))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

    def test_owner_gets_own_rent_records(self):
        response = my_rent_records(_jwt_request(self.owner))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_anonymous_returns_401(self):
        response = my_rent_records(_anon_request())
        self.assertEqual(response.status_code, 401)


class UpdateLateFeePolicyTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="late_owner", password="p", full_name="LateOwner", phone="+1"
        )
        self.plan = SubscriptionPlan.objects.create(
            name="late_pro",
            monthly_price=Decimal("29.99"),
            yearly_price=Decimal("299.99"),
        )
        UserSubscription.objects.create(user=self.owner, plan=self.plan, is_active=True)
        self.building = Building.objects.create(
            owner=self.owner,
            name="LFB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        self.unit = Unit.objects.create(
            owner=self.owner,
            building=self.building,
            unit="LF101",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        self.renter = Renter.objects.create(
            unit=self.unit,
            name="LF Renter",
            phone="+911234567890",
            email="lf@test.com",
            rent_amount=Decimal("10000"),
            start_date=date.today(),
        )
        self.rent = RentRecord.objects.create(
            unit=self.unit,
            renter=self.renter,
            amount=Decimal("1000"),
            payment_method="upi",
            status="PENDING",
            due_date=date.today(),
            late_fee=Decimal("0"),
        )

    def test_update_late_fee_policy(self):
        response = update_late_fee_policy(
            _jwt_request(self.owner, method="PATCH", data={"late_fee_amount": "500"}),
            property_id=self.rent.id,
        )
        self.assertEqual(response.status_code, 200)
        self.rent.refresh_from_db()
        self.assertEqual(self.rent.late_fee, Decimal("500"))

    def test_update_late_fee_policy_anonymous_returns_401(self):
        response = update_late_fee_policy(
            _anon_request(method="PATCH"), property_id=self.rent.id
        )
        self.assertEqual(response.status_code, 401)


class RevokeRentAgreementTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="revoke_owner", password="p", full_name="RevokeOwner", phone="+1"
        )
        self.plan = SubscriptionPlan.objects.create(
            name="revoke_pro",
            monthly_price=Decimal("29.99"),
            yearly_price=Decimal("299.99"),
        )
        UserSubscription.objects.create(user=self.owner, plan=self.plan, is_active=True)
        self.building = Building.objects.create(
            owner=self.owner,
            name="RevB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        self.unit = Unit.objects.create(
            owner=self.owner,
            building=self.building,
            unit="Rev101",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        self.renter = Renter.objects.create(
            unit=self.unit,
            name="Rev Renter",
            phone="+911234567890",
            email="rev@test.com",
            rent_amount=Decimal("10000"),
            start_date=date.today(),
        )

    def test_revoke_rent_agreement(self):
        with patch(
            "properties.views.property_views.send_whatsapp_message"
        ) as mock_send:
            response = revoke_rent_agreement(
                _jwt_request(
                    self.owner, method="POST", data={"reason": "Owner request"}
                ),
                renter_id=self.renter.id,
            )
        self.assertEqual(response.status_code, 200)
        self.renter.refresh_from_db()
        self.assertTrue(self.renter.is_agreement_revoked)
        self.assertEqual(self.renter.revocation_reason, "Owner request")
        mock_send.assert_called_once()

    def test_revoke_rent_agreement_anonymous_returns_401(self):
        response = revoke_rent_agreement(
            _anon_request(method="POST"), renter_id=self.renter.id
        )
        self.assertEqual(response.status_code, 401)


class UnitAnalyticsTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="analytics_owner",
            password="p",
            full_name="AnalyticsOwner",
            phone="+1",
        )
        self.plan = SubscriptionPlan.objects.create(
            name="analytics_pro",
            monthly_price=Decimal("29.99"),
            yearly_price=Decimal("299.99"),
        )
        UserSubscription.objects.create(user=self.owner, plan=self.plan, is_active=True)
        self.building = Building.objects.create(
            owner=self.owner,
            name="AnB",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
        )
        self.unit = Unit.objects.create(
            owner=self.owner,
            building=self.building,
            unit="An101",
            unit_type="flat",
            address_line="1 St",
            city="C",
            state="S",
            country="CO",
            postal_code="1",
            is_vacant=False,
        )

    def test_unit_analytics_returns_data(self):
        with patch(
            "properties.views.property_views.get_owner_analytics"
        ) as mock_analytics:
            mock_analytics.return_value = {"total_units": 1, "occupied": 1, "vacant": 0}
            response = unit_analytics(_jwt_request(self.owner))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total_units"], 1)

    def test_unit_analytics_by_building(self):
        with patch(
            "properties.services.unit_service.get_building_analytics"
        ) as mock_building:
            mock_building.return_value = {"building": "AnB", "units": 1}
            response = unit_analytics(
                _jwt_request(self.owner, path=f"/test?building_id={self.building.id}")
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["building"], "AnB")

    def test_unit_analytics_anonymous_returns_401(self):
        response = unit_analytics(_anon_request())
        self.assertEqual(response.status_code, 401)
